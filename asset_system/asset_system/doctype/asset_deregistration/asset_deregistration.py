# Copyright (c) 2026, Aaron Shenny and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AssetDeregistration(Document):

    def on_update(self):
        if self.has_value_changed("status") and self.status == "Approved":
            asset = frappe.get_doc("BYT Asset", self.asset)

            if asset.status != "Deregistered":
                asset.status = "Deregistered"
                asset.save(ignore_permissions=True)
