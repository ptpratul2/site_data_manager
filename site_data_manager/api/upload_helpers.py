# Copyright (c) 2026, Octavision and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def read_uploaded_table(db, file_path: str, ext: str):
	"""Read an uploaded file into an Ibis table.

	Excel files use all_varchar=True because DuckDB infers column types from the
	first row only; mixed-type columns (numbers + text) cause InvalidInputException.
	Google Sheet CSV exports also use all_varchar to handle mixed columns safely.
	"""
	try:
		if ext == "xlsx":
			return db.read_xlsx(file_path, all_varchar=True)
		if ext in ("json", "jsonl"):
			return db.read_json(file_path)
		return db.read_csv(file_path, all_varchar=True)

	except Exception as e:
		frappe.log_error(title="site_data_manager: read upload file", message=frappe.get_traceback())

		msgs = {
			"xlsx": _(
				"Failed to read Excel file. If the sheet mixes numbers and text in the same column, "
				"save as CSV and try again. ({0})"
			).format(str(e)[:200]),
			"json": _("Failed to read JSON/JSONL file. Ensure the file is valid JSON or JSONL."),
			"jsonl": _("Failed to read JSON/JSONL file. Ensure the file is valid JSON or JSONL."),
		}
		frappe.throw(
			msgs.get(ext, _("Failed to read uploaded file. Please try again.")),
			exc=frappe.ValidationError,
		)


def preview_uploaded_table(db, file_path: str, ext: str):
	"""Read a file into an Ibis table and return preview metadata."""
	from insights.insights.doctype.insights_data_source_v3.ibis_utils import get_columns_from_schema

	table = read_uploaded_table(db, file_path, ext)
	columns = get_columns_from_schema(table.schema())
	rows = table.head(50).execute().fillna("").to_dict(orient="records")
	return {
		"table": table,
		"columns": columns,
		"rows": rows,
		"total_rows": int(table.count().execute()),
	}


def link_uploaded_table_to_folder(table_name: str, site_folder: str, data_source: str = "uploads"):
	from insights.insights.doctype.insights_table_v3.insights_table_v3 import InsightsTablev3

	InsightsTablev3.bulk_create(data_source, [table_name])

	table_doc = frappe.db.get_value(
		"Insights Table v3",
		{"data_source": data_source, "table": table_name},
		"name",
	)
	if table_doc:
		frappe.db.set_value(
			"Insights Table v3", table_doc, "custom_site_folder", site_folder, update_modified=False
		)


def import_table_into_uploads(table_name: str, table, site_folder: str, db=None):
	"""Import an Ibis table into uploads DuckDB and link it to a Site Folder."""
	from insights.api import create_uploads_if_not_exists

	create_uploads_if_not_exists()
	ds = frappe.get_doc("Insights Data Source v3", "uploads")

	if db is None:
		with ds.write_connection() as conn:
			conn.create_table(table_name, table, overwrite=True)
	else:
		db.create_table(table_name, table, overwrite=True)

	link_uploaded_table_to_folder(table_name, site_folder, ds.name)
