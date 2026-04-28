import frappe


def execute():
    """Rename the custom 'Asset' DocType to 'BYT Asset'.

    Guards against accidentally renaming ERPNext's built-in Asset DocType by
    checking the module owner before proceeding.
    """
    if not frappe.db.exists("DocType", "Asset"):
        return
    if frappe.db.get_value("DocType", "Asset", "module") != "Asset System":
        return
    if frappe.db.exists("DocType", "BYT Asset"):
        return
    frappe.rename_doc("DocType", "Asset", "BYT Asset", force=True)
    frappe.db.commit()
