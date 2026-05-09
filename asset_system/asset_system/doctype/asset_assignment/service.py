import frappe
from frappe import _

from .repository import AssetRepository
from .rules import validate_dates


class AssetAssignmentService:

    @staticmethod
    def validate(doc):

        validate_dates(
            doc.assigned_date,
            doc.return_date
        )

        AssetAssignmentService.validate_asset_available(
            doc.asset
        )

    @staticmethod
    def validate_asset_available(asset):

        status = AssetRepository.get_status(asset)

        if status == "Scrapped":
            frappe.throw(
                _("Asset {0} is Scrapped and cannot be assigned.")
                .format(asset)
            )

    @staticmethod
    def assign(doc):

        AssetRepository.assign_asset(
            doc.asset,
            doc.assigned_to
        )

        
    @staticmethod
    def unassign(doc):

        AssetRepository.unassign_asset(doc.asset)

    
