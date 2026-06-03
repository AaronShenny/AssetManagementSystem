
import frappe

@frappe.whitelist(allow_guest=True)
def callback():
    return {
        "args": frappe.form_dict
    }
