# Copyright (c) 2026, Octavision and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from insights.decorators import insights_whitelist, validate_type
from insights.insights.doctype.insights_team.insights_team import check_data_source_permission

from site_data_manager.api.upload_helpers import import_table_into_uploads, preview_uploaded_table
from site_data_manager.permissions import (
	can_delete_uploaded_tables,
	expand_allowed_folders_for_tree,
	get_allowed_site_folders,
	validate_delete_uploaded_table,
	validate_site_folder_for_upload,
	validate_upload_table_access,
)


def _check_site_folder_read():
	if not frappe.has_permission("Site Folder", "read"):
		frappe.throw(_("Not permitted to read Site Folder."), frappe.PermissionError)


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

@insights_whitelist()
def get_user_info():
	"""Extend Insights session info with uploads delete permission."""
	from insights.api import get_user_info as _get_user_info

	info = _get_user_info()
	info["can_delete_uploads"] = can_delete_uploaded_tables()
	return info


# ---------------------------------------------------------------------------
# Folder tree helpers
# ---------------------------------------------------------------------------

def _get_site_folder_rows(allowed: list[str] | None, upload_only: bool = False):
	filters = {}
	if upload_only:
		filters["is_group"] = 0
	if allowed is not None:
		filters["name"] = ["in", allowed]
	return frappe.get_all(
		"Site Folder",
		filters=filters,
		fields=["name", "folder_name", "parent_site_folder", "is_group"],
		order_by="folder_name asc, name asc",
	)


def _build_site_folder_tree(allowed: list[str] | None) -> list[dict]:
	"""Build a nested folder tree. `allowed=None` means unrestricted."""
	allowed = expand_allowed_folders_for_tree(allowed)
	folders = _get_site_folder_rows(allowed)
	by_name = {f.name: f for f in folders}
	children: dict[str | None, list] = {}

	for folder in folders:
		parent = folder.parent_site_folder if folder.parent_site_folder in by_name else None
		children.setdefault(parent, []).append(folder)

	def build_node(folder) -> dict:
		child_nodes = [
			build_node(child)
			for child in sorted(children.get(folder.name, []), key=lambda f: (f.folder_name or f.name).lower())
		]
		return {
			"name": folder.name,
			"folder_name": folder.folder_name or folder.name,
			"is_group": frappe.utils.cint(folder.is_group) or bool(child_nodes),
			"children": child_nodes,
		}

	roots = sorted(children.get(None, []), key=lambda f: (f.folder_name or f.name).lower())
	return [build_node(root) for root in roots]


def _leaf_folder_select_options(nodes: list[dict], path: list[str] | None = None) -> list[dict]:
	"""Desk Select: leaf options labelled with full path (e.g. Debari → Debari-1)."""
	path = path or []
	rows = []
	for node in nodes:
		label = node.get("folder_name") or node.get("name")
		children = node.get("children") or []
		if children:
			rows.extend(_leaf_folder_select_options(children, path + [label]))
		else:
			rows.append({"label": " → ".join(path + [label]), "value": node["name"]})
	return rows


# ---------------------------------------------------------------------------
# Folder API endpoints
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_site_folders():
	"""Desk upload page: leaf folders with parent path in the label."""
	_check_site_folder_read()
	return _leaf_folder_select_options(_build_site_folder_tree(get_allowed_site_folders()))


@frappe.whitelist()
def get_site_folder_tree():
	"""Desk Manage page: nested folder tree."""
	_check_site_folder_read()
	return _build_site_folder_tree(get_allowed_site_folders())


@insights_whitelist()
def get_site_folder_tree_for_insights():
	"""Insights: nested folder tree (upload picker + uploads list)."""
	check_data_source_permission("uploads")
	return _build_site_folder_tree(get_allowed_site_folders())


@insights_whitelist()
def get_site_folders_for_insights():
	"""Insights upload dialog: flat leaf options labelled with full parent path."""
	check_data_source_permission("uploads")
	return _leaf_folder_select_options(_build_site_folder_tree(get_allowed_site_folders()))


# ---------------------------------------------------------------------------
# Upload flow
# ---------------------------------------------------------------------------

@insights_whitelist()
@validate_type
def get_file_data(filename: str):
	"""Preview uploaded file before import."""
	from insights.api import create_uploads_if_not_exists, get_csv_file

	check_data_source_permission("uploads")

	file, ext = get_csv_file(filename)
	file_name = frappe.scrub((file.file_name or "").split(".")[0])

	create_uploads_if_not_exists()
	ds = frappe.get_doc("Insights Data Source v3", "uploads")
	with ds.write_connection() as db:
		try:
			preview = preview_uploaded_table(db, file.get_full_path(), ext)
			return {
				"tablename": file_name,
				"columns": preview["columns"],
				"rows": preview["rows"],
				"total_rows": preview["total_rows"],
			}
		except frappe.ValidationError:
			raise
		except Exception:
			frappe.log_error(title="site_data_manager: get_file_data", message=frappe.get_traceback())
			raise


@insights_whitelist()
@validate_type
def import_csv_data(filename: str, tablename: str = "", site_folder: str = ""):
	from insights.api import create_uploads_if_not_exists, get_csv_file

	check_data_source_permission("uploads")

	if not site_folder:
		frappe.throw(
			_("Please select a Site Folder (sub-folder). Group folders cannot be used for upload."),
			frappe.MandatoryError,
		)
	validate_site_folder_for_upload(site_folder)

	file, ext = get_csv_file(filename)
	table_name = frappe.scrub(tablename) if tablename else frappe.scrub(file.file_name.split(".")[0])

	create_uploads_if_not_exists()
	ds = frappe.get_doc("Insights Data Source v3", "uploads")
	with ds.write_connection() as db:
		try:
			preview = preview_uploaded_table(db, file.get_full_path(), ext)
			import_table_into_uploads(table_name, preview["table"], site_folder, db=db)
		except frappe.ValidationError:
			raise
		except Exception:
			frappe.log_error(title="site_data_manager: import_csv_data", message=frappe.get_traceback())
			frappe.throw(_("Failed to import file into Insights. Please try again."))

	frappe.db.commit()


# ---------------------------------------------------------------------------
# Permissions / delete
# ---------------------------------------------------------------------------

@insights_whitelist()
def get_uploads_permissions():
	return {"can_delete": can_delete_uploaded_tables()}


@insights_whitelist()
@validate_type
def delete_uploaded_table(table_name: str):
	"""Remove an uploaded table from DuckDB and Insights Table v3."""
	from insights.insights.doctype.insights_table_v3.insights_table_v3 import get_table_name
	from insights.api import create_uploads_if_not_exists

	check_data_source_permission("uploads")

	if not frappe.db.exists("Insights Table v3", {"data_source": "uploads", "table": table_name}):
		frappe.throw(_("Table '{0}' was not found in uploads.").format(table_name))

	validate_upload_table_access(table_name)
	table_doc_name = get_table_name("uploads", table_name)
	validate_delete_uploaded_table(table_doc_name)

	create_uploads_if_not_exists()
	ds = frappe.get_doc("Insights Data Source v3", "uploads")

	with ds.write_connection() as db:
		if table_name in db.list_tables():
			db.drop_table(table_name, force=True)

	frappe.delete_doc("Insights Table v3", table_doc_name)

	if frappe.db.exists("Google Sheet Sync", table_name):
		frappe.delete_doc("Google Sheet Sync", table_name, ignore_permissions=True)

	frappe.db.commit()

	return {"ok": True, "table_name": table_name}
