# Copyright (c) 2026, Octavision and contributors
# For license information, please see license.txt

import frappe


def execute():
	if not frappe.db.has_column("Site Folder", "lft"):
		return

	from frappe.utils.nestedset import rebuild_tree

	rebuild_tree("Site Folder")
	frappe.clear_cache(doctype="Site Folder")
