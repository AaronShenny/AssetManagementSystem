"""
asset_system.api.asset_api
~~~~~~~~~~~~~~~~~~~~~~~~~~
Whitelisted API methods for the Asset Management System.

All methods return clean JSON-serialisable dicts and raise frappe.ValidationError
(or frappe.PermissionError) on input problems so the standard Frappe JSON
error wrapper passes them back to the caller.
"""
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import today


# ---------------------------------------------------------------------------#
# Helpers                                                                    #
# ---------------------------------------------------------------------------#


def _get_asset_or_throw(asset_name: str):
    """Fetch and return an Asset document, raising 404-style error if absent."""
    doc = frappe.get_doc("Asset", asset_name)
    if not doc:
        frappe.throw(_("Asset '{0}' not found.").format(asset_name), frappe.DoesNotExistError)
    return doc


# ---------------------------------------------------------------------------#
# Public whitelisted methods                                                 #
# ---------------------------------------------------------------------------#


@frappe.whitelist()
def create_asset(
    asset_name: str,
    category: str,
    purchase_date: str = None,
    purchase_value: float = None,
    location: str = None,
    serial_number: str = None,
    description: str = None,
) -> dict:
    """Create a new Asset document.

    Returns:
        dict: ``{"asset_id": "AST-0001", "name": "AST-0001", "status": "Available"}``
    """
    if not asset_name:
        frappe.throw(_("asset_name is required."))
    if not category:
        frappe.throw(_("category is required."))

    doc = frappe.get_doc(
        {
            "doctype": "Asset",
            "asset_name": asset_name,
            "category": category,
            "purchase_date": purchase_date,
            "purchase_value": purchase_value,
            "location": location,
            "serial_number": serial_number,
            "description": description,
            "status": "Available",
        }
    )
    doc.insert(ignore_permissions=False)
    frappe.db.commit()

    return {
        "asset_id": doc.name,
        "name": doc.name,
        "asset_name": doc.asset_name,
        "status": doc.status,
        "category": doc.category,
        "location": doc.location,
    }


@frappe.whitelist()
def get_assets(
    status: str = None,
    category: str = None,
    location: str = None,
    assigned_to: str = None,
    page_length: int = 20,
    page: int = 1,
) -> dict:
    """Return a paginated list of Assets with optional filters.

    Returns:
        dict: ``{"total": N, "assets": [...]}``
    """
    filters = {}
    if status:
        filters["status"] = status
    if category:
        filters["category"] = category
    if location:
        filters["location"] = location
    if assigned_to:
        filters["assigned_to"] = assigned_to

    total = frappe.db.count("Asset", filters=filters)
    assets = frappe.get_all(
        "Asset",
        filters=filters,
        fields=[
            "name",
            "asset_name",
            "category",
            "status",
            "location",
            "assigned_to",
            "purchase_date",
            "purchase_value",
            "serial_number",
        ],
        limit_page_length=int(page_length),
        limit_start=(int(page) - 1) * int(page_length),
        order_by="creation desc",
    )

    return {"total": total, "page": int(page), "page_length": int(page_length), "assets": assets}


@frappe.whitelist()
def move_asset(
    asset: str,
    to_location: str,
    movement_date: str = None,
    remarks: str = None,
) -> dict:
    """Move an asset to a new location (creates + submits an Asset Movement).

    Returns:
        dict: ``{"movement": "ASTMV-0001", "asset": "AST-0001", "to_location": "..."}``
    """
    if not asset:
        frappe.throw(_("asset is required."))
    if not to_location:
        frappe.throw(_("to_location is required."))

    asset_doc = _get_asset_or_throw(asset)

    if asset_doc.status == "Scrapped":
        frappe.throw(_("Asset {0} is Scrapped and cannot be moved.").format(asset))

    movement = frappe.get_doc(
        {
            "doctype": "Asset Movement",
            "asset": asset,
            "from_location": asset_doc.location,
            "to_location": to_location,
            "movement_date": movement_date or today(),
            "moved_by": frappe.session.user,
            "remarks": remarks,
        }
    )
    movement.insert(ignore_permissions=False)
    movement.submit()
    frappe.db.commit()

    return {
        "movement": movement.name,
        "asset": asset,
        "from_location": movement.from_location,
        "to_location": to_location,
        "movement_date": movement.movement_date,
    }


@frappe.whitelist()
def assign_asset(
    asset: str,
    assigned_to: str,
    assigned_date: str = None,
    return_date: str = None,
    remarks: str = None,
) -> dict:
    """Assign an asset to a user (creates + submits an Asset Assignment).

    Returns:
        dict: ``{"assignment": "ASTAS-0001", "asset": "AST-0001", "assigned_to": "user@example.com"}``
    """
    if not asset:
        frappe.throw(_("asset is required."))
    if not assigned_to:
        frappe.throw(_("assigned_to is required."))

    asset_doc = _get_asset_or_throw(asset)

    if asset_doc.status == "Scrapped":
        frappe.throw(_("Asset {0} is Scrapped and cannot be assigned.").format(asset))

    assignment = frappe.get_doc(
        {
            "doctype": "Asset Assignment",
            "asset": asset,
            "assigned_to": assigned_to,
            "assigned_date": assigned_date or today(),
            "return_date": return_date,
            "remarks": remarks,
        }
    )
    assignment.insert(ignore_permissions=False)
    assignment.submit()
    frappe.db.commit()

    return {
        "assignment": assignment.name,
        "asset": asset,
        "assigned_to": assigned_to,
        "assigned_date": assignment.assigned_date,
    }


@frappe.whitelist()
def get_asset_history(asset: str) -> dict:
    """Return full movement and assignment history for an asset.

    Returns:
        dict: ``{"asset": "AST-0001", "movements": [...], "assignments": [...]}``
    """
    if not asset:
        frappe.throw(_("asset is required."))

    _get_asset_or_throw(asset)  # validate existence

    movements = frappe.get_all(
        "Asset Movement",
        filters={"asset": asset},
        fields=[
            "name",
            "from_location",
            "to_location",
            "movement_date",
            "moved_by",
            "remarks",
            "docstatus",
        ],
        order_by="movement_date desc",
    )

    assignments = frappe.get_all(
        "Asset Assignment",
        filters={"asset": asset},
        fields=[
            "name",
            "assigned_to",
            "assigned_date",
            "return_date",
            "remarks",
            "docstatus",
        ],
        order_by="assigned_date desc",
    )

    return {
        "asset": asset,
        "movements": movements,
        "assignments": assignments,
    }


@frappe.whitelist()
def return_asset(assignment_name: str, return_date: str = None) -> dict:
    """Record the return date on a submitted Asset Assignment.

    Returns:
        dict: ``{"assignment": "ASTAS-0001", "return_date": "2024-06-01"}``
    """
    if not assignment_name:
        frappe.throw(_("assignment_name is required."))

    doc = frappe.get_doc("Asset Assignment", assignment_name)
    if doc.docstatus != 1:
        frappe.throw(_("Only submitted assignments can be returned."))

    doc.return_date = return_date or today()
    doc.save(ignore_permissions=False)

    # Clear assignment on the Asset
    frappe.db.set_value("Asset", doc.asset, {
        "assigned_to": None,
        "status": "Available",
    })
    frappe.db.commit()

    return {
        "assignment": doc.name,
        "asset": doc.asset,
        "return_date": doc.return_date,
    }


@frappe.whitelist()
def get_dashboard_stats() -> dict:
    """Return summary statistics for the Asset dashboard.

    Returns:
        dict with total, available, in_use, maintenance, scrapped counts.
    """
    total = frappe.db.count("Asset")
    available = frappe.db.count("Asset", {"status": "Available"})
    in_use = frappe.db.count("Asset", {"status": "In Use"})
    maintenance = frappe.db.count("Asset", {"status": "Maintenance"})
    scrapped = frappe.db.count("Asset", {"status": "Scrapped"})

    return {
        "total": total,
        "available": available,
        "in_use": in_use,
        "maintenance": maintenance,
        "scrapped": scrapped,
    }
