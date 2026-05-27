"""asset_system.utils.asset_history_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Centralized, production-grade service for recording Asset History audit trail
entries across the entire Asset Management System.

Public API
----------
create_asset_history(asset, action_type, ...)
    Create and immediately submit a single Asset History record.

detect_field_changes(doc, old_doc, extra_ignore=None)
    Return a list of changed-field dicts for simple (non-table) fields.

detect_child_table_changes(doc, old_doc, table_fieldname)
    Return (old_summary, new_summary) strings for a child table; both empty
    if the table has not changed.

Usage example::

    from asset_system.utils.asset_history_service import (
        create_asset_history,
        detect_field_changes,
    )

    create_asset_history(
        asset="BYT.SFO.LAP.00001",
        action_type="NEW REGISTRATION",
        reference_doctype="BYT Asset",
        reference_docname="BYT.SFO.LAP.00001",
    )
"""
from __future__ import unicode_literals

import frappe
from frappe.utils import now_datetime

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Framework / system fields that are always excluded from change tracking
_IGNORED_FIELDS = frozenset(
    {
        "name",
        "owner",
        "creation",
        "docstatus",
        "idx",
        "parentfield",
        "_user_tags",
        "__last_sync_on",
        # BYT Asset derived / hidden fields
        "asset_id",
        "category_abbreviation",
        "location_abbreviation",
        # Binary / attachments
        # Structural UI fields
        "section_break_info",
        "section_break_purchase",
        "section_break_gosi",
        "section_break_qr",
        "column_break_info",
        "column_break_purchase",
    }
)

# Frappe field types that carry no data worth comparing
_IGNORED_FIELDTYPES = frozenset(
    {
        "Section Break",
        "Column Break",
        "Tab Break",
        "HTML",
        "Button",
        "Fold",
        "Heading",
        "Image",
    }
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_asset_history(
    asset,
    action_type,
    reference_doctype=None,
    reference_docname=None,
    remarks=None,
    changes=None,
    changed_by=None,
):
    """Create and immediately submit an Asset History record.

    Safe to call from any controller hook.  Handles recursion prevention,
    missing-asset safety, and install/migrate guard internally.

    :param asset:              BYT Asset name (link value).
    :param action_type:        One of the allowed Select option strings on the
                               Asset History "Action Type" (status) field.
    :param reference_doctype:  DocType that triggered this history entry.
    :param reference_docname:  Document name that triggered this entry.
    :param remarks:            Optional free-text note.
    :param changes:            List of dicts:
                               ``[{"field_name": ..., "old_data": ..., "new_data": ...}]``
    :param changed_by:         User responsible for the change (defaults to
                               the current session user).

    :returns: The new Asset History document name, or ``None`` on failure.
    """
    # ------------------------------------------------------------------
    # Recursion guard — prevents Asset History saves from triggering more
    # Asset History saves in the same request thread.
    # ------------------------------------------------------------------
    if getattr(frappe.local, "_creating_asset_history", False):
        return None

    # ------------------------------------------------------------------
    # Skip during bench install / migrate / test-setup scaffolding.
    # ------------------------------------------------------------------
    if frappe.flags.in_install or frappe.flags.in_migrate:
        return None

    # ------------------------------------------------------------------
    # Safety: asset reference must be non-empty and must exist in the DB.
    # ------------------------------------------------------------------
    if not asset:
        return None
    if not frappe.db.exists("BYT Asset", asset):
        return None

    frappe.local._creating_asset_history = True
    try:
        hist = frappe.get_doc(
            {
                "doctype": "Asset History",
                "asset": asset,
                # The fieldname on the DocType is "status"; its label is
                # "Action Type".  We always populate it with one of the
                # predefined action-type strings.
                "status": action_type,
                "changed_by": changed_by or frappe.session.user,
                "changed_on": now_datetime(),
                "reference_doctype": reference_doctype or "",
                "reference_docname": reference_docname or "",
                "remarks": remarks or "",
            }
        )

        for row in changes or []:
            hist.append(
                "changes",
                {
                    "field_name": str(row.get("field_name") or ""),
                    "old_data": _safe_str(row.get("old_data")),
                    "new_data": _safe_str(row.get("new_data")),
                },
            )

        hist.insert(ignore_permissions=True)
        hist.submit()

        return hist.name

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"Asset History creation failed — asset={asset}, action={action_type}",
        )
        return None

    finally:
        frappe.local._creating_asset_history = False


def detect_field_changes(doc, old_doc, extra_ignore=None):
    """Compare *doc* against *old_doc* and return changed simple-field dicts.

    Only simple (non-Table) fields are considered.  Framework noise fields
    defined in ``_IGNORED_FIELDS`` are always excluded.

    :param doc:          Current Frappe Document (post-save state).
    :param old_doc:      Previous document state (``frappe.Document`` or dict).
    :param extra_ignore: Additional fieldnames to exclude from comparison.

    :returns: ``[{"field_name": label_or_fieldname, "old_data": ..., "new_data": ...}]``
    """
    if not old_doc:
        return []

    ignore = _IGNORED_FIELDS | set(extra_ignore or [])
    changes = []

    for field in frappe.get_meta(doc.doctype).fields:
        fn = field.fieldname
        if fn in ignore:
            continue
        if field.fieldtype in _IGNORED_FIELDTYPES:
            continue
        # Child tables are handled separately via detect_child_table_changes
        if field.fieldtype == "Table":
            continue

        old_val = old_doc.get(fn) if hasattr(old_doc, "get") else None
        new_val = doc.get(fn)

        old_str = _safe_str(old_val)
        new_str = _safe_str(new_val)

        if old_str != new_str:
            changes.append(
                {
                    "field_name": field.label or fn,
                    "old_data": old_str,
                    "new_data": new_str,
                }
            )

    return changes


def detect_child_table_changes(doc, old_doc, table_fieldname):
    """Detect whether a child table changed between *old_doc* and *doc*.

    Returns a compact, human-readable summary of the old and new states.
    Both values are empty strings when there is no change.

    :param doc:              Current document.
    :param old_doc:          Previous document state.
    :param table_fieldname:  Fieldname of the Table field to inspect.

    :returns: ``(old_summary, new_summary)`` — both empty if unchanged.
    """


    if not old_doc:
        return []

    old_rows = old_doc.get(table_fieldname) or []
    new_rows = doc.get(table_fieldname) or []

    old_map = {
        row.get("spec"): row.get("value")
        for row in old_rows
    }

    new_map = {
        row.get("spec"): row.get("value")
        for row in new_rows
    }

    changes = []

    # Modified + removed
    for spec, old_value in old_map.items():

        new_value = new_map.get(spec)

        if old_value != new_value:

            changes.append({
                "field_name": spec,
                "old_data": old_value or "",
                "new_data": new_value or "",
            })

    # Newly added
    for spec, new_value in new_map.items():

        if spec not in old_map:

            changes.append({
                "field_name": spec,
                "old_data": "",
                "new_data": new_value or "",
            })

    return changes


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _safe_str(value):
    """Coerce *value* to a clean string suitable for comparison / storage."""
    if value is None:
        return ""
    return str(value)


def _summarise_child_table(rows):
    """Return clean human-readable summary of child-table rows."""

    if not rows:
        return ""

    parts = []

    for row in rows:

        spec = row.get("spec") or ""
        value = row.get("value") or ""

        if spec or value:
            parts.append(f"{spec}: {value}")

    return " | ".join(parts)
