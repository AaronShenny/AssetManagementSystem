import json

import frappe


OLD_DOCTYPE = "Asset"
NEW_DOCTYPE = "BYT Asset"
APP_MODULE = "Asset System"


def execute():
    if _should_exit_early():
        frappe.logger().info("[Asset Rename Patch] Skipping patch execution; safe no-op.")
        frappe.clear_cache()
        frappe.db.commit()
        return

    _rename_custom_asset_doctype()
    _update_docfield_options()
    _update_custom_field_options()
    _update_property_setter_values()
    _update_workspace_link_to_values()
    _update_workspace_shortcut_link_to_values()
    _update_workspace_content_json()

    frappe.clear_cache(doctype=NEW_DOCTYPE)
    frappe.clear_cache()
    frappe.db.commit()


def _should_exit_early():
    old_exists = frappe.db.exists("DocType", OLD_DOCTYPE)
    new_exists = frappe.db.exists("DocType", NEW_DOCTYPE)

    if new_exists and not old_exists:
        return True

    if old_exists:
        old_module = frappe.db.get_value("DocType", OLD_DOCTYPE, "module")
        if old_module != APP_MODULE:
            return True

    return False


def _rename_custom_asset_doctype():
    if not frappe.db.exists("DocType", OLD_DOCTYPE):
        return

    if frappe.db.exists("DocType", NEW_DOCTYPE):
        frappe.logger().info(
            "[Asset Rename Patch] '%s' already exists. Skipping rename from '%s'.",
            NEW_DOCTYPE,
            OLD_DOCTYPE,
        )
        return

    module = frappe.db.get_value("DocType", OLD_DOCTYPE, "module")
    if module != APP_MODULE:
        frappe.logger().info(
            "[Asset Rename Patch] '%s' belongs to module '%s'. Skipping rename.",
            OLD_DOCTYPE,
            module,
        )
        return

    frappe.rename_doc("DocType", OLD_DOCTYPE, NEW_DOCTYPE, force=True)
    frappe.logger().info(
        "[Asset Rename Patch] Renamed DocType from '%s' to '%s'.",
        OLD_DOCTYPE,
        NEW_DOCTYPE,
    )


def _update_docfield_options():
    rows = frappe.get_all(
        "DocField",
        filters={"fieldtype": "Link", "options": OLD_DOCTYPE},
        fields=["name", "parent", "fieldname", "options"],
        limit_page_length=0,
    )

    for row in rows:
        parent_module = frappe.db.get_value("DocType", row.parent, "module")
        if parent_module != APP_MODULE:
            continue

        if row.options == OLD_DOCTYPE:
            frappe.db.set_value("DocField", row.name, "options", NEW_DOCTYPE, update_modified=False)
            frappe.logger().info(
                "[Asset Rename Patch] Updated DocField.options in '%s.%s' from '%s' to '%s'.",
                row.parent,
                row.fieldname,
                OLD_DOCTYPE,
                NEW_DOCTYPE,
            )


def _update_custom_field_options():
    rows = frappe.get_all(
        "Custom Field",
        filters={"fieldtype": "Link", "options": OLD_DOCTYPE},
        fields=["name", "dt", "fieldname", "options"],
        limit_page_length=0,
    )

    for row in rows:
        dt_module = frappe.db.get_value("DocType", row.dt, "module")
        if dt_module != APP_MODULE:
            continue

        if row.options == OLD_DOCTYPE:
            frappe.db.set_value("Custom Field", row.name, "options", NEW_DOCTYPE, update_modified=False)
            frappe.logger().info(
                "[Asset Rename Patch] Updated Custom Field.options in '%s.%s' from '%s' to '%s'.",
                row.dt,
                row.fieldname,
                OLD_DOCTYPE,
                NEW_DOCTYPE,
            )


def _update_property_setter_values():
    rows = frappe.get_all(
        "Property Setter",
        filters={"property": "options", "value": OLD_DOCTYPE},
        fields=["name", "doc_type", "field_name", "value"],
        limit_page_length=0,
    )

    for row in rows:
        doc_type_module = frappe.db.get_value("DocType", row.doc_type, "module")
        if doc_type_module != APP_MODULE:
            continue

        if row.value == OLD_DOCTYPE:
            frappe.db.set_value("Property Setter", row.name, "value", NEW_DOCTYPE, update_modified=False)
            frappe.logger().info(
                "[Asset Rename Patch] Updated Property Setter.value in '%s.%s' from '%s' to '%s'.",
                row.doc_type,
                row.field_name,
                OLD_DOCTYPE,
                NEW_DOCTYPE,
            )


def _update_workspace_link_to_values():
    rows = frappe.get_all(
        "Workspace Link",
        filters={"link_to": OLD_DOCTYPE},
        fields=["name", "parent", "label", "link_to"],
        limit_page_length=0,
    )

    for row in rows:
        module = frappe.db.get_value("Workspace", row.parent, "module")
        if module != APP_MODULE:
            continue

        if row.link_to == OLD_DOCTYPE:
            frappe.db.set_value("Workspace Link", row.name, "link_to", NEW_DOCTYPE, update_modified=False)
            frappe.logger().info(
                "[Asset Rename Patch] Updated Workspace Link.link_to in workspace '%s' (label '%s') from '%s' to '%s'.",
                row.parent,
                row.label,
                OLD_DOCTYPE,
                NEW_DOCTYPE,
            )


def _update_workspace_shortcut_link_to_values():
    rows = frappe.get_all(
        "Workspace Shortcut",
        filters={"link_to": OLD_DOCTYPE},
        fields=["name", "parent", "label", "link_to"],
        limit_page_length=0,
    )

    for row in rows:
        module = frappe.db.get_value("Workspace", row.parent, "module")
        if module != APP_MODULE:
            continue

        if row.link_to == OLD_DOCTYPE:
            frappe.db.set_value("Workspace Shortcut", row.name, "link_to", NEW_DOCTYPE, update_modified=False)
            frappe.logger().info(
                "[Asset Rename Patch] Updated Workspace Shortcut.link_to in workspace '%s' (label '%s') from '%s' to '%s'.",
                row.parent,
                row.label,
                OLD_DOCTYPE,
                NEW_DOCTYPE,
            )


def _update_workspace_content_json():
    workspaces = frappe.get_all(
        "Workspace",
        filters={"module": APP_MODULE},
        fields=["name", "content"],
        limit_page_length=0,
    )

    for workspace in workspaces:
        content = workspace.content
        if not content:
            continue

        try:
            payload = json.loads(content)
        except Exception:
            frappe.logger().info(
                "[Asset Rename Patch] Workspace '%s' has non-JSON content. Skipping.",
                workspace.name,
            )
            continue

        changed = _update_workspace_json_payload(payload)
        if not changed:
            continue

        frappe.db.set_value(
            "Workspace",
            workspace.name,
            "content",
            json.dumps(payload),
            update_modified=False,
        )
        frappe.logger().info(
            "[Asset Rename Patch] Updated Workspace.content JSON for workspace '%s'.",
            workspace.name,
        )


def _update_workspace_json_payload(node):
    changed = False

    if isinstance(node, dict):
        if "shortcut_name" in node and node["shortcut_name"] == OLD_DOCTYPE:
            node["shortcut_name"] = NEW_DOCTYPE
            changed = True
            frappe.logger().info(
                "[Asset Rename Patch] Updated Workspace.content shortcut_name from '%s' to '%s'.",
                OLD_DOCTYPE,
                NEW_DOCTYPE,
            )

        if "link_to" in node and node["link_to"] == OLD_DOCTYPE:
            node["link_to"] = NEW_DOCTYPE
            changed = True
            frappe.logger().info(
                "[Asset Rename Patch] Updated Workspace.content link_to from '%s' to '%s'.",
                OLD_DOCTYPE,
                NEW_DOCTYPE,
            )

        for value in node.values():
            if _update_workspace_json_payload(value):
                changed = True

    elif isinstance(node, list):
        for item in node:
            if _update_workspace_json_payload(item):
                changed = True

    return changed
