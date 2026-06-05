import frappe
from frappe import _
from frappe.model.document import Document

from asset_system.asset_system.doctype.asset_assignment.helpers import (
    get_active_assignment,
    has_active_assignment,
)

# Status transition rules
ALLOWED_TRANSITIONS = {
    "Available": ["Assigned", "Maintenance", "Deregistered"],
    "Assigned": ["Available", "Maintenance"],
    "Maintenance": ["Available", "Assigned", "Deregistered"],
    "Deregistered": [],  # terminal state
    
}

# Labels of BYT Asset fields that produce an UPDATED history entry.
# Kept at module level to avoid recreating the set on every call.
_UPDATED_TRACK_LABELS = frozenset(
    {
        "Asset Name",
        "Serial Number",
        "Category",
        "Purchase Date",
        "Purchase Value",
        "Description",
    }
)


class BYTAsset(Document):
    # ------------------------------------------------------------------ #
    # Lifecycle hooks (also wired via hooks.py for external callers)      #
    # ------------------------------------------------------------------ #
    def after_insert(self):
        _record_new_registration(self)

    def on_update(self):
        _record_asset_update(self)

    def before_insert(self):
        """Set the asset_id field from the autoname value before saving."""
        # `name` is set by autoname at this point; mirror it to asset_id
        if not self.asset_id:
            self.asset_id = self.name

    def validate(self):
        self._validate_status_transition()
        self._validate_assignment_status()
        self._warranty_date_check()
        

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #
    def _warranty_date_check(self):
        if self.warranty_expiry_date < self.purchase_date:
            frappe.throw(
                _("Warrenty date should not be less than Purchase date"))
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

    def _validate_assignment_status(self):
        """Keep status consistent with active assignment state."""
        if not self.name:
            return

        has_assignment = has_active_assignment(self.name)
        if has_assignment and self.status == "Available":
            self.status = "Assigned"
        if not has_assignment and self.status == "Assigned":
            self.status = "Available"

    @frappe.whitelist()
    def move_asset(self, new_location):
        self.location = new_location
        self.save()
        return self

    @frappe.whitelist()
    def assign_asset(self, user):
        existing = get_active_assignment(self.name)
        if existing:
            frappe.throw(
                _("Asset '{0}' already has an active assignment. Unassign it before creating a new one.").format(
                    self.name
                )
            )
        assignment = frappe.get_doc(
            {
                "doctype": "Asset Assignment",
                "asset": self.name,
                "assigned_to": user,
                "assigned_date": frappe.utils.nowdate(),
                "status": "Assigned",
            }
        )
        assignment.insert(ignore_permissions=True)
        return assignment
    

# ------------------------------------------------------------------ #
# Module-level functions wired via hooks.py doc_events                #
# ------------------------------------------------------------------ #
def has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))

    if roles.intersection({"Infra Admin", "Infra Executive", "Leadership"}):
        return True

    if "Employee" in roles:
        active_assignment = get_active_assignment(doc.name)
        return bool(active_assignment and active_assignment.get("assigned_to") == user)
    return False

def get_permission_query_conditions(user):

    if not user:
        user = frappe.session.user

    roles = set(frappe.get_roles(user))
    if roles.intersection({"Infra Admin", "Infra Executive", "Leadership"}):
        return ""

    if "Employee" in roles:
        escaped_user = frappe.db.escape(user)
        print(escaped_user)
        return (
            "exists (select 1 from `tabAsset Assignment` aa "
            f"where aa.asset = `tabBYT Asset`.name and aa.assigned_to = {escaped_user} and aa.is_active = 1)"
        )

    return "1=0"
def before_insert(doc, method=None):
    doc.before_insert()


def validate(doc, method=None):
    doc.validate()


# ---------------------------------------------------------------------------
# Asset History tracking helpers
# ---------------------------------------------------------------------------

def _record_new_registration(doc):
    """Fire NEW REGISTRATION after a BYT Asset is first created."""
    from asset_system.utils.asset_history_service import create_asset_history

    create_asset_history(
        asset=doc.name,
        action_type="NEW REGISTRATION",
        reference_doctype="BYT Asset",
        reference_docname=doc.name,
        remarks="Asset registered in the system.",
    )


def _record_asset_update(doc):
    """Inspect what changed on BYT Asset and fire the appropriate history action.

    Priority order (first match wins):
      1. Status → Maintenance          → UNDER MAINTENANCE
      2. Status from Maintenance → *   → RESTORED
      3. Status → Deregistered         → DEREGISTERED
      4. location changed              → MOVED
      5. specification table changed   → SPECIFICATION UPDATED
      6. Other meaningful fields       → UPDATED
    """
    from asset_system.utils.asset_history_service import (
        create_asset_history,
        detect_field_changes,
        detect_child_table_changes,
    )

    # _doc_before_save is None for brand-new documents; on_update fires for
    # inserts too, so we skip here — after_insert already fired NEW REGISTRATION.
    old_doc = doc.get_doc_before_save()
    if old_doc is None:
        return

    # Guard: skip during framework migrations / installs
    if frappe.flags.in_install or frappe.flags.in_migrate:
        return

    old_status = old_doc.get("status") or ""
    new_status = doc.status or ""

    # --- 1 & 2 & 3: Status transitions ---------------------------------
    if old_status != new_status:
        if new_status == "Maintenance":
            create_asset_history(
                asset=doc.name,
                action_type="UNDER MAINTENANCE",
                reference_doctype="BYT Asset",
                reference_docname=doc.name,
                changes=[
                    {
                        "field_name": "Status",
                        "old_data": old_status,
                        "new_data": new_status,
                    }
                ],
            )
            return

        if old_status == "Maintenance" and new_status not in ("Maintenance", "Deregistered"):
            # Skip RESTORED when transitioning directly from Maintenance to
            # Deregistered — the DEREGISTERED entry (priority 3) handles that.
            create_asset_history(
                asset=doc.name,
                action_type="RESTORED",
                reference_doctype="BYT Asset",
                reference_docname=doc.name,
                changes=[
                    {
                        "field_name": "Status",
                        "old_data": old_status,
                        "new_data": new_status,
                    }
                ],
            )
            return

        if new_status == "Deregistered":
            create_asset_history(
                asset=doc.name,
                action_type="DEREGISTERED in Asset page",
                reference_doctype="BYT Asset",
                reference_docname=doc.name,
                changes=[
                    {
                        "field_name": "Status",
                        "old_data": old_status,
                        "new_data": new_status,
                    }
                ],
            )
            return

    # --- 4: Direct location change (not via Asset Movement doc) --------
    old_location = old_doc.get("location") or ""
    new_location = doc.location or ""

    if old_location != new_location:
        create_asset_history(
            asset=doc.name,
            action_type="MOVED",
            reference_doctype="BYT Asset",
            reference_docname=doc.name,
            changes=[
                {
                    "field_name": "Location",
                    "old_data": old_location,
                    "new_data": new_location,
                }
            ],
        )
        return

    # --- 5: Specification child-table changes --------------------------
    spec_change = detect_child_table_changes(doc, old_doc, "specification")
    if spec_change:
        create_asset_history(
            asset=doc.name,
            action_type="SPECIFICATION UPDATED",
            reference_doctype="BYT Asset",
            reference_docname=doc.name,
            changes=spec_change,
        )
        return

    # --- 6: Other meaningful field changes → UPDATED -------------------
    field_changes = detect_field_changes(
        doc,
        old_doc,
        extra_ignore={"status", "location", "specification", "assigned_date"},
    )
    # Filter to only fields that are considered meaningful
    tracked = [c for c in field_changes if _label_in_tracked(c["field_name"])]
    if tracked:
        create_asset_history(
            asset=doc.name,
            action_type="UPDATED",
            reference_doctype="BYT Asset",
            reference_docname=doc.name,
            changes=tracked,
        )

def _label_in_tracked(label):
    """Return True if *label* is among the meaningful tracked field labels."""
    return label in _UPDATED_TRACK_LABELS
