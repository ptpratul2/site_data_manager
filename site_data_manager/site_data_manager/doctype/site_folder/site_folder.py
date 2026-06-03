# Copyright (c) 2026, Octavision and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.nestedset import NestedSet


class SiteFolder(NestedSet):
	nsm_parent_field = "parent_site_folder"

	def autoname(self):
		self.name = self._make_folder_docname()

	def validate(self):
		self._validate_parent()
		self._validate_sibling_folder_name()
		self._sync_is_group()

	def on_update(self):
		super().on_update()
		self._sync_parent_is_group()

	def _sync_is_group(self):
		"""Folders with children must be marked as group so the Desk tree can expand."""
		has_children = frappe.db.exists("Site Folder", {"parent_site_folder": self.name})
		if has_children:
			self.is_group = 1

	def _sync_parent_is_group(self):
		if self.parent_site_folder:
			frappe.db.set_value(
				"Site Folder",
				self.parent_site_folder,
				"is_group",
				1,
				update_modified=False,
			)

	def _make_folder_docname(self) -> str:
		base = frappe.scrub(self.folder_name or "").strip()
		if not base:
			frappe.throw(_("Folder Name is required"))
		if self.parent_site_folder:
			return f"{self.parent_site_folder}-{base}"
		return base

	def _validate_parent(self):
		if not self.parent_site_folder:
			return

		if self.parent_site_folder == self.name:
			frappe.throw(_("A folder cannot be its own parent."))

		if not frappe.db.exists("Site Folder", self.parent_site_folder):
			frappe.throw(_("Parent Site Folder '{0}' does not exist.").format(self.parent_site_folder))

		ancestor = self.parent_site_folder
		seen = {self.name} if self.name else set()
		while ancestor:
			if ancestor in seen:
				frappe.throw(_("Circular folder hierarchy is not allowed."))
			seen.add(ancestor)
			ancestor = frappe.db.get_value("Site Folder", ancestor, "parent_site_folder")

	def _validate_sibling_folder_name(self):
		filters = {"folder_name": self.folder_name, "name": ["!=", self.name or ""]}
		if self.parent_site_folder:
			filters["parent_site_folder"] = self.parent_site_folder
		else:
			filters["parent_site_folder"] = ["in", ["", None]]
		if frappe.db.exists("Site Folder", filters):
			parent_label = self.parent_site_folder or _("(root)")
			frappe.throw(
				_("Folder name '{0}' already exists under {1}.").format(self.folder_name, parent_label)
			)
