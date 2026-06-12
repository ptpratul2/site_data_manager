# Copyright (c) 2026, Octavision and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now_datetime

from site_data_manager.api.google_sheets import sync_google_sheet_doc


def sync_all_google_sheets():
	"""Scheduled job: refresh linked Google Sheets that are due for sync."""
	for name in frappe.get_all("Google Sheet Sync", filters={"enabled": 1}, pluck="name"):
		doc = frappe.get_doc("Google Sheet Sync", name)
		if not doc.is_due_for_sync():
			continue

		try:
			sync_google_sheet_doc(doc)
		except Exception:
			frappe.log_error(
				title=f"Google Sheet Sync failed: {doc.table_name}",
				message=frappe.get_traceback(),
			)
