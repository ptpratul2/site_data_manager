# Copyright (c) 2026, Octavision and contributors
# Source of truth for Insights UI: insights_frontend/ → copied into apps/insights on migrate.
# After migrate run: bench build --app insights

from pathlib import Path

import frappe

INSIGHTS_ROOT = Path(frappe.get_app_path("insights")).parent

SYNC_FILES = (
	("UploadCSVFileDialog.vue", "src2/data_source/UploadCSVFileDialog.vue"),
	("DataSourceTableList.vue", "src2/data_source/DataSourceTableList.vue"),
	("FolderTreeBranch.vue", "src2/data_source/FolderTreeBranch.vue"),
	("FolderSelectTree.vue", "src2/data_source/FolderSelectTree.vue"),
	("FolderSelectBranch.vue", "src2/data_source/FolderSelectBranch.vue"),
	("tables.ts", "src2/data_source/tables.ts"),
	("session.ts", "src2/session.ts"),
)


def sync_insights_frontend():
	"""Copy custom Vue/TS files into the Insights frontend source tree."""
	src_root = Path(frappe.get_app_path("site_data_manager")) / "insights_frontend"
	ok = True
	for name, dest_rel in SYNC_FILES:
		src = src_root / name
		dst = INSIGHTS_ROOT / "frontend" / dest_rel
		if not src.exists():
			frappe.log_error(f"Missing source file: {src}", "site_data_manager sync_insights_frontend")
			ok = False
			continue
		dst.parent.mkdir(parents=True, exist_ok=True)
		dst.write_text(src.read_text())
	return ok


def after_migrate():
	frappe.clear_cache()
	sync_insights_frontend()


def after_install():
	frappe.clear_cache()
