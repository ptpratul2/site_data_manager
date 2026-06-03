# Site Data Manager

Organize Insights file uploads by **Site Folder** (nested folders, permissions).  
**Desk pages** plus **Insights → Data Sources → Uploads** (frontend synced on migrate; see below).

**Full user guide:** [USER_MANUAL.md](USER_MANUAL.md)

## Install

```bash
pip install -e apps/site_data_manager
bench --site <your-site> install-app site_data_manager
bench --site <your-site> migrate
```

## Desk pages

| Page | Route | Purpose |
|------|--------|---------|
| **Upload Insights File** | `/app/upload-insights-file` | Upload with Site Folder (leaf folders only) + preview |
| **Manage Insights Uploads** | `/app/manage-insights-uploads` | Nested folder tree, open in Insights, delete |
| **Site Folder** | `/app/site-folder` (Tree view) | Create parent/child folders |

Open **Site Data Manager** workspace in Desk, or search the page names in the awesome bar.

**Manage Insights Uploads** refreshes permissions on **Refresh** or when User/Role Permission changes (realtime).

### Site Folder tree

Create folders in **Site Folder** → **Tree** view. Use **Is Group** on parents (e.g. Debari); upload only into **sub-folders** (e.g. Debari-1).

### Permissions

- **User Permission** → Allow = Site Folder → limits folders/tables (includes sub-folders)
- **Role Permission** → Insights Table v3 → **Delete** controls delete button
- **Administrator** is not restricted by Site Folder user permissions

## Insights UI (Data Sources → Uploads)

On **`bench migrate`**, `insights_frontend/*` is copied into `apps/insights/frontend/`. Then:

```bash
bench build --app insights
```

In Insights you get **Upload File**, **nested Site Folder tree**, and **Site Folder** in the upload dialog (leaf folders only).  
`apps/insights` will show modified frontend files after migrate; re-run migrate after upgrading `site_data_manager` to refresh the sync.

Backend API overrides still apply: folder filtering, import with `site_folder`, delete — so Insights only shows tables you are allowed to see.

## Verify Insights git is clean

```bash
cd apps/insights && git status
# expected: nothing to commit, working tree clean
```

## Backend (`site_data_manager` only)

- `Site Folder` doctype (nested, Tree view in Desk)
- `custom_site_folder` on Insights Table v3
- `hooks.py` API overrides: import, list tables, delete, `get_user_info` (can_delete_uploads)
- Permission cache clear on User Permission / Role Permission save

`insights_frontend/*` is **reference only** — never copied into Insights.
