app_name = "site_data_manager"
app_title = "Site Data Manager"
app_publisher = "Octavision"
app_description = "Site folders for Insights file uploads"
app_email = "khushboo.yadav@octavision.in"
app_license = "mit"

required_apps = ["insights"]

after_install = ["site_data_manager.install.after_install"]
after_migrate = ["site_data_manager.install.after_migrate"]

scheduler_events = {
	"cron": {
		"*/15 * * * *": ["site_data_manager.tasks.sync_all_google_sheets"],
	},
}

fixtures = [
	{
		"dt": "Custom Field",
		"filters": [["name", "in", ["Insights Table v3-custom_site_folder"]]],
	},
	{
		"dt": "Workspace",
		"filters": [["name", "in", ["Site Data Manager"]]],
	},
]

doc_events = {
	"User Permission": {
		"after_insert": "site_data_manager.permissions.on_user_permission_change",
		"on_update": "site_data_manager.permissions.on_user_permission_change",
		"on_trash": "site_data_manager.permissions.on_user_permission_change",
	},
	"Custom DocPerm": {
		"after_insert": "site_data_manager.permissions.on_custom_docperm_change",
		"on_update": "site_data_manager.permissions.on_custom_docperm_change",
		"on_trash": "site_data_manager.permissions.on_custom_docperm_change",
	},
}

override_whitelisted_methods = {
	"insights.api.get_user_info": "site_data_manager.api.insights.get_user_info",
	"insights.api.get_uploads_permissions": "site_data_manager.api.insights.get_uploads_permissions",
	"insights.api.get_site_folder_tree": "site_data_manager.api.insights.get_site_folder_tree_for_insights",
	"insights.api.get_file_data": "site_data_manager.api.insights.get_file_data",
	"insights.api.import_csv_data": "site_data_manager.api.insights.import_csv_data",
	"insights.api.delete_uploaded_table": "site_data_manager.api.insights.delete_uploaded_table",
	"insights.api.data_sources.get_data_source_tables": "site_data_manager.overrides.data_sources.get_data_source_tables",
	"insights.api.data_sources.get_data_source_table": "site_data_manager.overrides.data_sources.get_data_source_table",
	"insights.api.data_sources.get_data_source_table_row_count": "site_data_manager.overrides.data_sources.get_data_source_table_row_count",
	"insights.api.data_sources.get_data_source_table_columns": "site_data_manager.overrides.data_sources.get_data_source_table_columns",
}

# Desk UI: /app/upload-insights-file, /app/manage-insights-uploads
# Insights UI: synced from insights_frontend/ on migrate (bench build --app insights)
