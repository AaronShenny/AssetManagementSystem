from __future__ import unicode_literals

app_name = "asset_system"
app_title = "Asset System"
app_publisher = "Aaron Shenny"
app_description = "A fully independent Asset Management System built on Frappe Framework"
app_icon = "octicon octicon-package"
app_color = "#2490EF"
app_email = ""
app_license = "MIT"
app_version = "1.0.0"

# ------------------------------------------------------------------
# DocTypes list for this app
# ------------------------------------------------------------------
# Includes in <head>
# ------------------------------------------------------------------
# app_include_css = "/assets/asset_system/css/asset_system.css"
# app_include_js = "/assets/asset_system/js/asset_system.js"

app_include_css = ["/assets/asset_system/css/asset_system.css"]
app_include_js = ["/assets/asset_system/js/asset_system.js"]

# ------------------------------------------------------------------
# Fixtures – export these DocTypes when running bench export-fixtures
# ------------------------------------------------------------------
fixtures = [
    {"dt": "Role", "filters": [["name", "in", ["Asset Manager", "Asset Employee"]]]},
    {"dt": "Workspace", "filters": [["name", "in", ["Asset System"]]]},
]

# ------------------------------------------------------------------
# Document Events (hooks on insert/update/etc.)
# ------------------------------------------------------------------
doc_events = {
    "Asset": {
        "before_insert": "asset_system.asset_system.doctype.asset.asset.before_insert",
        "validate": "asset_system.asset_system.doctype.asset.asset.validate",
    },
    "Asset Movement": {
        "validate": "asset_system.asset_system.doctype.asset_movement.asset_movement.validate",
        "on_submit": "asset_system.asset_system.doctype.asset_movement.asset_movement.on_submit",
    },
    "Asset Assignment": {
        "validate": "asset_system.asset_system.doctype.asset_assignment.asset_assignment.validate",
        "on_submit": "asset_system.asset_system.doctype.asset_assignment.asset_assignment.on_submit",
        "on_cancel": "asset_system.asset_system.doctype.asset_assignment.asset_assignment.on_cancel",
    },
}

# ------------------------------------------------------------------
# Scheduled tasks
# ------------------------------------------------------------------
# scheduler_events = {
#     "daily": ["asset_system.tasks.daily"],
# }

# ------------------------------------------------------------------
# Jinja environments
# ------------------------------------------------------------------
# jinja = {
#     "methods": "asset_system.utils.jinja_methods",
# }
