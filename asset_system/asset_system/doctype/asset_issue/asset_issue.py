# Copyright (c) 2026, Aaron Shenny and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document


class AssetIssue(Document):


    def on_update(self):

        if self.status not in ["Open", "Resolved", "Closed"]:

            asset_doc = frappe.get_doc("BYT Asset", self.asset)

            asset_doc.status = "Maintenance"

            asset_doc.save()
