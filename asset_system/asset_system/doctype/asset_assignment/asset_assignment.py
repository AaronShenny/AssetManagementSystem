import frappe
from frappe import _
from frappe.model.document import Document


class AssetAssignment(Document):
    def validate(self):
        self._validate_dates()
        self._validate_asset_available()

    def on_submit(self):
        self._assign_asset()

    def on_cancel(self):
        self._unassign_asset()

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _validate_dates(self):
        if self.return_date and self.assigned_date:
            if self.return_date < self.assigned_date:
                frappe.throw(_("Return Date cannot be before Assigned Date."))

    def _validate_asset_available(self):
        """Prevent assigning a Scrapped asset."""
        status = frappe.db.get_value("BYT Asset", self.asset, "status")
        if status == "Scrapped":
            frappe.throw(
                _("Asset {0} is Scrapped and cannot be assigned.").format(self.asset)
            )

    def _assign_asset(self):
        """On submit, update Asset.assigned_to and set status to In Use."""
        frappe.db.set_value("BYT Asset", self.asset, {
            "assigned_to": self.assigned_to,
            "status": "In Use",
        })
        # Send notification email if the assigned user has an email
        user_email = frappe.db.get_value("User", self.assigned_to, "email")
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

    def _unassign_asset(self):
        """On cancel, clear Asset.assigned_to and set status to Available."""
        frappe.db.set_value("BYT Asset", self.asset, {
            "assigned_to": None,
            "status": "Available",
        })


# ------------------------------------------------------------------ #
# Module-level hooks wired via hooks.py                               #
# ------------------------------------------------------------------ #


def validate(doc, method=None):
    doc.validate()


def on_submit(doc, method=None):
    doc.on_submit()


def on_cancel(doc, method=None):
    doc.on_cancel()
