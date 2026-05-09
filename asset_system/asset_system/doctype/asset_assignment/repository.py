import frappe


class AssetRepository:

    @staticmethod
    def get_status(asset):

        return frappe.db.get_value(
            "BYT Asset",
            asset,
            "status"
        )

    @staticmethod
    def assign_asset(asset, assigned_to):

        frappe.db.set_value(
            "BYT Asset",
            asset,
            {
                "assigned_to": assigned_to,
                "status": "In Use"
            }
        )

    @staticmethod
    def unassign_asset(asset):

        frappe.db.set_value(
            "BYT Asset",
            asset,
            {
                "assigned_to": None,
                "status": "Available"
            }
        )



