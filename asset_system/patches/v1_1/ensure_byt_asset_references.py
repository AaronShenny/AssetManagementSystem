import frappe


OLD_DOCTYPE = "Asset"
NEW_DOCTYPE = "BYT Asset"
APP_MODULE = "Asset System"


def execute():
    _rename_custom_asset_doctype()
    _update_link_field_options()
    _update_workspace_links_and_shortcuts()
    _update_workspace_content_json()
    frappe.clear_cache(doctype=NEW_DOCTYPE)
    frappe.db.commit()


def _rename_custom_asset_doctype():
    old_exists = frappe.db.exists("DocType", OLD_DOCTYPE)
    new_exists = frappe.db.exists("DocType", NEW_DOCTYPE)

    if not old_exists:
        return

    old_module = frappe.db.get_value("DocType", OLD_DOCTYPE, "module")

    # Never touch ERPNext's built-in Asset DocType.
    if old_module != APP_MODULE:
        return

    if new_exists:
        frappe.throw(
            "Both custom DocTypes 'Asset' and 'BYT Asset' exist in module 'Asset System'. "
            "Please merge/fix manually, then re-run migrate."
        )

    frappe.rename_doc("DocType", OLD_DOCTYPE, NEW_DOCTYPE, force=True)


def _update_link_field_options():
    # Standard DocFields in this app's DocTypes.
    frappe.db.sql(
        """
        UPDATE `tabDocField` df
        INNER JOIN `tabDocType` dt ON dt.name = df.parent
        SET df.options = %s
        WHERE df.fieldtype = 'Link'
          AND df.options = %s
          AND dt.module = %s
        """,
        (NEW_DOCTYPE, OLD_DOCTYPE, APP_MODULE),
    )

    # Custom Fields targeting this app's DocTypes.
    frappe.db.sql(
        """
        UPDATE `tabCustom Field`
        SET options = %s
        WHERE fieldtype = 'Link'
          AND options = %s
          AND dt IN (
              SELECT name
              FROM `tabDocType`
              WHERE module = %s
          )
        """,
        (NEW_DOCTYPE, OLD_DOCTYPE, APP_MODULE),
    )

    # Property Setters overriding link options on this app's DocTypes.
    frappe.db.sql(
        """
        UPDATE `tabProperty Setter`
        SET value = %s
        WHERE property = 'options'
          AND value = %s
          AND doc_type IN (
              SELECT name
              FROM `tabDocType`
              WHERE module = %s
          )
        """,
        (NEW_DOCTYPE, OLD_DOCTYPE, APP_MODULE),
    )


def _update_workspace_links_and_shortcuts():
    frappe.db.sql(
        """
        UPDATE `tabWorkspace Link`
        SET link_to = %s
        WHERE link_to = %s
          AND parent IN (
              SELECT name
              FROM `tabWorkspace`
              WHERE module = %s
          )
        """,
        (NEW_DOCTYPE, OLD_DOCTYPE, APP_MODULE),
    )

    frappe.db.sql(
        """
        UPDATE `tabWorkspace Shortcut`
        SET link_to = %s
        WHERE link_to = %s
          AND parent IN (
              SELECT name
              FROM `tabWorkspace`
              WHERE module = %s
          )
        """,
        (NEW_DOCTYPE, OLD_DOCTYPE, APP_MODULE),
    )


def _update_workspace_content_json():
    frappe.db.sql(
        """
        UPDATE `tabWorkspace`
        SET content = REPLACE(content, %s, %s)
        WHERE module = %s
          AND IFNULL(content, '') != ''
          AND content LIKE %s
        """,
        (
            '"shortcut_name":"Asset"',
            '"shortcut_name":"BYT Asset"',
            APP_MODULE,
            '%"shortcut_name":"Asset"%',
        ),
    )
