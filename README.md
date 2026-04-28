# Asset Management System

A **fully independent** Asset Management System built as a custom Frappe Framework app (`asset_system`). Does **not** depend on ERPNext, Item, or Accounting modules.

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        Frappe Framework                          │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    asset_system (App)                       │ │
│  │                                                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │ │
│  │  │  Asset       │  │Asset Category│  │    Location      │  │ │
│  │  │  (AST-####)  │→ │              │  │  (Tree)          │  │ │
│  │  └──────┬───────┘  └──────────────┘  └──────────────────┘  │ │
│  │         │                                                    │ │
│  │   ┌─────┴────────────────────────────────┐                  │ │
│  │   │                                      │                  │ │
│  │   ▼                                      ▼                  │ │
│  │  ┌──────────────────┐  ┌──────────────────────────────────┐ │ │
│  │  │  Asset Movement  │  │      Asset Assignment            │ │ │
│  │  │  (ASTMV-####)    │  │      (ASTAS-####)                │ │ │
│  │  └──────────────────┘  └──────────────────────────────────┘ │ │
│  │                                                             │ │
│  │  ┌─────────────────────────────────────────────────────┐   │ │
│  │  │  Whitelisted API  (asset_system/api/asset_api.py)   │   │ │
│  │  │  create_asset · get_assets · move_asset             │   │ │
│  │  │  assign_asset · get_asset_history · return_asset    │   │ │
│  │  │  get_dashboard_stats                                │   │ │
│  │  └─────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Folder Structure

```
asset_system/                          ← App root (git repo / pip package)
├── setup.py
├── requirements.txt
├── MANIFEST.in
└── asset_system/                      ← Python package  (import asset_system)
    ├── __init__.py                    ← __version__ = "1.0.0"
    ├── hooks.py                       ← Frappe hooks (doc_events, fixtures, etc.)
    ├── modules.txt                    ← "Asset System"
    ├── patches.txt
    │
    ├── api/                           ← Whitelisted REST API
    │   ├── __init__.py
    │   └── asset_api.py
    │
    ├── public/                        ← Static assets (CSS/JS)
    │   ├── css/asset_system.css
    │   └── js/asset_system.js
    │
    ├── templates/                     ← Jinja2 web templates
    │   └── pages/
    │       └── asset_dashboard.html
    │
    ├── fixtures/                      ← Exported fixtures (Workspace)
    │   └── asset_system_workspace.json
    │
    ├── tests/
    │   ├── conftest.py                ← frappe mock setup
    │   └── test_asset_system.py
    │
    └── asset_system/                  ← Module folder (module = "Asset System")
        ├── __init__.py
        └── doctype/
            ├── asset/
            │   ├── asset.json         ← DocType schema
            │   ├── asset.py           ← Server-side controller
            │   └── asset.js           ← Client-side controller
            ├── asset_category/
            ├── location/
            ├── asset_movement/
            └── asset_assignment/
```

---

## DocTypes

| DocType | Autoname | Submittable | Description |
|---------|----------|-------------|-------------|
| **Asset** | `AST-{####}` | No | Core entity. Lifecycle: Available → In Use → Maintenance → Scrapped |
| **Asset Category** | By `category_name` | No | Groups assets (Electronics, Furniture, etc.) |
| **Location** | By `location_name` | No | Physical location (supports parent/child) |
| **Asset Movement** | `ASTMV-{####}` | Yes | Records movement between locations |
| **Asset Assignment** | `ASTAS-{####}` | Yes | Records assignment to a user |

### Asset Status Lifecycle

```
  Available ──────────────────────────────► Scrapped
      │   ▲              ▲                     ▲
      ▼   │              │                     │
    In Use ──────────────┤                     │
      │   ▲          Maintenance ──────────────┘
      └───┘
```

---

## Roles & Permissions

| Role | Assets | Movements | Assignments | Categories | Locations |
|------|--------|-----------|-------------|------------|-----------|
| **System Manager** | Full | Full | Full | Full | Full |
| **Asset Manager** | Create/Edit | Create/Submit | Create/Submit | Create/Edit | Create/Edit |
| **Asset Employee** | Read-only | Read-only | Read-only | Read-only | Read-only |

---

## Installation

```bash
# 1. Get the app
cd /path/to/frappe-bench
bench get-app https://github.com/AaronShenny/AssetManagementSystem

# 2. Install on a site
bench --site your-site.local install-app asset_system

# 3. Run migrations
bench --site your-site.local migrate

# 4. Build static assets
bench build --app asset_system
```

Or for development (editable install):

```bash
pip install -e /path/to/asset_system/
```

---

## Whitelisted API

All endpoints are accessible at `/api/method/asset_system.api.asset_api.<method_name>`.

### `create_asset`

```python
import requests

response = requests.post(
    "https://your-site/api/method/asset_system.api.asset_api.create_asset",
    data={
        "asset_name": "Dell Laptop",
        "category": "Electronics",
        "location": "Head Office",
        "purchase_date": "2024-01-15",
        "purchase_value": 85000,
        "serial_number": "SN-12345",
    },
    headers={"Authorization": "token api_key:api_secret"},
)
# Response: {"message": {"asset_id": "AST-0001", "status": "Available", ...}}
```

### `get_assets`

```python
response = requests.get(
    "https://your-site/api/method/asset_system.api.asset_api.get_assets",
    params={"status": "Available", "page": 1, "page_length": 10},
    headers={"Authorization": "token api_key:api_secret"},
)
# Response: {"message": {"total": 42, "assets": [...]}}
```

### `move_asset`

```python
response = requests.post(
    "https://your-site/api/method/asset_system.api.asset_api.move_asset",
    data={
        "asset": "AST-0001",
        "to_location": "Branch Office",
        "remarks": "Relocated for project",
    },
    headers={"Authorization": "token api_key:api_secret"},
)
```

### `assign_asset`

```python
response = requests.post(
    "https://your-site/api/method/asset_system.api.asset_api.assign_asset",
    data={
        "asset": "AST-0001",
        "assigned_to": "john@example.com",
        "assigned_date": "2024-02-01",
    },
    headers={"Authorization": "token api_key:api_secret"},
)
```

### `get_asset_history`

```python
response = requests.get(
    "https://your-site/api/method/asset_system.api.asset_api.get_asset_history",
    params={"asset": "AST-0001"},
    headers={"Authorization": "token api_key:api_secret"},
)
# Response: {"message": {"asset": "AST-0001", "movements": [...], "assignments": [...]}}
```

### `get_dashboard_stats`

```python
response = requests.get(
    "https://your-site/api/method/asset_system.api.asset_api.get_dashboard_stats",
    headers={"Authorization": "token api_key:api_secret"},
)
# Response: {"message": {"total": 50, "available": 20, "in_use": 25, "maintenance": 3, "scrapped": 2}}
```

---

## Sample Test Data (bench console)

```python
import frappe

# 1. Create categories
frappe.get_doc({"doctype": "Asset Category", "category_name": "Electronics",    "depreciation_applicable": 1, "expected_life": 5}).insert()
frappe.get_doc({"doctype": "Asset Category", "category_name": "Furniture",      "depreciation_applicable": 1, "expected_life": 10}).insert()
frappe.get_doc({"doctype": "Asset Category", "category_name": "Office Supplies", "depreciation_applicable": 0}).insert()

# 2. Create locations
frappe.get_doc({"doctype": "Location", "location_name": "Head Office"}).insert()
frappe.get_doc({"doctype": "Location", "location_name": "Branch Office"}).insert()
frappe.get_doc({"doctype": "Location", "location_name": "IT Room", "parent_location": "Head Office"}).insert()

# 3. Create assets
laptop = frappe.get_doc({
    "doctype": "Asset",
    "asset_name": "Dell Laptop XPS 15",
    "category": "Electronics",
    "location": "Head Office",
    "purchase_date": "2024-01-15",
    "purchase_value": 85000,
    "serial_number": "SN-DELL-001",
})
laptop.insert()

# 4. Move asset
movement = frappe.get_doc({
    "doctype": "Asset Movement",
    "asset": laptop.name,
    "from_location": "Head Office",
    "to_location": "IT Room",
    "movement_date": frappe.utils.today(),
})
movement.insert()
movement.submit()

# 5. Assign asset
assignment = frappe.get_doc({
    "doctype": "Asset Assignment",
    "asset": laptop.name,
    "assigned_to": "administrator@example.com",
    "assigned_date": frappe.utils.today(),
})
assignment.insert()
assignment.submit()

frappe.db.commit()
print("Test data created!")
```

---

## hooks.py: How It Works

`hooks.py` is the main configuration file for a Frappe app. Key sections:

| Hook | Purpose |
|------|---------|
| `app_include_css / app_include_js` | Include custom CSS/JS on every Frappe Desk page |
| `doc_events` | Wire Python functions to DocType lifecycle events (validate, on_submit, etc.) |
| `fixtures` | Define what data is exported with `bench export-fixtures` |
| `scheduler_events` | Schedule background tasks (daily, weekly, etc.) |

---

## Running Tests

```bash
# Without a live Frappe site (unit tests only)
cd asset_system/
python -m pytest asset_system/tests/ -v

# With a live Frappe bench
bench run-tests --app asset_system
```