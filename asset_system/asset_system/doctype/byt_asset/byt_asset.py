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
    def after_insert(self):
        self.create_user_permission()

    def on_update(self):
        self.create_user_permission()
    
    def create_user_permission(self):

        if not self.assigned_to:

            existing_asset_permission = frappe.db.exists(
                "User Permission",
                {
                    "allow": "BYT Asset",
                    "for_value": self.name
                }
            )

            if existing_asset_permission:
                frappe.delete_doc(
                    "User Permission",
                    existing_asset_permission,
                    ignore_permissions=True
                )

            return

        # Get linked user
        user = frappe.db.get_value(
            "User",
            self.assigned_to,
            "name"
        )

        if not user:
            return

        # Avoid duplicate permissions
        exists = frappe.db.exists(
            "User Permission",
            {
                "user": user,
                "allow": "BYT Asset",
                "for_value": self.name
            }
        )

        if exists:
            return

        # Create permission
        perm = frappe.get_doc({
            "doctype": "User Permission",
            "user": user,
            "allow": "BYT Asset",
            "for_value": self.name,
            "apply_to_all_doctypes": 1
        })

        perm.insert(ignore_permissions=True)
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

    @frappe.whitelist()
    def move_asset(self, new_location):
        self.location = new_location
        self.save()
        return self

    @frappe.whitelist()
    def assign_asset(self, user):
        self.assigned_to = user
        self.save()
        return self


# ------------------------------------------------------------------ #
# Module-level functions wired via hooks.py doc_events                #
# ------------------------------------------------------------------ #

def get_permission_query_conditions(user):

    if not user:
        user = frappe.session.user

    if "System Manager" in frappe.get_roles(user):
        return ""

    if "Asset Manager" in frappe.get_roles(user):
        return ""

    if "Asset Employee" in frappe.get_roles(user):
        return f"`tabBYT Asset`.assigned_to = {frappe.db.escape(user)}"

    return "1=0"
def before_insert(doc, method=None):
    doc.before_insert()


def validate(doc, method=None):
    doc.validate()
