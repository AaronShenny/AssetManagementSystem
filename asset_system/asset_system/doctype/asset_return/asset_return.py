# asset_return.py

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class AssetReturn(Document):
    def validate(self):
        self._validate_basic_fields()
        assignment = self._get_assignment()
        self._validate_matches_assignment(assignment)
        self._validate_dates(assignment)

    def on_submit(self):
        self._apply_return_to_assignment()
        self._record_deallocated()

    def on_cancel(self):
        self._revert_assignment()

    def _get_assignment(self):
        if not self.asset_assignment:
            frappe.throw(_("Asset Assignment is required."))

        if not frappe.db.exists("Asset Assignment", self.asset_assignment):
            frappe.throw(_("Asset Assignment {0} does not exist.").format(self.asset_assignment))

        return frappe.get_doc("Asset Assignment", self.asset_assignment)

    def _validate_basic_fields(self):
        if not self.returned_date:
            frappe.throw(_("Returned Date is required."))

        if not self.return_reason:
            frappe.throw(_("Return Reason is required."))

    def _validate_matches_assignment(self, assignment):
        if self.asset != assignment.asset:
            frappe.throw(
                _("Selected Asset does not match the Asset in the linked Asset Assignment.")
            )

        if self.employee != assignment.assigned_to:
            frappe.throw(
                _("Selected Employee does not match the Assigned To user in the linked Asset Assignment.")
            )

        if assignment.status != "Assigned":
            frappe.throw(
                _("Only an Asset Assignment with status Assigned can be returned. Current status is {0}.").format(
                    assignment.status
                )
            )

    def _validate_dates(self, assignment):
        returned_date = getdate(self.returned_date)
        today = getdate(nowdate())

        if returned_date > today:
            frappe.throw(_("Returned Date cannot be in the future."))

        if assignment.assigned_date and returned_date < getdate(assignment.assigned_date):
            frappe.throw(_("Returned Date cannot be before Assigned Date."))

        if assignment.return_date and getdate(assignment.return_date) <= returned_date:
            frappe.throw(_("This Asset Assignment already has a return date set."))

    def _apply_return_to_assignment(self):
        assignment = self._get_assignment()

        # Asset Assignment only allows these status values:
        # Assigned / Returned / Replacement / Off Board
        # So map the return reason to a valid status.
        status_map = {
            "Off Board": "Off Board",
            "Replacement": "Replacement",
            "Damage": "Returned",
            "Other Reason": "Returned",
        }
        new_status = status_map.get(self.return_reason, "Returned")
# use doc.save, frappe.db.set_value dosent triggers validate,on_update things like that
        frappe.db.set_value(
            "Asset Assignment",
            self.asset_assignment,
            {
                "status": new_status,
                "return_date": self.returned_date,
                "remarks": self.remarks or assignment.remarks,
            },
            update_modified=True,
        )

        # Optional: if your BYT Asset doctype has fields for release/reset,
        # update them here. Keep this only if those fields actually exist.
        frappe.db.set_value(
            "BYT Asset",
             self.asset,
            {
                "assigned_to": None,
                "status": "Available",
            },
            update_modified=True,
        )

    def _revert_assignment(self):
        # Revert the linked assignment if this return doc is cancelled.
        frappe.db.set_value(
            "Asset Assignment",
            self.asset_assignment,
            {
                "status": "Assigned",
                "return_date": None,
            },
            update_modified=True,
        )

    def _record_deallocated(self):
        """Record DEALLOCATED history after a formal asset return.

        _apply_return_to_assignment() uses frappe.db.set_value on BYT Asset,
        which bypasses its lifecycle hooks, so we create the history here.
        """
        from asset_system.utils.asset_history_service import create_asset_history

        reason_label = self.return_reason or "Return"
        create_asset_history(
            asset=self.asset,
            action_type="DEALLOCATED",
            reference_doctype="Asset Return",
            reference_docname=self.name,
            remarks=f"Asset returned by {self.employee}. Reason: {reason_label}.",
            changes=[
                {
                    "field_name": "Assigned To",
                    "old_data": self.employee or "",
                    "new_data": "",
                },
                {
                    "field_name": "Return Reason",
                    "old_data": "",
                    "new_data": reason_label,
                },
            ],
        )
