import frappe


ACTIVE_ASSIGNMENT_STATUSES = frozenset({"Assigned"})


def is_assignment_active_status(status):
    return status in ACTIVE_ASSIGNMENT_STATUSES


def get_active_assignment(asset):
    if not asset:
        return None

    return frappe.db.get_value(
        "Asset Assignment",
        {"asset": asset, "is_active": 1},
        ["name", "assigned_to", "status"],
        as_dict=True,
        order_by="creation desc",
    )


def has_active_assignment(asset):
    return bool(get_active_assignment(asset))
