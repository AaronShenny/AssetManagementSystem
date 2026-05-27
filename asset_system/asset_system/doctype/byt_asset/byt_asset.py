import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

# Status transition rules
ALLOWED_TRANSITIONS = {
    "Available": ["Assigned", "Maintenance", "Deregistered"],
    "Assigned": ["Available", "Maintenance", "Deregistered"],
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
        self.create_user_permission()
        _record_new_registration(self)

    def on_update(self):
        self.create_user_permission()
        _record_asset_update(self)
    
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
            self.status = "Assigned"
        if not self.assigned_to and self.status == "Assigned":
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
def has_permission(doc, user=None, permission_type=None):
    from asset_system.asset_system.doctype.asset_assignment.helpers import get_active_assignment

    user = user or frappe.session.user

    # Allow System Manager
    if "System Manager" in frappe.get_roles(user):
        return True

    # Allow Asset Manager
    if "Asset Manager" in frappe.get_roles(user):
        return True

    # Allow assigned Asset Employee
    if "Asset Employee" in frappe.get_roles(user):
        active_assignment = get_active_assignment(doc.name)
        return bool(active_assignment and active_assignment.get("assigned_to") == user)

def get_permission_query_conditions(user):

    if not user:
        user = frappe.session.user

    if "System Manager" in frappe.get_roles(user):
        return ""

    if "Infra Admin" in frappe.get_roles(user):
        return ""

    if "Asset Employee" in frappe.get_roles(user):
        escaped_user = frappe.db.escape(user)
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
      4. assigned_to changed           → ALLOCATED / DEALLOCATED / TRANSFERRED
      5. location changed              → MOVED
      6. specification table changed   → SPECIFICATION UPDATED
      7. Other meaningful fields       → UPDATED
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
                action_type="DEREGISTERED",
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

    # --- 4: Assignment changes -----------------------------------------
    old_assigned = old_doc.get("assigned_to") or ""
    new_assigned = doc.assigned_to or ""

    if old_assigned != new_assigned:
        if not old_assigned and new_assigned:
            # Find the latest Asset Assignment as a reference if available
            ref_name = _latest_assignment(doc.name, new_assigned)
            create_asset_history(
                asset=doc.name,
                action_type="ALLOCATED",
                reference_doctype="Asset Assignment" if ref_name else "BYT Asset",
                reference_docname=ref_name or doc.name,
                changes=[
                    {
                        "field_name": "Assigned To",
                        "old_data": "",
                        "new_data": new_assigned,
                    }
                ],
            )
        elif old_assigned and not new_assigned:
            create_asset_history(
                asset=doc.name,
                action_type="DEALLOCATED",
                reference_doctype="BYT Asset",
                reference_docname=doc.name,
                changes=[
                    {
                        "field_name": "Assigned To",
                        "old_data": old_assigned,
                        "new_data": "",
                    }
                ],
            )
        else:
            # Both exist but differ → ownership transferred directly
            create_asset_history(
                asset=doc.name,
                action_type="TRANSFERRED",
                reference_doctype="BYT Asset",
                reference_docname=doc.name,
                changes=[
                    {
                        "field_name": "Assigned To",
                        "old_data": old_assigned,
                        "new_data": new_assigned,
                    }
                ],
            )
        return

    # --- 5: Direct location change (not via Asset Movement doc) --------
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

    # --- 6: Specification child-table changes --------------------------
    spec_change= detect_child_table_changes(doc, old_doc, "specification")
    if spec_change:
        create_asset_history(
            asset=doc.name,
            action_type="SPECIFICATION UPDATED",
            reference_doctype="BYT Asset",
            reference_docname=doc.name,
            changes=spec_change,
        )
        return

    # --- 7: Other meaningful field changes → UPDATED -------------------
    field_changes = detect_field_changes(
        doc,
        old_doc,
        extra_ignore={"status", "assigned_to", "location", "specification", "assigned_date"},
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


def _latest_assignment(asset, assigned_to):
    """Return the most recent Asset Assignment name for the given asset/user pair."""
    try:
        return frappe.db.get_value(
            "Asset Assignment",
            {"asset": asset, "assigned_to": assigned_to},
            "name",
            order_by="creation desc",
        )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"Asset History: could not fetch latest assignment for asset={asset}",
        )
        return None


def _label_in_tracked(label):
    """Return True if *label* is among the meaningful tracked field labels."""
    return label in _UPDATED_TRACK_LABELS
