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
    {
        "dt": "Role",
        "filters": [["name", "in", ["Infra Executive", "Infra Admin", "Leadership", "Employee"]]],
    },
    {"dt": "Workspace", "filters": [["name", "in", ["Asset System"]]]},
]

# ------------------------------------------------------------------
# Document Events (hooks on insert/update/etc.)
# ------------------------------------------------------------------
doc_events = {
    "BYT Asset": {
        "before_insert": "asset_system.asset_system.doctype.byt_asset.byt_asset.before_insert",
        "validate": "asset_system.asset_system.doctype.byt_asset.byt_asset.validate",
    },

   
}
permission_query_conditions = {
    "BYT Asset": "asset_system.asset_system.doctype.byt_asset.byt_asset.get_permission_query_conditions"
}
has_permission = {
    "BYT Asset": "asset_system.asset_system.doctype.byt_asset.byt_asset.has_permission"
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
