import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

# Status transition rules
ALLOWED_TRANSITIONS = {
    "Available": ["In Use", "Maintenance", "Scrapped"],
    "In Use": ["Available", "Maintenance", "Scrapped"],
    "Maintenance": ["Available", "In Use", "Scrapped"],
    "Scrapped": [],  # terminal state
}


class BYTAsset(Document):
    # ------------------------------------------------------------------ #
    # Lifecycle hooks (also wired via hooks.py for external callers)      #
    # ------------------------------------------------------------------ #

    def before_insert(self):
        """Set the asset_id field from the autoname value before saving."""
        # `name` is set by autoname at this point; mirror it to asset_id
        if not self.asset_id:
            self.asset_id = self.name

    def validate(self):
        self._validate_status_transition()
        self._validate_assigned_to()

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _validate_status_transition(self):
        """Enforce allowed lifecycle transitions when status changes."""
        if self.is_new():
            return
        old_status = frappe.db.get_value("BYT Asset", self.name, "status")
        if not old_status or old_status == self.status:
            return
        allowed = ALLOWED_TRANSITIONS.get(old_status, [])
        if self.status not in allowed:
            frappe.throw(
                _("Status transition from '{0}' to '{1}' is not allowed.").format(
                    old_status, self.status
                )
            )

    def _validate_assigned_to(self):
        """Keep status consistent with assigned_to field."""
        if self.assigned_to and self.status == "Available":
            self.status = "In Use"
        if not self.assigned_to and self.status == "In Use":
            self.status = "Available"


# ------------------------------------------------------------------ #
# Module-level functions wired via hooks.py doc_events                #
# ------------------------------------------------------------------ #


def before_insert(doc, method=None):
    doc.before_insert()


def validate(doc, method=None):
    doc.validate()
