# Copyright (c) 2026, Octavision and contributors

from functools import wraps

import frappe
from frappe import _


def allow_insights_roles(fn):
	"""Whitelist wrapper that allows Insights User, Insights Admin, and Insights team admins."""

	@frappe.whitelist()
	@wraps(fn)
	def wrapper(*args, **kwargs):
		user = frappe.session.user
		if user == "Administrator":
			return fn(*args, **kwargs)

		roles = frappe.get_roles(user)
		if "Insights User" in roles or "Insights Admin" in roles:
			return fn(*args, **kwargs)

		from insights.insights.doctype.insights_team.insights_team import is_admin

		if is_admin(user):
			return fn(*args, **kwargs)

		frappe.throw(_("You do not have permission to access this resource."), frappe.PermissionError)

	return wrapper
