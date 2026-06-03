# Copyright (c) 2026, Octavision and contributors
# For license information, please see license.txt

import frappe
from frappe import _

_UNSET = object()


# ---------------------------------------------------------------------------
# Per-request cache helpers
# ---------------------------------------------------------------------------

def _local_cache_get(key):
	return getattr(frappe.local, key, _UNSET)


def _local_cache_set(key, value):
	setattr(frappe.local, key, value)


# ---------------------------------------------------------------------------
# Folder hierarchy helpers
# ---------------------------------------------------------------------------

def get_all_site_folders_parent_map() -> dict[str, str | None]:
	"""All Site Folder names → parent name. Cached per request."""
	cached = _local_cache_get("_sdm_folder_parent_map")
	if cached is not _UNSET:
		return cached
	rows = frappe.get_all("Site Folder", fields=["name", "parent_site_folder"])
	result = {row.name: row.parent_site_folder or None for row in rows}
	_local_cache_set("_sdm_folder_parent_map", result)
	return result


def get_descendant_folders(folder_names: list[str]) -> set[str]:
	"""All folder doc names including every descendant of folder_names."""
	if not folder_names:
		return set()

	parent_map = get_all_site_folders_parent_map()
	children_by_parent: dict[str | None, list[str]] = {}
	for name, parent in parent_map.items():
		children_by_parent.setdefault(parent, []).append(name)

	result = set(folder_names)
	queue = list(folder_names)
	while queue:
		parent = queue.pop()
		for child in children_by_parent.get(parent, []):
			if child not in result:
				result.add(child)
				queue.append(child)
	return result


def get_ancestor_folders(folder_name: str | None) -> list[str]:
	"""Parent chain from folder up to root (excluding the folder itself)."""
	if not folder_name:
		return []
	parent_map = get_all_site_folders_parent_map()
	ancestors = []
	current = parent_map.get(folder_name)
	while current:
		ancestors.append(current)
		current = parent_map.get(current)
	return ancestors


# ---------------------------------------------------------------------------
# Permission helpers
# ---------------------------------------------------------------------------

def clear_permission_caches(user: str | None = None):
	"""Invalidate cached role/user permissions (same effect as Desk permission save)."""
	if user:
		frappe.cache.hdel("user_permissions", user)
		frappe.cache.hdel("roles", user)
		frappe.cache.hdel("bootinfo", user)

	frappe.clear_cache(doctype="Insights Table v3")
	frappe.clear_cache(doctype="Site Folder")


def notify_upload_permissions_changed(user: str | None = None):
	"""Tell Insights clients to refresh session permissions without re-login."""
	payload = {"user": user} if user else {}
	frappe.publish_realtime("insights_upload_permissions_updated", message=payload, after_commit=True)


def on_user_permission_change(doc, method=None):
	clear_permission_caches(doc.user)
	notify_upload_permissions_changed(doc.user)


def on_custom_docperm_change(doc, method=None):
	if doc.parent not in ("Insights Table v3", "Site Folder"):
		return
	clear_permission_caches()
	notify_upload_permissions_changed()


def get_allowed_site_folders(user: str | None = None) -> list[str] | None:
	"""Return allowed Site Folder doc names for user, or None if unrestricted.

	- Administrator → unrestricted (None).
	- No User Permission rows → unrestricted (None).
	- Has User Permission rows → those folders + all descendants.

	Result is cached for the duration of the current request.
	"""
	user = user or frappe.session.user
	if not user or user == "Guest":
		return []

	cache_key = f"_sdm_allowed_folders_{user}"
	cached = _local_cache_get(cache_key)
	if cached is not _UNSET:
		return cached

	if user == "Administrator":
		_local_cache_set(cache_key, None)
		return None

	folders = frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": "Site Folder"},
		pluck="for_value",
		distinct=True,
	)

	result = None if not folders else list(get_descendant_folders(folders))
	_local_cache_set(cache_key, result)
	return result


def is_site_folder_restricted(user: str | None = None) -> bool:
	return get_allowed_site_folders(user) is not None


def has_site_folder_access(folder: str | None, user: str | None = None) -> bool:
	allowed = get_allowed_site_folders(user)
	if allowed is None:
		return True
	if not folder:
		return False
	return folder in allowed


def validate_site_folder_access(folder: str, user: str | None = None):
	if not folder:
		frappe.throw(_("Please select a Site Folder."), frappe.MandatoryError)

	if not has_site_folder_access(folder, user):
		frappe.throw(
			_("You do not have permission to access Site Folder '{0}'.").format(folder),
			frappe.PermissionError,
		)


def validate_site_folder_for_upload(folder: str, user: str | None = None):
	"""Uploads must target a leaf folder, not a group (parent) folder."""
	validate_site_folder_access(folder, user)

	row = frappe.db.get_value("Site Folder", folder, ["is_group", "folder_name"], as_dict=True)
	if row and frappe.utils.cint(row.is_group):
		frappe.throw(
			_("'{0}' is a group folder. Select a sub-folder (leaf folder) to upload files.").format(
				row.folder_name or folder
			),
			frappe.ValidationError,
		)


def can_delete_uploaded_tables(user: str | None = None) -> bool:
	"""True when the user's role permissions allow delete on Insights Table v3."""
	user = user or frappe.session.user
	if not user or user == "Guest":
		return False
	return bool(frappe.has_permission("Insights Table v3", "delete", user=user))


def validate_delete_uploaded_table(table_doc_name: str, user: str | None = None):
	if not can_delete_uploaded_tables(user):
		frappe.throw(
			_("You do not have permission to delete uploaded files."),
			frappe.PermissionError,
		)
	doc = frappe.get_doc("Insights Table v3", table_doc_name)
	doc.check_permission("delete")


def validate_upload_table_access(table_name: str, user: str | None = None):
	"""Ensure the user may act on an uploads table (by its Site Folder)."""
	folder = frappe.db.get_value(
		"Insights Table v3",
		{"data_source": "uploads", "table": table_name},
		"custom_site_folder",
	)
	if not has_site_folder_access(folder, user):
		frappe.throw(_("You do not have permission to access this table."), frappe.PermissionError)


def expand_allowed_folders_for_tree(allowed: list[str] | None) -> list[str] | None:
	"""Include ancestor Site Folders so tree can show parent → child hierarchy."""
	if allowed is None:
		return None

	expanded = set(get_descendant_folders(allowed))
	for folder in list(expanded):
		for ancestor in get_ancestor_folders(folder):
			expanded.add(ancestor)
	return list(expanded)


def filter_upload_tables_by_folder(tables: list, user: str | None = None) -> list:
	allowed = get_allowed_site_folders(user)
	if allowed is None:
		return tables

	return [
		t for t in tables
		if (t.get("custom_site_folder") if isinstance(t, dict) else t.custom_site_folder) in allowed
	]


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def site_folder_query(doctype, txt, searchfield, start, page_len, filters):
	"""Link field search for uploads: leaf folders only, respecting User Permission."""
	allowed = get_allowed_site_folders()
	extra_filters = [["is_group", "=", 0]]
	if allowed is not None:
		extra_filters.append(["name", "in", allowed])

	return frappe.desk.search.search_widget(
		doctype, txt, searchfield, start, page_len, filters, extra_filters=extra_filters,
	)
