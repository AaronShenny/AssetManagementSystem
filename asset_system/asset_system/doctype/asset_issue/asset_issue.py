# Copyright (c) 2026, Aaron Shenny and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document

from asset_system.asset_system.doctype.asset_assignment.helpers import has_active_assignment
from asset_system.utils.asset_history_service import create_asset_history


# These values must stay in sync with Asset Issue.status options in asset_issue.json.
ACTIVE_ISSUE_STATES = frozenset(
    {
        "Assigned",
        "In Progress",
        "Waiting for IT",
        "Waiting for Vendor",
    }
)
RESTORE_STATES = frozenset({"Resolved", "Closed"})
ALLOWED_REPORTER_ROLES = frozenset({"Employee", "System Manager", "Infra Executive"})


class AssetIssue(Document):
    def before_insert(self):
        self._validate_reporter_role()
        self.reported_by = self.owner
        self.reported_date = self.creation

        

    def after_insert(self):
        self._record_issue_raised()
        self._apply_issue_state()
        
    def on_update(self):
        self._record_issue_status_change()
        self._apply_issue_state()

    def _validate_reporter_role(self):
        user_roles = set(frappe.get_roles(frappe.session.user))
        if not ALLOWED_REPORTER_ROLES.intersection(user_roles):
            frappe.throw(_("Only Employee, System Manager, or Infra Executive can raise Asset Issues."))

    def _apply_issue_state(self):
        if not self.asset:
            return

        asset_status = frappe.db.get_value("BYT Asset", self.asset, "status")
        if self.status in ACTIVE_ISSUE_STATES and asset_status != "Deregistered":
            self._move_asset_to_maintenance(asset_status)
            return

        if self.status in RESTORE_STATES:
            self._restore_asset_status(asset_status)

    def _move_asset_to_maintenance(self, current_asset_status):
        if current_asset_status != "Maintenance":
            frappe.db.set_value("BYT Asset", self.asset, "status", "Maintenance", update_modified=True)
            create_asset_history(
                asset=self.asset,
                action_type="UNDER MAINTENANCE",
                reference_doctype="Asset Issue",
                reference_docname=self.name,
                remarks=f"Issue {self.name} moved to {self.status}.",
                changes=[
                    {"field_name": "Status", "old_data": current_asset_status or "", "new_data": "Maintenance"}
                ],
            )

    def _restore_asset_status(self, current_asset_status):
        self._record_issue_resolved()
        if current_asset_status == "Deregistered":
            return

        if self._has_other_active_issues():
            return

        target_status = "Assigned" if has_active_assignment(self.asset) else "Available"
        if current_asset_status == target_status:
            return

        frappe.db.set_value("BYT Asset", self.asset, "status", target_status, update_modified=True)
        create_asset_history(
            asset=self.asset,
            action_type="RESTORED",
            reference_doctype="Asset Issue",
            reference_docname=self.name,
            remarks=f"Asset restored after issue {self.name} moved to {self.status}.",
            changes=[
                {"field_name": "Status", "old_data": current_asset_status or "", "new_data": target_status}
            ],
        )

    def _has_other_active_issues(self):
        return bool(
            frappe.db.exists(
                "Asset Issue",
                {
                    "asset": self.asset,
                    "name": ["!=", self.name],
                    "status": ["in", list(ACTIVE_ISSUE_STATES)],
                },
            )
        )

    def _record_issue_raised(self):
        create_asset_history(
            asset=self.asset,
            action_type="ISSUE RAISED",
            reference_doctype="Asset Issue",
            reference_docname=self.name,
            remarks=f"Issue raised by {self.reported_by}.",
        )

    def _record_issue_resolved(self):
        old_status, new_status = self._get_status_change()
        if old_status is None:
            return
        if old_status in RESTORE_STATES:
            return

        create_asset_history(
            asset=self.asset,
            action_type="ISSUE RESOLVED",
            reference_doctype="Asset Issue",
            reference_docname=self.name,
            remarks=f"Issue moved to {new_status}.",
            changes=[{"field_name": "Issue Status", "old_data": old_status or "", "new_data": new_status or ""}],
        )

    def _record_issue_status_change(self):
        old_status, new_status = self._get_status_change()
        if old_status is None or new_status in RESTORE_STATES:
            return

        create_asset_history(
            asset=self.asset,
            action_type="UPDATED",
            reference_doctype="Asset Issue",
            reference_docname=self.name,
            remarks=f"Issue status changed to {new_status}.",
            changes=[{"field_name": "Issue Status", "old_data": old_status or "", "new_data": new_status or ""}],
        )

    def _get_status_change(self):
        if self.is_new():
            return None, None

        old_doc = self.get_doc_before_save()
        old_status = old_doc.get("status") if old_doc else None
        new_status = self.status
        if old_status == new_status:
            return None, None

        return old_status, new_status


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
            f"where aa.asset = `tabAsset Issue`.asset and aa.assigned_to = {escaped_user} and aa.is_active = 1)"
        )
