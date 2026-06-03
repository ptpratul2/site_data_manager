# Site Data Manager — User Manual

**App:** Site Data Manager  
**Module:** Site Data Manager  
**Requires:** Frappe Insights (v3)  
**Publisher:** Octavision  

This manual explains how to organize file uploads in Insights by **Site Folder**, control who can see which data, and upload or delete files from **Desk** or **Insights → Data Sources → Uploads**.

---

## Quick start (5 minutes)

1. **System Manager:** Install the app and run `bench migrate` (see [Administrator notes](#14-administrator-notes)).
2. **Admin:** Create **Site Folder** records (e.g. Balco, Debari).
3. **Admin:** Add **User Permission** rows if users should only see specific folders.
4. **User:** Open **Upload Insights File** → pick folder → upload → **Preview** → **Import to Insights**.
5. **User:** Open **Manage Insights Uploads** to browse by folder; use **Insights → Uploads** to build queries.

---

## Table of contents

1. [What this app does](#1-what-this-app-does)
2. [Who should read this](#2-who-should-read-this)
3. [Before you start](#3-before-you-start)
4. [Key concepts](#4-key-concepts)
5. [Desk pages (main workflow)](#5-desk-pages-main-workflow)
6. [Step-by-step: Site Folders](#6-step-by-step-site-folders)
7. [Step-by-step: Upload a file](#7-step-by-step-upload-a-file)
8. [Step-by-step: Manage uploads (folder tree & delete)](#8-step-by-step-manage-uploads-folder-tree--delete)
9. [Using data in Insights](#9-using-data-in-insights)
10. [Permissions](#10-permissions)
11. [When permissions change (no logout)](#11-when-permissions-change-no-logout)
12. [Roles reference](#12-roles-reference)
13. [File formats and naming rules](#13-file-formats-and-naming-rules)
14. [Administrator notes](#14-administrator-notes)
15. [Troubleshooting](#15-troubleshooting)
16. [Worked example: Balco-only user](#16-worked-example-balco-only-user)
17. [FAQ](#17-faq)
18. [Appendix: Technical overview (IT)](#18-appendix-technical-overview-it)
19. [Quick reference](#19-quick-reference)

---

## 1. What this app does

| Feature | Description |
|--------|-------------|
| **Site Folders** | Logical folders (e.g. Balco, Debari) to group uploaded files |
| **Upload with folder** | Every import from Desk is linked to one Site Folder |
| **Folder-based access** | Users only see folders and tables they are allowed to access |
| **Delete uploaded tables** | Users with the right **role permission** can remove uploads from Insights |
| **Insights integration** | Data is stored in the Insights **Uploads** data source (DuckDB); queries and dashboards work as usual |

```text
  Desk (Site Data Manager)              Insights
  ------------------------              --------
  Site Folder (master)        ----->    Uploads data source
  Upload Insights File                  (tables per file)
  Manage Insights Uploads    ----->    Queries / Workbooks / Dashboards
```

---

## 2. Who should read this

| Role | Use this manual for |
|------|---------------------|
| **End user** (Insights User) | Uploading files, viewing own folders, opening tables in Insights |
| **Power user / site lead** (Insights Admin) | Managing folders, assigning user access, deleting files |
| **System Manager / IT** | Installation, Role Permission, User Permission setup |

---

## 3. Before you start

### You need

- Access to **Frappe Desk** (ERPNext / Frappe site login)
- **Insights** installed and working on the same site
- One of these roles (minimum):
  - **Insights User**, or
  - **Insights Admin**, or
  - **System Manager**

### How to open Desk pages

Use the Desk search bar (awesome bar) and type:

- `Upload Insights File`
- `Manage Insights Uploads`
- `Site Folder`

Or open directly:

| Page | URL path |
|------|----------|
| Upload Insights File | `/app/upload-insights-file` |
| Manage Insights Uploads | `/app/manage-insights-uploads` |
| Site Folder list | `/app/site-folder` |

---

## 4. Key concepts

### Site Folder

A **Site Folder** is a master record with a name (e.g. `Balco`, `Debari`). It is not a physical folder on disk; it is a label stored in the database and attached to each uploaded table.

- Created in Desk: **Site Folder** — use **Tree** view for expand/collapse hierarchy (or set **Parent Site Folder** on the form)
- Folders can be **nested**: e.g. parent **Debari** → sub-folders **Debari-1**, **Debari-2**
- Each upload is linked to **one** folder (usually a sub-folder)
- **User Permission** on a parent folder grants access to that folder **and all sub-folders** below it

### Uploads data source (Insights)

When you import a file, Site Data Manager stores it in Insights under the data source named **uploads** (title may show as **Uploads**). Each file becomes one **table** you can use in queries and workbooks.

### Folder on each table

Each imported table has a hidden field **Site Folder** (`custom_site_folder`) linking it to the folder you chose at upload time. This drives:

- Folder tree on **Manage Insights Uploads**
- User Permission filtering (who sees which tables)

### Insights UI (Data Sources → Uploads)

After **`bench migrate`** and **`bench build --app insights`**, the Uploads screen in Insights includes:

- **Upload File** with **nested Site Folder picker** (parent e.g. Debari, then sub-folder e.g. Debari-1)
- **Nested folder tree** on the uploads list (Debari → Debari-1 → your files)
- **Delete** (when role allows)

Desk pages remain available as an alternative.

| Task | Desk | Insights |
|------|------|----------|
| Upload with Site Folder | **Upload Insights File** | **Uploads** → **Upload File** |
| Browse by folder, delete | **Manage Insights Uploads** | **Uploads** (folder tree) |
| Open table for queries | Link from Manage | Click table name in tree |

**Site Data Manager** workspace in Desk lists Desk-only pages.

---

## 5. Desk pages (main workflow)

```text
                    ┌─────────────────────┐
                    │   Site Folder       │
                    │   (create folders)  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
   ┌──────────────────────┐        ┌──────────────────────┐
   │ Upload Insights File │        │ Manage Insights       │
   │ (new upload)         │        │ Uploads (list/delete) │
   └──────────┬───────────┘        └──────────┬───────────┘
              │                               │
              └───────────────┬───────────────┘
                              ▼
                    ┌─────────────────────┐
                    │ Insights → Uploads  │
                    │ (queries & charts)  │
                    └─────────────────────┘
```

| Step | Where | Action |
|------|--------|--------|
| 1 | Site Folder | Create folders for your sites / plants / units |
| 2 | Upload Insights File | Upload CSV / Excel / JSON and assign a folder |
| 3 | Manage Insights Uploads | Review by folder, delete if allowed, refresh permissions |
| 4 | Insights | Build queries and dashboards on imported tables |

---

## 6. Step-by-step: Site Folders

### Create a top-level folder

1. Log in to **Desk**.
2. Search **Site Folder** and open the list.
3. Use **Tree** view (default when opening from the form menu) for expand/collapse hierarchy, or **List** view for a flat table of all folders (switch via the view menu next to the page title).
4. Click **+ New** (root folder) or **Add Child** on a parent row.
5. Enter **Folder Name** (e.g. `Debari`). Leave **Parent Site Folder** empty.
6. Enable **Is Group** if this folder will have sub-folders (required for expand/collapse in the tree).
7. Save.

### Create a sub-folder (folder inside folder)

**From Tree view (recommended):**

1. In **Site Folder** → **Tree** view, click the row for **Debari**.
2. Click **Add Child**.
3. Enter **Folder Name** (e.g. `Debari-1` or `Debari-2`) and save. (Sub-folders are leaves — leave **Is Group** unchecked.)

**From List / form:**

1. **+ Add Site Folder** → set **Parent Site Folder** = `Debari`.
2. Enter **Folder Name** and save.

Example structure:

```text
Debari                 (parent — optional grouping only)
├── Debari-1           (upload files here)
└── Debari-2           (upload files here)
```

Sub-folder document names are generated automatically (e.g. `Debari-debari-1`). You select folders by **Folder Name** in the upload dropdown.

### Edit or rename

- Open the Site Folder record.
- Change **Folder Name** or **Parent** if needed.
- Save.

> **Note:** Existing uploaded tables keep their link to the folder document selected at import time. If you rename or move folders in the tree, review affected uploads.

### Who can create folders

By default, roles with create permission on **Site Folder** include **System Manager**, **Insights Admin**, and **Insights User** (see DocType permissions). Your site may restrict this further.

---

## 7. Step-by-step: Upload a file

Use **Upload Insights File** for all new uploads (required to select a Site Folder).

### Steps

1. Open **Upload Insights File** (`/app/upload-insights-file`).
2. **Site Folder** (required)  
   - Select a **leaf** folder for this upload (e.g. `Debari-1`).  
   - **Group** (parent) folders such as `Debari` are **not shown** — files must go into a sub-folder.  
   - You only see folders you are allowed to access (see [Permissions](#10-permissions)).
3. **File**  
   - Click to upload or drag and drop.  
   - Allowed types: **`.csv`**, **`.xlsx`**, **`.json`**, **`.jsonl`**
4. **Preview** (recommended)  
   - Click **Preview** to load a sample of rows and column headers (up to **50 rows** shown; total row count is displayed).  
   - **Table Name** appears; you can edit it before import (this is the table name inside Insights).
5. **Import to Insights**  
   - Click **Import to Insights**.  
   - On success, data is written to the Uploads data source and linked to your Site Folder.  
   - Desk redirects you to the **Site Folder** list.

### Table names (automatic cleanup)

When you import, the system normalizes the table name (Frappe **scrub**): spaces become underscores, casing is adjusted, and unsafe characters are removed. For example, `Sales Report Q1.csv` may become `sales_report_q1`. You can set the name explicitly in **Table Name** after Preview.

### After import

- Table appears under **Manage Insights Uploads** in the correct folder.
- Table appears in **Insights → Data Sources → Uploads** (if you have permission).
- You can open the table from Manage page (link opens Insights) or from Insights directly.

### If import fails

- Ensure a **Site Folder** is selected.
- Ensure you have permission for that folder.
- Avoid special characters in file/table names (see [File formats and naming rules](#13-file-formats-and-naming-rules)).
- Check file is valid CSV / Excel / JSON.
- **Excel `InvalidInputException`** (e.g. “Could not convert string … to DOUBLE”): the sheet has **mixed numbers and text in the same column** (common in process/quality reports). Site Data Manager reads Excel with all columns as text so import works; numeric columns in Insights queries may need casting in queries.

---

## 8. Step-by-step: Manage uploads (folder tree & delete)

Open **Manage Insights Uploads** (`/app/manage-insights-uploads`).

### Screen layout

- Short help text at the top.
- **Upload File** (primary action) — opens Upload Insights File page.
- **Refresh** (secondary action) — reloads folders, table list, and delete permission.
- **Folder sections** — each Site Folder you can access, with a count badge (folders start **expanded**).
- Click a folder heading to **expand / collapse** the list of tables.
- **Other Files** — tables with no Site Folder (usually older imports); only shown if relevant.

### Open a table in Insights

- Click the **table name** (monospace link).  
- Opens Insights in a new tab: `/insights/data-source/uploads/<table_name>`.

### Delete a table

1. Expand the folder containing the table.
2. If you have delete permission, a **delete** control (trash) appears on the row.
3. Click delete → confirm → table is removed from:
   - Insights Uploads storage (DuckDB), and
   - Insights Table v3 metadata.

**Delete is permanent** and cannot be undone.

If you do **not** see delete:

- Your role does not have **Delete** on **Insights Table v3** (see [Permissions](#10-permissions)), or
- Click **Refresh** after an admin changed role permissions.

---

## 9. Using data in Insights

1. Open **Insights** (e.g. `/insights`).
2. Go to **Data Sources** → **Uploads**.
3. You see a list of tables you are allowed to access (filtered by Site Folder rules).
4. Open a table to preview data, or create a **Query / Workbook / Dashboard** as usual.

### Difference: Desk vs Insights list

| Location | View | Delete | Folder groups |
|----------|------|--------|----------------|
| **Manage Insights Uploads** (Desk) | Folder tree | Yes (if permitted) | Yes |
| **Insights → Uploads** | Flat list | No (use Desk) | No (API still filters rows) |

---

## 10. Permissions

Site Data Manager uses standard Frappe permission tools in two layers.

### A. Site Folder access (User Permission)

Controls **which folders and which uploaded tables** a user sees.

**Setup (admin):**

1. Desk → **User Permission** → New.
2. **User:** e.g. `user@company.com`
3. **Allow:** `Site Folder`
4. **For Value:** e.g. `Balco` (exact folder name)
5. Save.

**Behaviour:**

| User setup | What they see |
|------------|----------------|
| **No** User Permission for Site Folder | All folders and all upload tables (unrestricted for folder filter) |
| **One or more** User Permissions for Site Folder | Those folders, **all sub-folders under them**, and tables in any of those folders |
| **Administrator** user | Always sees **all** folders and tables (folder filter not applied) |

**Examples:**

- User has only **Balco** → Manage page shows only Balco folder and its tables; Upload page only offers Balco in dropdown.
- User has **Balco** and **Debari** → sees both folders and their tables.

Tables **without** a Site Folder appear under **Other Files** only for unrestricted users. Restricted users do not see unassigned tables.

### B. Delete access (Role Permission)

Controls whether the **delete** button appears and whether delete API calls succeed.

**Default in Insights (DocType: Insights Table v3):**

| Role | Delete on Insights Table v3 |
|------|---------------------------|
| **Insights Admin** | Yes (by default) |
| **Insights User** | No (by default) |

**To allow Insights User to delete:**

1. Desk → **Role Permissions Manager** (or customize **Insights Table v3** permissions).
2. Role: **Insights User**
3. Enable **Delete** on **Insights Table v3**.
4. Save.

**To deny delete for an Insights Admin:**

- Remove **Delete** for **Insights Admin** on **Insights Table v3** in Role Permission Manager.

Delete permission is checked on the server; hiding the button alone is not sufficient for security (server always enforces).

### C. Insights data source access

Users still need normal **Insights** access (Insights User or Insights Admin, team permissions, etc.) to open Insights and query tables. Site Data Manager adds folder and delete rules on top of that.

---

## 11. When permissions change (no logout)

After an admin changes **User Permission** or **Role Permission** (for Site Folder or Insights Table v3):

1. **Manage Insights Uploads** — click **Refresh**, or  
2. Re-open the page, or  
3. If Desk realtime is connected, the page may refresh automatically within a few seconds.

You do **not** need to log out of Insights or restart the server for permission changes to apply.

**Upload Insights File** also respects updated folder permissions the next time you open it (Site Folder dropdown / link field).

---

## 12. Roles reference

| Role | Typical use |
|------|-------------|
| **Insights User** | Upload (Desk), view allowed folders, query in Insights |
| **Insights Admin** | Same + manage folders, delete (default), user setup |
| **System Manager** | Full Desk access including Site Folder and permissions |
| **Administrator** | Full access; not restricted by Site Folder User Permission |

Assign roles in **User** → Roles section.

---

## 13. File formats and naming rules

### Supported file types

| Extension | Format |
|-----------|--------|
| `.csv` | Comma-separated values |
| `.xlsx` | Excel workbook |
| `.json` | JSON data |
| `.jsonl` | JSON lines |

### Table / file naming (important)

Avoid these characters in **file names** and **table names**, especially when opening tables in Insights from URLs:

| Character | Problem |
|-----------|---------|
| `#` | Breaks Insights URLs (treated as URL fragment) |
| `?`, `&` | Breaks query strings in URLs |
| `/` | Path separator issues |

**Recommendation:** Use letters, numbers, and underscores only (e.g. `sales_data_2024`, `process_report_march`).

If you must use special characters, open tables from **Manage Insights Uploads** (Desk link uses proper encoding) rather than typing URLs manually.

### Overwriting an existing table

Importing again with the **same table name** overwrites the existing table in Uploads data source. Use this to refresh data or re-import with a Site Folder if an older row had no folder.

---

## 14. Administrator notes

### Installation (one-time per site)

```bash
pip install -e apps/site_data_manager
bench --site <your-site> install-app site_data_manager
bench --site <your-site> migrate
```

### Verify Insights app is untouched

```bash
cd apps/insights && git status
```

Expected: **clean** working tree (no modified files from Site Data Manager).

### What Site Data Manager changes (backend only)

- New DocType: **Site Folder**
- Custom field on **Insights Table v3**: `custom_site_folder`
- API overrides (via hooks): import, list tables, delete, user session flag `can_delete_uploads`
- Desk pages: **Upload Insights File**, **Manage Insights Uploads**

### Custom field

| DocType | Field | Type | Purpose |
|---------|-------|------|---------|
| Insights Table v3 | Site Folder (`custom_site_folder`) | Link → Site Folder | Folder assignment per table |

### Giving a user access to one folder (checklist)

1. Create **Site Folder** (e.g. Balco) if missing.
2. Add **User Permission**: User + Allow Site Folder + For Value Balco.
3. Ensure user has **Insights User** or **Insights Admin**.
4. If they must delete files: grant **Delete** on **Insights Table v3** for their role.
5. User opens **Manage Insights Uploads** and clicks **Refresh**.

### Removing access

- Remove or delete the **User Permission** row for that user and folder.
- User clicks **Refresh** on Manage page; folder and tables disappear from their view.

---

## 15. Troubleshooting

| Problem | Likely cause | What to do |
|---------|----------------|------------|
| Site Folder not in upload dropdown | User Permission limits folders | Add User Permission for that folder, or remove restrictions |
| User sees all folders | No Site Folder User Permission rows | Add User Permission rows to restrict |
| User sees no tables | Restricted to folder with no uploads | Upload files to that folder, or add permission for correct folder |
| Delete button missing | Role lacks Delete on Insights Table v3 | Enable Delete in Role Permissions Manager; click Refresh |
| Delete fails with permission error | Same as above | Fix role permission |
| Import fails “Site Folder required” | No folder selected on upload page | Select Site Folder before Import |
| Table not found in Insights URL | `#` or special chars in table name | Rename file/table; use Desk link from Manage page |
| Changes after permission edit not visible | Cached session | Refresh Manage page or re-open; no logout needed |
| Administrator sees everything | By design | Administrator bypasses Site Folder User Permission filter |
| Folder tree only in Desk | By design | Use **Manage Insights Uploads**; Insights list stays flat |

### Still stuck?

1. Confirm **site_data_manager** is installed: `bench --site <site> list-apps`
2. Run `bench --site <site> migrate`
3. Check **Error Log** in Desk for failed imports or permission errors
4. Contact your System Manager with: user email, folder name, and screenshot of the error

---

## 16. Worked example: Balco-only user

This example matches a typical rollout: two folders (**Balco**, **Debari**) and one analyst who must only see Balco.

### Setup (admin)

| Step | Action |
|------|--------|
| 1 | Create **Site Folder** `Balco` and `Debari` |
| 2 | Open **User** `analyst@company.com` → ensure role **Insights User** |
| 3 | **User Permission** → New → User = analyst, Allow = **Site Folder**, For Value = **Balco** |
| 4 | (Optional) To allow delete: **Role Permissions Manager** → **Insights User** → **Insights Table v3** → enable **Delete** |

### What the analyst experiences

| Screen | Sees |
|--------|------|
| Upload Insights File | Site Folder dropdown lists **Balco** only |
| Manage Insights Uploads | Only **Balco** panel and its tables |
| Insights → Uploads | Only tables linked to **Balco** |
| Delete button | Visible only if Delete is enabled on Insights Table v3 |

### Admin uploads to Debari

An admin without folder restrictions uploads `plant_metrics.xlsx` to **Debari**. The Balco-only analyst **does not** see that table anywhere (Manage page, Insights list, or delete API).

### Granting Debari later

Add a second **User Permission** row (For Value = **Debari**). Analyst clicks **Refresh** on Manage Insights Uploads — **Debari** folder appears without logging out.

---

## 17. FAQ

**Can I upload from inside the Insights app?**  
Yes, Insights still has its built-in upload UI, but it does **not** ask for Site Folder. For folder assignment and consistent permissions, use **Upload Insights File** in Desk.

**Why doesn’t Insights show a folder tree?**  
By design, Site Data Manager does not modify the Insights frontend. Folder tree and delete live on **Manage Insights Uploads**.

**What happens if I rename a Site Folder?**  
The DocType allows rename. Existing tables keep the **old** folder name in `custom_site_folder` until re-imported or updated manually. Prefer creating a new folder and migrating uploads if you need a clean rename.

**Can two users upload the same table name?**  
Table names are global within the **uploads** data source. A second import with the same name **overwrites** the previous table for everyone who can see it.

**Does Insights Admin always see delete?**  
Only if **Delete** is enabled for **Insights Admin** on **Insights Table v3** (default is yes). You can remove it in Role Permissions Manager.

**Why does Administrator see everything?**  
The **Administrator** user bypasses Site Folder User Permission filtering so support staff can troubleshoot without extra permission rows.

---

## 18. Appendix: Technical overview (IT)

For teams maintaining the bench — not required for day-to-day users.

### Architecture

```text
  Browser (Desk)
       │
       ├─ upload-insights-file.js  ──► insights.api.import_csv_data (overridden)
       └─ manage-insights-uploads.js ──► insights.api.get_user_info (overridden)
                                        └── insights.api.data_sources.get_data_source_tables (overridden)

  site_data_manager/
       ├── permissions.py      User Permission filter, delete checks, cache + realtime
       ├── api/insights.py     import, delete, set custom_site_folder
       └── overrides/data_sources.py  folder filter on table list/detail APIs
```

### API overrides (via `hooks.py`)

| Insights endpoint | Replaced by |
|-------------------|-------------|
| `insights.api.get_user_info` | Adds `can_delete_uploads` |
| `insights.api.get_uploads_permissions` | Role-based delete flag |
| `insights.api.import_csv_data` | Requires `site_folder`, sets `custom_site_folder` |
| `insights.api.delete_uploaded_table` | Folder + role checks, DuckDB drop |
| `insights.api.data_sources.get_data_source_tables` | Filters by allowed folders |
| `insights.api.data_sources.get_data_source_table` (+ row count, columns) | Folder access check |

### Realtime events (permission refresh)

When **User Permission** or **Custom DocPerm** (Insights Table v3 / Site Folder) changes, the app clears permission caches and publishes:

- `insights_upload_permissions_updated`
- Frappe’s `update_user_permissions` (Manage page listens to both)

### Uninstall / rollback notes

- Removing the app does not automatically remove imported DuckDB tables or **Insights Table v3** rows.
- Custom field `custom_site_folder` is delivered via fixtures/patch; review before uninstalling on production.

---

## 19. Quick reference

### Desk pages

| Task | Page |
|------|------|
| Create folders | Site Folder |
| Upload file | Upload Insights File |
| View by folder / delete | Manage Insights Uploads |

### Permission tools

| Goal | Tool |
|------|------|
| Limit user to folder(s) | User Permission → Site Folder |
| Allow / deny delete | Role Permissions Manager → Insights Table v3 → Delete |

### Insights

| Task | Path |
|------|------|
| List tables (flat) | Insights → Data Sources → Uploads |
| Query data | Insights → Workbooks / Queries |

---

*Document version: 1.1 — Site Data Manager (Site Data Manager module)*
