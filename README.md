# Asset Management System

Custom Frappe app (`asset_system`) for tracking asset lifecycle, movement, assignment, return, and basic dashboard/API operations.

## Current codebase snapshot

- App/package version: `1.0.0`
- Python package root: `asset_system/`
- API module: `asset_system/api/api.py`
- Workspace fixture: `asset_system/fixtures/asset_system_workspace.json`
- Patches:
  - `asset_system.patches.v1_0.rename_asset_to_byt_asset`
  - `asset_system.patches.v1_1.ensure_byt_asset_references`

## Main modules and DocTypes

| DocType | Autoname | Submittable | Notes |
|---|---|---|---|
| `BYT Asset` | `BYT.{location_abbreviation}..{category_abbreviation}..#####.` | No | Core asset record |
| `Asset Category` | `field:category_name` | No | Asset grouping + abbreviation |
| `Location` | `field:location_name` | No | Asset location + parent relationship |
| `Asset Movement` | `ASTMV-{####}` | Yes | Location transfer records |
| `Asset Assignment` | `ASTAS-{####}` | No | User assignment records |
| `Asset Return` | system naming | Yes | Return workflow linked to assignment |
| `Damages` | system naming | Yes | Damage assessment record |
| `BYT Asset Maintenance` | child table (`istable=1`) | No | Child table doctype scaffold |

## Asset lifecycle rules implemented

From `asset_system/asset_system/doctype/byt_asset/byt_asset.py`:

- Allowed status transitions:
  - `Available -> In Use / Assigned / Maintenance / Scrapped`
  - `In Use -> Available / Maintenance / Scrapped`
  - `Assigned -> Available / Maintenance / Scrapped`
  - `Maintenance -> Available / In Use / Assigned / Scrapped`
  - `Scrapped` is terminal
- `assigned_to` auto-sync:
  - if assigned and status is `Available`, status becomes `Assigned`
  - if unassigned and status is `Assigned`, status becomes `Available`
- Per-asset `User Permission` is created/removed based on assignment.

Related behavior:

- `Asset Movement` blocks scrapped assets and updates `BYT Asset.location` on submit.
- `Asset Assignment` blocks scrapped/in-use assets and updates `BYT Asset.assigned_to/status`.
- `Asset Return` validates assignment consistency, sets assignment return data/status, and resets asset to `Available`.

## Workspace

`Asset System` workspace includes shortcuts for:

- `BYT Asset`
- `Asset Category`
- `Location`
- `Asset Movement`
- `Asset Assignment`
- `Asset Return`

## Hooks and fixtures

`asset_system/hooks.py` currently configures:

- global app CSS/JS includes
- fixtures for:
  - `Role` (`Asset Manager`, `Asset Employee`)
  - `Workspace` (`Asset System`)
- `doc_events` for `BYT Asset` (`before_insert`, `validate`)
- custom permission handlers for `BYT Asset`

## API endpoints (whitelisted)

Methods are defined in `asset_system/api/api.py` and are callable via:

`/api/method/asset_system.api.api.<method_name>`

Primary endpoints:

- `create_asset`
- `get_assets`
- `move_asset`
- `assign_asset`
- `get_asset_history`
- `return_asset`
- `get_dashboard_stats`
- `get_asset_overview`

Additional utility endpoints in the same module:

- `can_create_asset`
- `can_create_assignment`
- `get_user_roles`
- `get_asset_details`
- `get_doctype_meta`
- `search_link_options`
- `get_filtered_doctype_list`
- `get_unified_filter_catalog`
- `check_permission`
- `get_my_assets`
- `get_actionable_notifications`
- `get_reports_dashboard_data`
- `is_proof_needed`

### `get_asset_overview` enrichment behaviour

`get_asset_overview(asset)` returns a combined summary payload for the 360° Asset Details page. The `recent_history` array is enriched server-side after fetching from the `Asset History` DocType:

- For `ALLOCATED` records where `reference_doctype == "Asset Assignment"`: the `assigned_to` field is resolved from the linked `Asset Assignment` document and injected into the history entry.
- For `DEALLOCATED` records where `reference_doctype == "Asset Return"`: the `employee` field (auto-fetched from `asset_assignment.assigned_to`) is resolved from the linked `Asset Return` document and injected as `assigned_to`.
- For `DEALLOCATED` records where `reference_doctype == "Asset Assignment"` (fallback): `assigned_to` is resolved directly from the `Asset Assignment`.

This ensures the frontend can always display **who the asset was allocated to or deallocated from**, independent of who performed the action (`changed_by`).

## Installation

```bash
cd /path/to/frappe-bench
bench get-app https://github.com/AaronShenny/AssetManagementSystem
bench --site your-site.local install-app asset_system
bench --site your-site.local migrate
bench build --app asset_system
```

## Migration note (`Asset` -> `BYT Asset`)

If upgrading from an older custom doctype named `Asset`, run:

```bash
bench --site your-site.local migrate
```

The included patches guard against renaming ERPNext-owned `Asset` doctypes and update link references/workspace references to `BYT Asset`.

## Tests

Repository unit tests are under:

- `asset_system/tests/conftest.py` (frappe mock bootstrap)
- `asset_system/tests/test_asset_system.py`

Run:

```bash
python -m pytest asset_system/tests/ -v
```
