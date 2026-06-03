# Copyright (c) 2026, Octavision and contributors
# For license information, please see license.txt

import frappe


def execute():
	if not frappe.db.has_column("Site Folder", "is_group"):
		return

	for folder in frappe.get_all("Site Folder", pluck="name"):
		has_children = frappe.db.exists("Site Folder", {"parent_site_folder": folder})
		frappe.db.set_value("Site Folder", folder, "is_group", 1 if has_children else 0)

	frappe.db.commit()
	frappe.clear_cache(doctype="Site Folder")
