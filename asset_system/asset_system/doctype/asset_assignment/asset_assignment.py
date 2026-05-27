import frappe
from frappe import _
from frappe.model.document import Document

from .helpers import is_assignment_active_status


class AssetAssignment(Document):
    def validate(self):
        self._validate_dates()
        if self._should_validate_asset_availability():
            self._validate_asset_available()
        self._sync_active_flag()

    def after_insert(self):
        self._assign_asset()
    def on_update(self):
        self._assign_asset()

    def on_trash(self):
        self._deactivate_assignment()
        self._unassign_asset()
        self._record_deallocated_on_trash()

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _validate_dates(self):
        if self.return_date and self.assigned_date:
            if self.return_date < self.assigned_date:
                frappe.throw(_("Return Date cannot be before Assigned Date."))

    def _validate_asset_available(self):
        """Prevent assigning an unavailable asset."""
        status = frappe.db.get_value("BYT Asset", self.asset, "status")
        if status == "Deregistered":
            frappe.throw(
                _("Asset {0} is deregistered and cannot be assigned.").format(self.asset)
            )
        if status in ("Assigned", "Maintenance"):
            frappe.throw(
                _("Asset {0} is not available for assignment.").format(self.asset)
            )

    def _should_validate_asset_availability(self):
        if self.is_new():
            return True

        # Test mocks may instantiate documents without full frappe Document helpers.
        if not callable(getattr(self, "has_value_changed", None)):
            return True

        if self.has_value_changed("asset"):
            return True

        return self.has_value_changed("status") and is_assignment_active_status(self.status)

    def _sync_active_flag(self):
        self.is_active = 1 if is_assignment_active_status(self.status) else 0

    def _deactivate_assignment(self):
        if self.name and frappe.db.exists("Asset Assignment", self.name):
            frappe.db.set_value("Asset Assignment", self.name, "is_active", 0, update_modified=False)

    def _unassign_asset(self):
        """On cancel, clear Asset.assigned_to and set status to Available."""
        current_status = frappe.db.get_value("BYT Asset", self.asset, "status")
        update_values = {"assigned_to": None}
        if current_status not in ("Maintenance", "Deregistered"):
            update_values["status"] = "Available"
        frappe.db.set_value("BYT Asset", self.asset, update_values)
    def _assign_asset(self):
        """Update Asset.assigned_to and keep status aligned with assignment activity."""
        asset_doc = frappe.get_doc("BYT Asset", self.asset)

        if not self.is_active:
            self._unassign_asset()
        else:
            asset_doc.assigned_to = self.assigned_to
            asset_doc.status = "Assigned"

        asset_doc.save(ignore_permissions=True)
        #frappe.db.set_value("BYT Asset", self.asset, {
        #    "assigned_to": self.assigned_to,
        #    "status": "In Use",
        #})
        # Send notification email if the assigned user has an email
        #user_email = frappe.db.get_value("User", self.assigned_to, "email")
        user_email = None
        if user_email:
            frappe.sendmail(
                recipients=[user_email],
                subject=_("Asset {0} has been assigned to you").format(self.asset),
                message=_(
                    "Dear {0},<br><br>"
                    "Asset <b>{1}</b> has been assigned to you on {2}.<br>"
                    "Please confirm receipt.<br><br>"
                    "Regards,<br>Asset Management System"
                ).format(self.assigned_to, self.asset, self.assigned_date),
            )

    

    def _record_deallocated_on_trash(self):
        """Record DEALLOCATED when an Asset Assignment document is deleted.

        _unassign_asset() uses frappe.db.set_value which bypasses BYT Asset
        lifecycle hooks, so we create the history entry here explicitly.
        """
        from asset_system.utils.asset_history_service import create_asset_history

        create_asset_history(
            asset=self.asset,
            action_type="DEALLOCATED",
            reference_doctype="Asset Assignment",
            reference_docname=self.name,
            remarks=f"Assignment {self.name} was deleted.",
            changes=[
                {
                    "field_name": "Assigned To",
                    "old_data": self.assigned_to or "",
                    "new_data": "",
                }
            ],
        )


# ------------------------------------------------------------------ #
# Module-level hooks wired via hooks.py                               #
# ------------------------------------------------------------------ #


def validate(doc, method=None):
    doc.validate()


def on_submit(doc, method=None):
    doc.on_submit()


def on_cancel(doc, method=None):
    doc.on_cancel()
