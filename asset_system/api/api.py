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
from frappe.query_builder import DocType
from pypika import Order

# ---------------------------------------------------------------------------#
# Helpers                                                                    #
# ---------------------------------------------------------------------------#


def _get_asset_or_throw(asset_name: str):
    """Fetch and return an Asset document, raising 404-style error if absent."""
    doc = frappe.get_doc("BYT Asset", asset_name)
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
            "doctype": "BYT Asset",
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

    total = frappe.db.count("BYT Asset", filters=filters)
    assets = frappe.get_all(
        "BYT Asset",
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
    """Return full lifecycle history of an asset."""

    if not asset:
        frappe.throw(_("Asset is required."))

    _get_asset_or_throw(asset)

    history = []

    # GET ALL ASSIGNMENTS
    assignments = frappe.get_all(
        "Asset Assignment",
        filters={
            "asset": asset
        },
        fields=[
            "name",
            "asset",
            "assigned_to",
            "assigned_date",
            "remarks",
            "docstatus",
            "creation",
        ],
        order_by="creation asc",
    )

    for assignment in assignments:

        # FIND RETURN FOR THIS ASSIGNMENT
        return_doc = frappe.db.get_value(
            "Asset Return",
            {
                "asset_assignment": assignment.name
            },
            [
                "name",
                "returned_date",
                "return_reason",
                "remarks",
                "docstatus",
                "creation",
            ],
            as_dict=True
        )

        history.append({
            "assignment": {
                "id": assignment.name,
                "employee": assignment.assigned_to,
                "assigned_date": assignment.assigned_date,
                "remarks": assignment.remarks,
                "docstatus": assignment.docstatus,
                "creation": assignment.creation,
            },

            "return": {
                "id": return_doc.name,
                "returned_date": return_doc.returned_date,
                "reason": return_doc.return_reason,
                "remarks": return_doc.remarks,
                "docstatus": return_doc.docstatus,
                "creation": return_doc.creation,
            } if return_doc else None
        })

    return {
        "asset": asset,
        "history": history,
    }

"""
assignments = frappe.get_all(
    "Asset Assignment",
    filters={
        "asset": asset,
        "return_date": ["is", "not set"]
    },
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
"""
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
    frappe.db.set_value("BYT Asset", doc.asset, {
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
    total = frappe.db.count("BYT Asset")
    available = frappe.db.count("BYT Asset", {"status": "Available"})
    in_use = frappe.db.count("BYT Asset", {"status": "In Use"})
    maintenance = frappe.db.count("BYT Asset", {"status": "Maintenance"})
    scrapped = frappe.db.count("BYT Asset", {"status": "Scrapped"})

    return {
        "total": total,
        "available": available,
        "in_use": in_use,
        "maintenance": maintenance,
        "scrapped": scrapped,
    }


@frappe.whitelist()
def can_create_asset():
    return frappe.has_permission("BYT Asset", "create")

import frappe
from frappe import _

def can_create_assignment():
    return frappe.has_permission("Asset Assignment","create")

@frappe.whitelist()
def get_Assetss(
    category=None,
    status=None,
    min_price=None,
    max_price=None,
    location=None,
    assigned_to=None,
    page=1,
    page_length=20
):
    # ----------------------------- #
    # 1. Permission check
    # ----------------------------- #
    if not frappe.has_permission("BYT Asset", "read"):
        frappe.throw(_("Not allowed"), frappe.PermissionError)

    # ----------------------------- #
    # 2. Build filters
    # ----------------------------- #
    filters = []

    if category:
        filters.append(["category", "=", category])

    if status:
        filters.append(["status", "=", status])

    if location:
        filters.append(["location", "=", location])

    if assigned_to:
        filters.append(["assigned_to", "=", assigned_to])

    if min_price and max_price:
        filters.append(["purchase_value", "between", [float(min_price), float(max_price)]])

    # ----------------------------- #
    # 3. Optional user restriction
    # ----------------------------- #
    if frappe.session.user != "Administrator":
        # Example: only show assets assigned to current user
        # remove this if not needed
        pass
        # filters.append(["assigned_to", "=", frappe.session.user])

    # ----------------------------- #
    # 4. Pagination setup
    # ----------------------------- #
    page = int(page)
    page_length = int(page_length)
    start = (page - 1) * page_length

    # ----------------------------- #
    # 5. Query database
    # ----------------------------- #
    assets = frappe.get_all(
        "BYT Asset",
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
            "serial_number"
        ],
        limit_start=start,
        limit_page_length=page_length,
        order_by="creation desc"
    )

    total = frappe.db.count("BYT Asset", filters=filters)

    # ----------------------------- #
    # 6. Return response
    # ----------------------------- #
    return {
        "total": total,
        "page": page,
        "page_length": page_length,
        "assets": assets
    }

@frappe.whitelist()
def who_am_i():
    return {
        "user": frappe.session.user
    }



@frappe.whitelist()
def get_user_roles():
    user = frappe.session.user

    roles = frappe.get_roles(user)
    print(roles)
    if user == 'Administrator':
        roles = ['Admin']
    return {
        "user": user,
        "roles": roles
    }



@frappe.whitelist()
def get_asset_details(asset):
    """
    Return all readable fields of an Asset
    for the currently logged-in user.
    """

    doctype = "BYT Asset"

    # Check permission
    if not frappe.has_permission(doctype, "read", doc=asset):
        frappe.throw("Not permitted", frappe.PermissionError)

    # Get document
    doc = frappe.get_doc(doctype, asset)
    print(doc)
    meta = frappe.get_meta(doctype)

    fields_data = []

    # Add default fields you may want
    #default_fields = [
    #    "name",
    #    "owner",
    #    "creation",
    #    "modified",
    #    "modified_by",
    #    "docstatus",
    #]

    for field in meta.fields:

        # Skip hidden fields
        if field.hidden:
            continue

        value = doc.get(field.fieldname)

        fields_data.append({
            "fieldname": field.fieldname,
            "label": field.label,
            "fieldtype": field.fieldtype,
            "value": value,
            "options": field.options,
            "reqd": field.reqd,
            "read_only": field.read_only,
        })

    # Add default fields manually
    #for fieldname in default_fields:
    #    fields_data.append({
    #        "fieldname": fieldname,
    #        "label": fieldname.replace("_", " ").title(),
    #        "fieldtype": "Data",
    #        "value": doc.get(fieldname),
    #        "options": None,
    #        "reqd": 0,
    #        "read_only": 1,
    #    })
    print(fields_data)
    return {
        "doctype": doctype,
        "asset": asset,
        "fields": fields_data
    }

@frappe.whitelist()
def get_doctype_meta(doctype: str):
    if not doctype:
        frappe.throw(_('doctype is required'))

    meta = frappe.get_meta(doctype)

    fields = []
    for field in meta.fields:
        fields.append(
            {
                "fieldname": field.fieldname,
                "label": field.label,
                "fieldtype": field.fieldtype,
                "hidden": field.hidden,
                "read_only": field.read_only,
                "reqd": field.reqd,
                "options": field.options,
                "in_list_view": field.in_list_view,
                "default": field.default,
            }
        )

    return {"fields": fields}

@frappe.whitelist()
def search_link_options(doctype, txt=""):
    if doctype == "BYT Asset":
        return frappe.get_all(
            doctype,
            filters={
                "name": ["like", f"%{txt}%"],
                "status" : ["!=","Deregistered"]
            },
            fields=["name"],
            limit=20
        )
    else:
        return frappe.get_all(
            doctype,
            filters={
                "name": ["like", f"%{txt}%"]
               
            },
            fields=["name"],
            limit=20
        )
ALLOWED_FILTER_OPERATORS = {"=", "!=", "<", ">", "<=", ">=", "like", "in", "between"}


def _parse_json(value, fallback):
    if value is None:
        return fallback
    if isinstance(value, (list, dict)):
        return value
    try:
        return frappe.parse_json(value)
    except Exception:
        return fallback


def _normalize_in_values(value):
    if isinstance(value, (list, tuple)):
        return [v for v in value if str(v).strip() != ""]
    if value is None:
        return []
    return [v.strip() for v in str(value).split(",") if v.strip()]


def _build_condition(field_sql: str, operator: str, value) -> Tuple[str, List]:
    operator = (operator or "").lower().strip()
    if operator not in ALLOWED_FILTER_OPERATORS:
        return "", []
    if operator == "between":
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            return "", []
        return f"{field_sql} BETWEEN %s AND %s", [value[0], value[1]]
    if operator == "in":
        values = _normalize_in_values(value)
        if not values:
            return "", []
        return f"{field_sql} IN ({', '.join(['%s'] * len(values))})", list(values)
    if operator == "like":
        return f"{field_sql} LIKE %s", [f"%{value}%"]
    return f"{field_sql} {operator} %s", [value]


@frappe.whitelist()
def get_doctype_meta(doctype: str):
    if not doctype:
        frappe.throw(_("doctype is required"))
    meta = frappe.get_meta(doctype)
    return {
        "fields": [
            {
                "fieldname": f.fieldname,
                "label": f.label,
                "fieldtype": f.fieldtype,
                "hidden": f.hidden,
                "read_only": f.read_only,
                "reqd": f.reqd,
                "options": f.options,
                "in_list_view": f.in_list_view,
                "default": f.default,
            }
            for f in meta.fields
        ]
    }


@frappe.whitelist()
def get_unified_filter_catalog(doctype: str = "BYT Asset"):
    """Single business-facing filter catalog with hidden relational semantics."""
    meta = frappe.get_meta(doctype)
    parent_catalog = []
    for field in meta.fields:
        if field.hidden or not field.fieldname or field.fieldtype in {"Table", "Section Break", "Column Break", "Tab Break", "HTML", "Button", "Fold", "Table MultiSelect"}:
            continue
        parent_catalog.append({
            "key": f"parent:{field.fieldname}",
            "label": field.label or field.fieldname.replace("_", " ").title(),
            "type": "parent",
            "fieldtype": field.fieldtype,
            "options": field.options,
            "source": {"fieldname": field.fieldname},
        })

    virtual_catalog = []
    for field in meta.fields:
        if field.fieldtype != "Table" or not field.options:
            continue
        child_meta = frappe.get_meta(field.options)
        child_fields = {f.fieldname: f for f in child_meta.fields if f.fieldname}
        if "spec" not in child_fields or "value" not in child_fields:
            continue
        child_table = DocType(field.options)
        specs = (
            frappe.qb.from_(child_table)
            .select(child_table.spec)
            .distinct()
            .where(
                (child_table.spec.isnotnull()) &
                (child_table.spec != "")
            )
            .orderby(child_table.spec, order=Order.asc)
        ).run(pluck=True)
        for spec in specs:
            virtual_catalog.append({
                "key": f"virtual_spec:{field.fieldname}:{spec}",
                "label": spec,
                "type": "virtual_specification",
                "fieldtype": child_fields["value"].fieldtype or "Data",
                "source": {
                    "tableField": field.fieldname,
                    "childDoctype": field.options,
                    "keyField": "spec",
                    "keyValue": spec,
                    "valueField": "value",
                },
            })

    return {"catalog": parent_catalog + virtual_catalog}

from typing import Dict, List, Tuple


ALLOWED_FILTER_OPERATORS = {"=", "!=", "<", ">", "<=", ">=", "like", "in", "between"}


def _parse_json(value, fallback):
    if value is None:
        return fallback
    if isinstance(value, (list, dict)):
        return value
    try:
        return frappe.parse_json(value)
    except Exception:
        return fallback


def _normalize_in_values(value):
    if isinstance(value, (list, tuple)):
        return [v for v in value if str(v).strip() != ""]
    if value is None:
        return []
    return [v.strip() for v in str(value).split(",") if v.strip()]


def _build_condition(field_sql: str, operator: str, value) -> Tuple[str, List]:
    if not operator:
        return "", []
    operator = operator.lower().strip()
    if operator not in ALLOWED_FILTER_OPERATORS:
        return "", []

    if operator == "between":
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            return "", []
        return f"{field_sql} BETWEEN %s AND %s", [value[0], value[1]]

    if operator == "in":
        values = _normalize_in_values(value)
        if not values:
            return "", []
        placeholders = ", ".join(["%s"] * len(values))
        return f"{field_sql} IN ({placeholders})", list(values)

    if operator == "like":
        return f"{field_sql} LIKE %s", [f"%{value}%"]

    return f"{field_sql} {operator} %s", [value]


def _sanitize_order_by(order_by: str, meta) -> str:
    if not order_by:
        return "`parent`.`modified` desc"

    parts = [p for p in str(order_by).split(" ") if p]
    fieldname = parts[0]
    direction = parts[1].lower() if len(parts) > 1 else "asc"
    direction = direction if direction in ("asc", "desc") else "asc"

    if fieldname not in {"name", "modified"} and not meta.has_field(fieldname):
        return "`parent`.`modified` desc"

    return f"`parent`.`{fieldname}` {direction}"


def _build_parent_conditions(meta, parent_filters: List) -> Tuple[List[str], List]:
    conditions = []
    params = []

    for row in parent_filters or []:
        if not isinstance(row, (list, tuple)) or len(row) < 3:
            continue

        fieldname, operator, value = row[0], row[1], row[2]
        if fieldname not in {"name", "modified"} and not meta.has_field(fieldname):
            continue

        condition, condition_params = _build_condition(f"`parent`.`{fieldname}`", operator, value)
        if not condition:
            continue

        conditions.append(condition)
        params.extend(condition_params)

    return conditions, params


def _normalize_child_filter_groups(filters_for_table) -> List[List[Dict]]:
    groups = []
    if not isinstance(filters_for_table, (list, tuple)):
        return groups

    for entry in filters_for_table:
        if not isinstance(entry, dict):
            continue
        if isinstance(entry.get("conditions"), (list, tuple)):
            conditions = entry.get("conditions")
        elif "child_field" in entry or "field" in entry:
            conditions = [entry]
        else:
            continue
        groups.append(conditions)

    return groups


def _build_child_group_exists(
    doctype: str, table_field, group_conditions: List[Dict], valid_child_fields: set
) -> Tuple[str, List]:
    conditions = []
    params = []

    for condition in group_conditions or []:
        if not isinstance(condition, dict):
            continue
        child_field = condition.get("field") or condition.get("child_field")
        operator = condition.get("operator")
        value = condition.get("value")
        if child_field not in valid_child_fields:
            continue

        sql_fragment, condition_params = _build_condition(
            f"`child`.`{child_field}`", operator, value
        )
        if not sql_fragment:
            continue

        conditions.append(sql_fragment)
        params.extend(condition_params)

    if not conditions:
        return "", []

    where_conditions = " AND ".join([f"({condition})" for condition in conditions])
    sql = f"""
        EXISTS (
            SELECT 1
            FROM `tab{table_field.options}` `child`
            WHERE `child`.`parenttype` = %s
              AND `child`.`parentfield` = %s
              AND `child`.`parent` = `parent`.`name`
              AND {where_conditions}
        )
    """.strip()

    return sql, [doctype, table_field.fieldname] + params


@frappe.whitelist()
def get_filtered_doctype_list(
    doctype: str,
    parent_filters=None,
    child_table_filters=None,
    fields=None,
    limit_start=0,
    limit_page_length=100,
    order_by=None,
):
    if not doctype:
        frappe.throw(_("doctype is required"))

    meta = frappe.get_meta(doctype)
    parent_filters = _parse_json(parent_filters, [])
    child_table_filters = _parse_json(child_table_filters, {})
    fields = _parse_json(fields, ["name"])

    if not isinstance(parent_filters, (list, tuple)):
        parent_filters = []

    if not isinstance(child_table_filters, dict):
        child_table_filters = {}

    if not isinstance(fields, (list, tuple)):
        fields = ["name"]

    safe_fields = []
    for field in fields:
        if field in {"name", "modified"} or meta.has_field(field):
            safe_fields.append(field)

    if not safe_fields:
        safe_fields = ["name"]

    parent_conditions, parent_params = _build_parent_conditions(meta, parent_filters)

    child_conditions = []
    child_params = []
    for field in meta.fields:
        if field.fieldtype != "Table" or not field.options:
            continue
        filters_for_table = child_table_filters.get(field.fieldname)
        if not filters_for_table:
            continue

        groups = _normalize_child_filter_groups(filters_for_table)
        if not groups:
            continue

        child_meta = frappe.get_meta(field.options)
        valid_child_fields = {f.fieldname for f in child_meta.fields if f.fieldname}
        for group_conditions in groups:
            exists_sql, exists_params = _build_child_group_exists(
                doctype, field, group_conditions, valid_child_fields
            )
            if not exists_sql:
                continue
            child_conditions.append(exists_sql)
            child_params.extend(exists_params)

    where_clauses = []
    if parent_conditions:
        where_clauses.append(" AND ".join(parent_conditions))

    if child_conditions:
        where_clauses.extend(child_conditions)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    order_by_sql = _sanitize_order_by(order_by, meta)

    fields_sql = ", ".join([f"`parent`.`{field}`" for field in safe_fields])
    sql = f"""
        SELECT {fields_sql}
        FROM `tab{doctype}` `parent`
        WHERE {where_sql}
        ORDER BY {order_by_sql}
        LIMIT %s OFFSET %s
    """.strip()

    params = parent_params + child_params + [int(limit_page_length), int(limit_start)]
    results = frappe.db.sql(sql, params, as_dict=True)
    return {"data": results}
