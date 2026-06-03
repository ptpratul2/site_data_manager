frappe.pages["upload-insights-file"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Upload Insights File"),
		single_column: true,
	});

	new UploadInsightsFilePage(page);
};

class UploadInsightsFilePage {
	constructor(page) {
		this.page = page;
		this.wrapper = $(page.body);
		this.file_doc = null;
		this.preview = null;
		this.site_folder_field = null;
		this.render();
		this.load_site_folders();
	}

	render() {
		this.wrapper.html(`
			<div class="upload-insights-file" style="max-width: 900px;">
				<div class="form-group">
					<label class="control-label">${__("Site Folder")} <span class="text-danger">*</span></label>
					<div class="site-folder-field"></div>
					<p class="help-block small text-muted site-folder-help">${__(
						"Loading folders…"
					)}</p>
				</div>
				<div class="form-group">
					<label class="control-label">${__("File")} <span class="text-danger">*</span></label>
					<div class="file-field"></div>
					<p class="help-block small text-muted">${__("CSV, Excel (.xlsx), JSON, or JSONL")}</p>
				</div>
				<div class="form-group table-name-group" style="display: none;">
					<label class="control-label">${__("Table Name")}</label>
					<input type="text" class="form-control table-name-input" />
				</div>
				<div class="preview-area" style="display: none; margin-top: 1rem;"></div>
				<div class="form-group" style="margin-top: 1rem;">
					<button class="btn btn-default btn-preview" disabled>${__("Preview")}</button>
					<button class="btn btn-primary btn-import" disabled style="margin-left: 8px;">${__("Import to Insights")}</button>
				</div>
			</div>
		`);

		this.file_uploader = new frappe.ui.FileUploader({
			wrapper: this.wrapper.find(".file-field"),
			make_attachments_public: 0,
			restrictions: {
				allowed_file_types: [".csv", ".xlsx", ".json", ".jsonl"],
			},
			on_success: (file_doc) => {
				this.file_doc = file_doc;
				this.wrapper.find(".btn-preview").prop("disabled", false);
				if (!this.wrapper.find(".table-name-input").val()) {
					const base = (file_doc.file_name || "").split(".")[0];
					this.wrapper.find(".table-name-input").val(base);
				}
			},
		});

		this.wrapper.find(".btn-preview").on("click", () => this.preview_file());
		this.wrapper.find(".btn-import").on("click", () => this.import_file());
	}

	load_site_folders() {
		const help = this.wrapper.find(".site-folder-help");
		help.text(__("Loading folders…"));

		frappe.call({
			method: "site_data_manager.api.insights.get_site_folders",
			callback: (r) => {
				const folders = r.message || [];
				if (this.site_folder_field) {
					this.site_folder_field.$wrapper.remove();
				}

				if (!folders.length) {
					help.html(
						`<span class="text-warning">${__(
							"No upload folders found. Create a sub-folder under a parent Site Folder."
						)}</span>`
					);
					return;
				}

				const options = folders.map((f) => f.value).join("\n");
				const labels = {};
				folders.forEach((f) => {
					labels[f.value] = f.label || f.value;
				});

				this.site_folder_field = frappe.ui.form.make_control({
					parent: this.wrapper.find(".site-folder-field"),
					df: {
						fieldtype: "Select",
						fieldname: "site_folder",
						label: __("Site Folder"),
						options,
						reqd: 1,
					},
					render_input: true,
				});
				this.site_folder_field.set_description(
					__(
						"Select a sub-folder. Labels show parent → sub-folder path."
					)
				);

				// Show folder_name labels in the select where possible
				const $select = this.site_folder_field.$input;
				if ($select && $select.is("select")) {
					$select.find("option").each(function () {
						const val = $(this).val();
						if (val && labels[val]) {
							$(this).text(labels[val]);
						}
					});
				}

				help.text("");
			},
			error: () => {
				help.html(
					`<span class="text-danger">${__(
						"Could not load Site Folders. Check Site Folder permissions or refresh the page."
					)}</span>`
				);
			},
		});
	}

	get_site_folder() {
		return this.site_folder_field?.get_value?.() || "";
	}

	get_table_name() {
		return this.wrapper.find(".table-name-input").val()?.trim();
	}

	preview_file() {
		if (!this.file_doc?.name) {
			frappe.msgprint(__("Please upload a file first."));
			return;
		}
		if (!this.get_site_folder()) {
			frappe.msgprint(__("Please select a Site Folder."));
			return;
		}

		frappe.call({
			method: "insights.api.get_file_data",
			args: { filename: this.file_doc.name },
			freeze: true,
			callback: (r) => {
				this.preview = r.message;
				const table_name = this.preview.tablename || this.get_table_name();
				this.wrapper.find(".table-name-group").show();
				this.wrapper.find(".table-name-input").val(table_name);
				this.wrapper.find(".btn-import").prop("disabled", false);

				const rows = (this.preview.rows || []).slice(0, 50);
				const cols = this.preview.columns || [];
				let html = `<p class="text-muted">${__("Showing {0} of {1} rows", [
					rows.length,
					this.preview.total_rows || 0,
				])}</p><div class="table-responsive"><table class="table table-bordered table-sm"><thead><tr>`;
				cols.forEach((c) => {
					const label = c.label || c.column || c.name || "";
					html += `<th>${frappe.utils.escape_html(label)}</th>`;
				});
				html += "</tr></thead><tbody>";
				rows.forEach((row) => {
					html += "<tr>";
					cols.forEach((c) => {
						const key = c.column || c.name;
						const val = row[key] ?? "";
						html += `<td>${frappe.utils.escape_html(String(val))}</td>`;
					});
					html += "</tr>";
				});
				html += "</tbody></table></div>";
				this.wrapper.find(".preview-area").html(html).show();
			},
		});
	}

	import_file() {
		if (!this.file_doc?.name) {
			frappe.msgprint(__("Please upload a file first."));
			return;
		}
		const site_folder = this.get_site_folder();
		if (!site_folder) {
			frappe.msgprint(__("Please select a Site Folder."));
			return;
		}

		frappe.call({
			method: "insights.api.import_csv_data",
			args: {
				filename: this.file_doc.name,
				tablename: this.get_table_name() || "",
				site_folder: site_folder,
			},
			freeze: true,
			callback: () => {
				frappe.show_alert({
					message: __("Table imported successfully"),
					indicator: "green",
				});
				frappe.set_route("manage-insights-uploads");
			},
		});
	}
}
