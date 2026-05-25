# Copyright (c) 2026, Aaron Shenny and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
class AssetSpecifications(Document):
    def validate(self):
        frappe.msgprint(f"Before: {self.spec}")

        if self.spec:
            self.spec = self.spec.strip().upper()

        frappe.msgprint(f"After: {self.spec}")
