# Copyright (c) 2026, Octavision and contributors
# For license information, please see license.txt

import frappe


def execute():
	if frappe.db.exists("Custom Field", {"dt": "Insights Table v3", "fieldname": "custom_site_folder"}):
		return

	frappe.get_doc(
		{
			"doctype": "Custom Field",
			"dt": "Insights Table v3",
			"fieldname": "custom_site_folder",
			"label": "Site Folder",
			"fieldtype": "Link",
			"options": "Site Folder",
			"insert_after": "label",
		}
	).insert(ignore_permissions=True)
