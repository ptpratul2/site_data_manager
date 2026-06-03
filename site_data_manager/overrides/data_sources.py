# Copyright (c) 2026, Octavision and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from insights.decorators import insights_whitelist, validate_type

from site_data_manager.permissions import (
	filter_upload_tables_by_folder,
	has_site_folder_access,
)


def _check_uploads_table_folder_access(data_source: str, table_name: str):
	if data_source != "uploads":
		return

	folder = frappe.db.get_value(
		"Insights Table v3",
		{"data_source": data_source, "table": table_name},
		"custom_site_folder",
	)
	if not has_site_folder_access(folder):
		frappe.throw(_("You do not have permission to access this table."), frappe.PermissionError)


@insights_whitelist()
@validate_type
def get_data_source_tables(data_source: str | None = None, search_term: str | None = None, limit: int = 100):
	tables = frappe.get_list(
		"Insights Table v3",
		filters={"data_source": data_source or ["is", "set"]},
		or_filters={
			"label": ["is", "set"] if not search_term else ["like", f"%{search_term}%"],
			"table": ["is", "set"] if not search_term else ["like", f"%{search_term}%"],
		},
		fields=["name", "table", "label", "data_source", "last_synced_on", "custom_site_folder"],
		limit=limit,
	)

	if data_source == "uploads":
		tables = filter_upload_tables_by_folder(tables)

	# Batch-fetch all folder names in one query (avoids N+1 per-table DB calls)
	folder_docs = {t.custom_site_folder for t in tables if t.custom_site_folder}
	folder_name_map: dict[str, str] = {}
	if folder_docs:
		rows = frappe.get_all(
			"Site Folder",
			filters={"name": ["in", list(folder_docs)]},
			fields=["name", "folder_name"],
		)
		folder_name_map = {r.name: r.folder_name or r.name for r in rows}

	return [
		frappe._dict(
			name=table.name,
			label=table.label,
			table_name=table.table,
			data_source=table.data_source,
			last_synced_on=table.last_synced_on,
			custom_site_folder=folder_name_map.get(table.custom_site_folder, table.custom_site_folder),
			custom_site_folder_doc=table.custom_site_folder,
		)
		for table in tables
	]


@insights_whitelist()
@validate_type
def get_data_source_table(data_source: str, table_name: str):
	_check_uploads_table_folder_access(data_source, table_name)
	from insights.api.data_sources import get_data_source_table as _fn
	return _fn(data_source, table_name)


@insights_whitelist()
@validate_type
def get_data_source_table_row_count(data_source: str, table_name: str):
	_check_uploads_table_folder_access(data_source, table_name)
	from insights.api.data_sources import get_data_source_table_row_count as _fn
	return _fn(data_source, table_name)


@insights_whitelist()
@validate_type
def get_data_source_table_columns(data_source: str, table_name: str):
	_check_uploads_table_folder_access(data_source, table_name)
	from insights.api.data_sources import get_data_source_table_columns as _fn
	return _fn(data_source, table_name)
