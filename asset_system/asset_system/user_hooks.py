

import frappe

def assign_default_role(doc, method):
    frappe.db.set_value("User", doc.name, "user_type", "System User")

    if not frappe.db.exists(
        "Has Role",
        {"parent": doc.name, "role": "Employee"}
    ):
        frappe.get_doc({
            "doctype": "Has Role",
            "parent": doc.name,
            "parenttype": "User",
            "parentfield": "roles",
            "role": "Employee"
        }).insert(ignore_permissions=True)
