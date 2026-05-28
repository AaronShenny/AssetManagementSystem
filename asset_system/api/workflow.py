import frappe
from frappe.model.workflow import get_transitions
@frappe.whitelist()
def get_actions(docname):
    doc = frappe.get_doc("Asset Issue", docname)
    return get_transitions(doc)
