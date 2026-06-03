// Copyright (c) 2026, Octavision and contributors
// Pattern aligned with ERPNext Item Group / Customer Group.

frappe.ui.form.on("Site Folder", {
	onload(frm) {
		// Default shortcut opens Tree; List view remains available from the view switcher.
		frm.list_route = "Tree/Site Folder";

		frm.set_query("parent_site_folder", () => ({
			filters: {
				is_group: 1,
				name: ["!=", frm.doc.name || ""],
			},
		}));
	},

	refresh(frm) {
		frm.add_custom_button(__("Site Folder Tree"), () => {
			frappe.set_route("Tree", "Site Folder");
		});
	},

	parent_site_folder(frm) {
		if (frm.doc.parent_site_folder) {
			frm.set_value("is_group", 0);
		}
	},
});
