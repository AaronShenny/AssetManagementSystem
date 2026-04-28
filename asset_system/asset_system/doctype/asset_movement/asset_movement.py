import frappe
from frappe import _
from frappe.model.document import Document


class AssetMovement(Document):
    def validate(self):
        self._validate_not_scrapped()
        self._validate_locations()
        self._set_moved_by()

    def on_submit(self):
        self._update_asset_location()

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _validate_not_scrapped(self):
        status = frappe.db.get_value("BYT Asset", self.asset, "status")
        if status == "Scrapped":
            frappe.throw(
                _("Asset {0} is Scrapped and cannot be moved.").format(self.asset)
            )

    def _validate_locations(self):
        if self.from_location and self.from_location == self.to_location:
            frappe.throw(_("'From Location' and 'To Location' cannot be the same."))

    def _set_moved_by(self):
        if not self.moved_by:
            self.moved_by = frappe.session.user

    def _update_asset_location(self):
        """On submit, update the current location on the linked Asset."""
        frappe.db.set_value("BYT Asset", self.asset, "location", self.to_location)
        frappe.db.set_value("BYT Asset", self.asset, "modified", frappe.utils.now())


# ------------------------------------------------------------------ #
# Module-level hooks wired via hooks.py                               #
# ------------------------------------------------------------------ #


def validate(doc, method=None):
    doc.validate()


def on_submit(doc, method=None):
    doc.on_submit()
