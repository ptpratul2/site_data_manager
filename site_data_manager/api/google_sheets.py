# Copyright (c) 2026, Octavision and contributors
# For license information, please see license.txt

import os
import tempfile

import frappe
from frappe import _
from frappe.utils.csvutils import get_csv_content_from_google_sheets, validate_google_sheets_url
from insights.decorators import insights_whitelist, validate_type
from insights.insights.doctype.insights_team.insights_team import check_data_source_permission

from site_data_manager.api.upload_helpers import import_table_into_uploads, preview_uploaded_table
from site_data_manager.permissions import validate_site_folder_for_upload, validate_upload_table_access


def _fetch_sheet_csv_to_tempfile(url: str) -> str:
	validate_google_sheets_url(url)
	content = get_csv_content_from_google_sheets(url)
	fd, path = tempfile.mkstemp(suffix=".csv")
	try:
		os.write(fd, content)
	finally:
		os.close(fd)
	return path


def _cleanup_tempfile(path: str | None):
	if path and os.path.exists(path):
		try:
			os.unlink(path)
		except OSError:
			pass


def _get_uploads_db():
	from insights.api import create_uploads_if_not_exists

	create_uploads_if_not_exists()
	return frappe.get_doc("Insights Data Source v3", "uploads")


def _ensure_table_name_available(table_name: str):
	if frappe.db.exists("Insights Table v3", {"data_source": "uploads", "table": table_name}):
		frappe.throw(
			_("Table '{0}' already exists. Choose a different name or delete the existing table first.").format(
				table_name
			),
			frappe.DuplicateEntryError,
		)


def sync_google_sheet_doc(doc, *, user: str | None = None):
	"""Fetch Google Sheet CSV and import into the uploads data source."""
	user = user or frappe.session.user
	validate_site_folder_for_upload(doc.site_folder, user)

	temp_path = None
	try:
		temp_path = _fetch_sheet_csv_to_tempfile(doc.sheet_url)
		ds = _get_uploads_db()
		with ds.write_connection() as db:
			preview = preview_uploaded_table(db, temp_path, "csv")
			import_table_into_uploads(doc.table_name, preview["table"], doc.site_folder, db=db)

		doc.db_set(
			{
				"last_synced_on": frappe.utils.now_datetime(),
				"last_sync_status": "Success",
				"last_sync_error": None,
			},
			update_modified=False,
		)
		frappe.db.commit()
		return {"ok": True, "table_name": doc.table_name, "total_rows": preview["total_rows"]}
	except Exception as e:
		error_msg = str(e)[:500]
		doc.db_set(
			{
				"last_sync_status": "Failed",
				"last_sync_error": error_msg,
			},
			update_modified=False,
		)
		frappe.db.commit()
		raise
	finally:
		_cleanup_tempfile(temp_path)


@insights_whitelist()
@validate_type
def preview_google_sheet(url: str):
	"""Preview a publicly shared Google Sheet before linking."""
	check_data_source_permission("uploads")

	url = (url or "").strip()
	if not url:
		frappe.throw(_("Google Sheet URL is required."), frappe.MandatoryError)

	temp_path = None
	try:
		temp_path = _fetch_sheet_csv_to_tempfile(url)
		ds = _get_uploads_db()
		with ds.write_connection() as db:
			preview = preview_uploaded_table(db, temp_path, "csv")
			return {
				"tablename": "google_sheet_import",
				"columns": preview["columns"],
				"rows": preview["rows"],
				"total_rows": preview["total_rows"],
			}
	except frappe.ValidationError:
		raise
	except Exception as e:
		frappe.log_error(title="site_data_manager: preview_google_sheet", message=frappe.get_traceback())
		frappe.throw(
			_("Failed to read Google Sheet. Ensure it is shared as 'Anyone with the link can view'. ({0})").format(
				str(e)[:200]
			),
			exc=frappe.ValidationError,
		)
	finally:
		_cleanup_tempfile(temp_path)


@insights_whitelist()
@validate_type
def link_google_sheet(
	url: str,
	tablename: str = "",
	site_folder: str = "",
	sync_interval_minutes: int | str = 30,
):
	"""Link a Google Sheet and import it; auto-sync on schedule afterwards."""
	check_data_source_permission("uploads")

	sync_interval_minutes = frappe.utils.cint(sync_interval_minutes) or 30
	url = (url or "").strip()

	if not site_folder:
		frappe.throw(
			_("Please select a Site Folder (sub-folder). Group folders cannot be used for upload."),
			frappe.MandatoryError,
		)
	validate_site_folder_for_upload(site_folder)

	table_name = frappe.scrub(tablename) if tablename else "google_sheet_import"
	if not table_name:
		frappe.throw(_("Table name is required."), frappe.MandatoryError)

	_ensure_table_name_available(table_name)

	doc = frappe.get_doc(
		{
			"doctype": "Google Sheet Sync",
			"sheet_url": url.strip(),
			"table_name": table_name,
			"site_folder": site_folder,
			"sync_interval_minutes": str(sync_interval_minutes or 30),
			"enabled": 1,
			"last_sync_status": "Pending",
		}
	)
	doc.insert(ignore_permissions=True)

	try:
		result = sync_google_sheet_doc(doc)
		return {"ok": True, "table_name": table_name, "sync_name": doc.name, **result}
	except Exception:
		frappe.delete_doc("Google Sheet Sync", doc.name, ignore_permissions=True)
		frappe.db.commit()
		raise


@insights_whitelist()
@validate_type
def sync_google_sheet_now(table_name: str):
	"""Manually refresh a linked Google Sheet table."""
	check_data_source_permission("uploads")
	validate_upload_table_access(table_name)

	if not frappe.db.exists("Google Sheet Sync", table_name):
		frappe.throw(_("No Google Sheet sync found for table '{0}'.").format(table_name))

	doc = frappe.get_doc("Google Sheet Sync", table_name)
	return sync_google_sheet_doc(doc)


def get_google_sheet_sync_map(table_names: list[str] | None = None) -> dict[str, dict]:
	"""Return sync metadata keyed by table_name for uploads list UI."""
	filters = {}
	if table_names:
		filters["table_name"] = ["in", table_names]

	rows = frappe.get_all(
		"Google Sheet Sync",
		filters=filters,
		fields=[
			"name",
			"table_name",
			"enabled",
			"sync_interval_minutes",
			"last_synced_on",
			"last_sync_status",
			"last_sync_error",
		],
		ignore_permissions=True,
	)
	return {
		row.table_name: {
			"name": row.name,
			"table_name": row.table_name,
			"enabled": row.enabled,
			"sync_interval_minutes": row.sync_interval_minutes,
			"last_synced_on": row.last_synced_on,
			"last_sync_status": row.last_sync_status,
			"last_sync_error": row.last_sync_error,
		}
		for row in rows
	}
