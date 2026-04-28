import frappe
from frappe.model.document import Document


class Location(Document):
    def validate(self):
        if self.parent_location == self.name:
            frappe.throw(frappe._("A location cannot be its own parent."))
