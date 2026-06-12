# Copyright (c) 2026, Octavision and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date, get_datetime, now_datetime
from frappe.utils.csvutils import validate_google_sheets_url

from site_data_manager.permissions import validate_site_folder_for_upload


class GoogleSheetSync(Document):
	def validate(self):
		validate_google_sheets_url(self.sheet_url)
		validate_site_folder_for_upload(self.site_folder)
		self.table_name = frappe.scrub(self.table_name or "")

		if not self.table_name:
			frappe.throw(_("Table name is required."), frappe.MandatoryError)

	def is_due_for_sync(self) -> bool:
		if not self.enabled:
			return False
		if not self.last_synced_on:
			return True

		interval = frappe.utils.cint(self.sync_interval_minutes) or 30
		next_sync = add_to_date(get_datetime(self.last_synced_on), minutes=interval)
		return now_datetime() >= next_sync
