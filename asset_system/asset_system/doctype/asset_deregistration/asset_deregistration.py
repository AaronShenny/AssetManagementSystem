# Copyright (c) 2026, Aaron Shenny and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AssetDeregistration(Document):
    def before_save(self):
        asset = frappe.get_doc("BYT Asset", self.asset)
        if asset.status == "Deregistered":
            frappe.throw(
                f"Asset {asset.name} is already deregistered"

            )
        if asset.status=="Assigned":
            frappe.throw(
                f"Asset {asset.name} is currently assigned to {asset.assigned_to}. "
                "Please deallocate the asset before deregistering it."
            )
    def after_insert(self):
        self._record_deregistration_request()

    def on_update(self):
        if self.has_value_changed("status"):
            if self.status == "Approved":
                self._approve_deregistration()
            elif self.status == "Rejected":
                self._record_deregistration_rejected()

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _approve_deregistration(self):
        """Mark the linked asset as Deregistered and record approval history."""
        from asset_system.utils.asset_history_service import create_asset_history

        asset = frappe.get_doc("BYT Asset", self.asset)
        
        # Prevent deregistration of assigned assets
        if asset.status=="Assigned":
            frappe.throw(
                f"Asset {asset.name} is currently assigned to {asset.assigned_to}. "
                "Please deallocate the asset before deregistering it."
            )
        create_asset_history(
            asset=self.asset,
            action_type="DEREGISTRATION APPROVED",
            reference_doctype="Asset Deregistration",
            reference_docname=self.name,
            remarks=f"Deregistration approved. Reason: {self.reason or 'N/A'}.",
        )
        if asset.status != "Deregistered":
            asset.status = "Deregistered"
            asset.save(ignore_permissions=True)

        

    def _record_deregistration_request(self):
        """Record that a deregistration request was submitted."""
        asset = frappe.get_doc("BYT Asset", self.asset)
        from asset_system.utils.asset_history_service import create_asset_history
        if asset.status=="Assigned":
            frappe.throw(
                f"Asset {asset.name} is currently assigned to {asset.assigned_to}. "
                "Please deallocate the asset before deregistering it."
            )
        
        create_asset_history(
            asset=self.asset,
            action_type="DEREGISTRATION REQUEST",
            reference_doctype="Asset Deregistration",
            reference_docname=self.name,
            remarks=f"Deregistration requested. Reason: {self.reason or 'N/A'}.",
        )

    def _record_deregistration_rejected(self):
        """Record that a deregistration request was rejected."""
        from asset_system.utils.asset_history_service import create_asset_history

        create_asset_history(
            asset=self.asset,
            action_type="DEREGISTRATION REJECTED",
            reference_doctype="Asset Deregistration",
            reference_docname=self.name,
            remarks=f"Deregistration rejected. Reason: {self.reason or 'N/A'}.",
        )
