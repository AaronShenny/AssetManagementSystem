# Copyright (c) 2026, Aaron Shenny and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Damages(Document):
    def after_insert(self):
        self._record_marked_damaged()

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _record_marked_damaged(self):
        """Record MARKED DAMAGED history when a Damages report is created."""
        from asset_system.utils.asset_history_service import create_asset_history

        asset = self.asset_id  # Damages uses asset_id as the Link field name
        if not asset:
            return

        changes = []
        if self.physical_condition:
            changes.append(
                {
                    "field_name": "Physical Condition",
                    "old_data": "",
                    "new_data": self.physical_condition,
                }
            )
        if self.working_condition:
            changes.append(
                {
                    "field_name": "Working Condition",
                    "old_data": "",
                    "new_data": self.working_condition,
                }
            )

        create_asset_history(
            asset=asset,
            action_type="MARKED DAMAGED",
            reference_doctype="Damages",
            reference_docname=self.name,
            remarks=(
                f"Physical: {self.physical_condition or 'N/A'}. "
                f"Working: {self.working_condition or 'N/A'}."
            ),
            changes=changes,
        )
