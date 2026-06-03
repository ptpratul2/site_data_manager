frappe.pages["manage-insights-uploads"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Manage Insights Uploads"),
		single_column: true,
	});

	page.set_primary_action(__("Upload File"), () => frappe.set_route("upload-insights-file"));
	page.set_secondary_action(__("Refresh"), () => page.manage_uploads?.refresh());

	new ManageInsightsUploadsPage(page);
};

class ManageInsightsUploadsPage {
	constructor(page) {
		this.page = page;
		this.page.manage_uploads = this;
		this.wrapper = $(page.body);
		this.can_delete = false;
		this.expanded = {};
		this.render();
		this.refresh();
	}

	render() {
		this.wrapper.html(`
			<div class="manage-insights-uploads">
				<div class="alert alert-info small" style="margin-bottom: 1rem;">
					<strong>${__("Site Data Manager")}</strong> —
					${__(
						"Uploaded files grouped by Site Folder. Same folders appear under Insights → Data Sources → Uploads."
					)}
				</div>
				<p class="text-muted small">${__(
					"Tables are grouped by Site Folder (including sub-folders). Permission changes apply after Refresh."
				)}</p>
				<div class="uploads-tree-area" style="margin-top: 1rem;"></div>
			</div>
		`);
		this.tree_area = this.wrapper.find(".uploads-tree-area");

		frappe.realtime.on("update_user_permissions", (data) => {
			if (!data?.user || data.user === frappe.session.user) this.refresh();
		});
		frappe.realtime.on("insights_upload_permissions_updated", (data) => {
			if (!data?.user || data.user === frappe.session.user) this.refresh();
		});
	}

	refresh() {
		return frappe
			.call({
				method: "insights.api.get_user_info",
				freeze: true,
			})
			.then((r) => {
				this.can_delete = Boolean(r.message?.can_delete_uploads);
				return Promise.all([
					frappe.call({
						method: "site_data_manager.api.insights.get_site_folder_tree",
						freeze: true,
					}),
					frappe.call({
						method: "insights.api.data_sources.get_data_source_tables",
						args: { data_source: "uploads", limit: 500 },
						freeze: true,
					}),
				]);
			})
			.then(([treeRes, tablesRes]) => {
				this.folder_tree = treeRes.message || [];
				this.last_tables = tablesRes.message || [];
				this.render_tree();
			});
	}

	get_tables_by_folder() {
		const by_folder = {};
		(this.last_tables || []).forEach((t) => {
			const key = t.custom_site_folder_doc || t.custom_site_folder;
			if (!key) return;
			if (!by_folder[key]) by_folder[key] = [];
			by_folder[key].push(t);
		});
		return by_folder;
	}

	render_flat_folder_groups(tables) {
		const by_label = {};
		tables.forEach((t) => {
			const label = t.custom_site_folder || __("Other Files");
			if (!by_label[label]) by_label[label] = [];
			by_label[label].push(t);
		});

		let html = "";
		Object.keys(by_label)
			.sort((a, b) => a.localeCompare(b))
			.forEach((label) => {
				const list = by_label[label];
				html += `
					<div class="panel panel-default" style="margin-bottom: 8px;">
						<div class="panel-heading">
							<strong>${frappe.utils.escape_html(label)}</strong>
							<span class="badge" style="margin-left: 8px;">${list.length}</span>
						</div>
						<div class="panel-body" style="padding: 0;">
							<table class="table table-sm table-bordered" style="margin: 0;"><tbody>
				`;
				list.forEach((t) => {
					html += this.render_row(t);
				});
				html += `</tbody></table></div></div>`;
			});
		return html;
	}

	count_tables_in_subtree(node, by_folder) {
		let count = (by_folder[node.name] || []).length;
		(node.children || []).forEach((child) => {
			count += this.count_tables_in_subtree(child, by_folder);
		});
		return count;
	}

	render_tree() {
		const tables = this.last_tables || [];
		const by_folder = this.get_tables_by_folder();
		const unassigned = tables.filter(
			(t) => !(t.custom_site_folder_doc || t.custom_site_folder)
		);

		if (!tables.length) {
			this.tree_area.html(`
				<div class="text-muted text-center" style="padding: 3rem;">
					<p>${__("No uploaded tables yet.")}</p>
					<button class="btn btn-primary btn-sm btn-upload-empty">${__("Upload File")}</button>
				</div>
			`);
			this.tree_area.find(".btn-upload-empty").on("click", () => frappe.set_route("upload-insights-file"));
			return;
		}

		let html = "";
		const tree = this.folder_tree || [];
		if (tree.length) {
			tree.forEach((root) => {
				html += this.render_folder_node(root, by_folder, 0);
			});
		} else if (tables.length) {
			html += this.render_flat_folder_groups(tables);
		}

		if (unassigned.length) {
			html += `<p class="text-muted text-uppercase small" style="margin: 1.5rem 0 0.5rem;">${__("Other Files")}</p>`;
			html += `<table class="table table-sm table-bordered"><tbody>`;
			unassigned.forEach((t) => {
				html += this.render_row(t);
			});
			html += `</tbody></table>`;
		}

		if (!html && tables.length) {
			html = this.render_flat_folder_groups(tables);
		}

		this.tree_area.html(html);

		this.tree_area.find(".folder-heading").on("click", (e) => {
			const name = $(e.currentTarget).data("folder");
			this.expanded[name] = !this.expanded[name];
			this.render_tree();
		});

		this.tree_area.find(".btn-delete-table").on("click", (e) => {
			e.stopPropagation();
			const table_name = $(e.currentTarget).data("table");
			this.confirm_delete(table_name);
		});
	}

	render_folder_node(node, by_folder, depth) {
		const list = by_folder[node.name] || [];
		const totalCount = this.count_tables_in_subtree(node, by_folder);
		if (!totalCount && !(node.children || []).length) {
			return "";
		}

		const open = this.expanded[node.name] !== false;
		const indent = depth * 16;
		const displayName = node.folder_name || node.name;
		let html = `
			<div class="panel panel-default" style="margin-bottom: 8px; margin-left: ${indent}px;">
				<div class="panel-heading folder-heading" data-folder="${frappe.utils.escape_html(node.name)}" style="cursor:pointer;">
					<span class="folder-chevron">${open ? "▼" : "▶"}</span>
					<strong style="margin-left: 8px;">${frappe.utils.escape_html(displayName)}</strong>
					<span class="badge" style="margin-left: 8px;">${totalCount}</span>
				</div>
				<div class="panel-body folder-body" data-folder="${frappe.utils.escape_html(node.name)}" style="${open ? "" : "display:none;"} padding: 0;">
		`;

		if (list.length) {
			html += `<table class="table table-sm table-bordered" style="margin: 0;"><tbody>`;
			list.forEach((t) => {
				html += this.render_row(t);
			});
			html += `</tbody></table>`;
		}

		(node.children || []).forEach((child) => {
			html += this.render_folder_node(child, by_folder, depth + 1);
		});

		html += `</div></div>`;
		return html;
	}

	render_row(table) {
		const delete_btn = this.can_delete
			? `<button class="btn btn-xs btn-default btn-delete-table" data-table="${frappe.utils.escape_html(
					table.table_name
			  )}" title="${__("Delete")}">🗑</button>`
			: "";
		return `
			<tr>
				<td class="col-table" style="width: 70%;">
					<a href="/insights/data-source/uploads/${encodeURIComponent(table.table_name)}" target="_blank">
						<code>${frappe.utils.escape_html(table.table_name)}</code>
					</a>
				</td>
				<td class="text-right">${delete_btn}</td>
			</tr>
		`;
	}

	confirm_delete(table_name) {
		frappe.confirm(
			__(
				"Permanently delete table <strong>{0}</strong>? This cannot be undone.",
				[table_name]
			),
			() => {
				frappe.call({
					method: "insights.api.delete_uploaded_table",
					args: { table_name },
					freeze: true,
					callback: () => {
						frappe.show_alert({
							message: __("Table deleted"),
							indicator: "green",
						});
						this.refresh();
					},
				});
			}
		);
	}
}
