# Changes Made — Asset History Tracking Implementation

## Overview

This document records every file that was created or modified as part of the
centralised, production-grade Asset History tracking system added to the
Asset Management System Frappe application.

---

## Analysis Summary

### A. DocTypes That Trigger Asset History

| DocType | Trigger event(s) | Action type(s) |
|---|---|---|
| BYT Asset | `after_insert` | NEW REGISTRATION |
| BYT Asset | `on_update` — status → Maintenance | UNDER MAINTENANCE |
| BYT Asset | `on_update` — status from Maintenance | RESTORED |
| BYT Asset | `on_update` — status → Deregistered | DEREGISTERED |
| BYT Asset | `on_update` — `assigned_to` None → value | ALLOCATED |
| BYT Asset | `on_update` — `assigned_to` value → None | DEALLOCATED |
| BYT Asset | `on_update` — `assigned_to` value A → B | TRANSFERRED |
| BYT Asset | `on_update` — `location` changed directly | MOVED |
| BYT Asset | `on_update` — `specification` table changed | SPECIFICATION UPDATED |
| BYT Asset | `on_update` — other meaningful fields | UPDATED |
| Asset Assignment | `on_trash` | DEALLOCATED |
| Asset Return | `on_submit` | DEALLOCATED |
| Asset Movement | `on_submit` | MOVED |
| Asset Deregistration | `on_submit` | DEREGISTRATION REQUEST |
| Asset Deregistration | `on_update` — status = Approved | DEREGISTRATION APPROVED |
| Asset Deregistration | `on_update` — status = Rejected | DEREGISTRATION REJECTED |
| Damages | `after_insert` | MARKED DAMAGED |

### B. Why Each Event Fires Where It Does

**BYT Asset `on_update`** handles the majority of transitions because direct
saves (e.g., `BYTAsset.assign_asset()`, `BYTAsset.move_asset()`, or UI edits)
go through `save()`, which triggers `on_update` and provides
`_doc_before_save` for field-level comparison.

**Event DocTypes fire separately** when they use `frappe.db.set_value` to
update BYT Asset, which intentionally bypasses `on_update`:

- `Asset Return._apply_return_to_assignment()` uses `frappe.db.set_value`
  on BYT Asset → on_update is **not** triggered → history is created inside
  `AssetReturn.on_submit()`.
- `Asset Movement._update_asset_location()` uses `frappe.db.set_value` →
  history is created inside `AssetMovement.on_submit()`.
- `Asset Assignment._unassign_asset()` (called from `on_trash`) uses
  `frappe.db.set_value` → history is created inside
  `AssetAssignment._record_deallocated_on_trash()`.

### C. Files Modified

| File | Type | Change |
|---|---|---|
| `asset_system/asset_system/doctype/asset_history/asset_history.json` | Modified | Added `asset` (Link → BYT Asset), `remarks` (Small Text), and `column_break_main` / section fields |
| `asset_system/asset_system/doctype/byt_asset/byt_asset.py` | Modified | Added `_record_new_registration`, `_record_asset_update`, helper functions |
| `asset_system/asset_system/doctype/asset_assignment/asset_assignment.py` | Modified | Added `_record_deallocated_on_trash` called from `on_trash` |
| `asset_system/asset_system/doctype/asset_return/asset_return.py` | Modified | Added `_record_deallocated` called from `on_submit` |
| `asset_system/asset_system/doctype/asset_movement/asset_movement.py` | Modified | Added `_record_moved` called from `on_submit` |
| `asset_system/asset_system/doctype/asset_deregistration/asset_deregistration.py` | Modified | Added `on_submit` (DEREGISTRATION REQUEST), `_approve_deregistration`, `_record_deregistration_rejected` |
| `asset_system/asset_system/doctype/damages/damages.py` | Modified | Implemented `after_insert` → `_record_marked_damaged` |

### D. Files Created

| File | Purpose |
|---|---|
| `asset_system/utils/__init__.py` | Python package marker for the new `utils` module |
| `asset_system/utils/asset_history_service.py` | **Central history service** — all history creation passes through this module |
| `changes-made.md` | This documentation file |

### E. Files Deleted

None.

---

## Detailed Change Log

### `asset_history.json` — Schema Changes

**Why:** The problem specification required `asset` and `remarks` fields,
which were absent from the original schema.

**What was added:**

- `asset` — `Link` field pointing to `BYT Asset`; required, indexed, shown in
  list view.  This is the primary foreign key linking every history record to
  a specific asset.
- `remarks` — `Small Text` for free-form notes attached to a history entry.
- `column_break_main` — column break for improved UI layout.
- Section breaks (`remarks_section`, `changes_section`) for cleaner grouping.
- Existing `section_break_iwxf` given a label ("Event Details").

**No fields were removed.**  The `status` fieldname is preserved (it carries
the action-type value; its label is "Action Type").

**Migration note:** Running `bench migrate` will add the new database columns
(`asset`, `remarks`) to the `tabAsset History` table.  Existing rows will have
`NULL` in these columns, which is acceptable since they pre-date the audit
system.

---

### `asset_history_service.py` — New Central Service

**Location:** `asset_system/utils/asset_history_service.py`

**Public functions:**

#### `create_asset_history(asset, action_type, ...)`

Creates and **immediately submits** an `Asset History` document.

Guards built in:

| Guard | Description |
|---|---|
| Recursion guard | `frappe.local._creating_asset_history` flag prevents Asset History saves from triggering further Asset History saves in the same request. |
| Install/migrate guard | Skips creation during `bench install` or `bench migrate`. |
| Missing-asset guard | Silently returns `None` if the asset does not exist in the database. |
| Error isolation | All exceptions are logged via `frappe.log_error` and never propagate to the caller, preventing history failures from breaking normal business operations. |

#### `detect_field_changes(doc, old_doc, extra_ignore=None)`

Compares two document states and returns a list of
`{"field_name", "old_data", "new_data"}` dicts for every simple field that
changed.  Framework noise fields (name, owner, creation, modified, …) and
derived fields (asset_id, category_abbreviation, …) are always excluded.

#### `detect_child_table_changes(doc, old_doc, table_fieldname)`

Returns `(old_summary, new_summary)` strings for a child table.  Returns
`("", "")` if the table is unchanged.  Uses a deterministic text serialisation
of the rows for comparison.

---

### `byt_asset.py` — Asset Registration & Update Tracking

**`after_insert`** now calls `_record_new_registration(self)`, which fires a
**NEW REGISTRATION** history entry immediately after the asset is persisted.

**`on_update`** now calls `_record_asset_update(self)`, which:

1. Obtains the pre-save document state via `doc.get_doc_before_save()`.
2. Returns early if `old_doc` is `None` (i.e., the event fired during an
   insert — already handled by `after_insert`).
3. Evaluates changes in strict priority order to avoid producing multiple
   history entries per save:

   | Priority | Condition | Action type |
   |---|---|---|
   | 1 | `status` → `Maintenance` | UNDER MAINTENANCE |
   | 2 | `status` from `Maintenance` | RESTORED |
   | 3 | `status` → `Deregistered` | DEREGISTERED |
   | 4a | `assigned_to` None → value | ALLOCATED |
   | 4b | `assigned_to` value → None | DEALLOCATED |
   | 4c | `assigned_to` A → B | TRANSFERRED |
   | 5 | `location` changed | MOVED |
   | 6 | `specification` table changed | SPECIFICATION UPDATED |
   | 7 | Other meaningful fields | UPDATED |

**ALLOCATED** entries include a lookup for the most recent `Asset Assignment`
document so the `reference_docname` points to the assignment, not just the
BYT Asset itself.

**UPDATED** entries only include changes in the field set:
`asset_name`, `serial_number`, `category`, `purchase_date`, `purchase_value`,
`description`.

---

### `asset_assignment.py` — Deletion Tracking

**`on_trash`** now additionally calls `_record_deallocated_on_trash()`.

`_unassign_asset()` (called from `on_trash`) uses `frappe.db.set_value`,
which does **not** trigger BYT Asset's `on_update` hook.  The dedicated method
ensures DEALLOCATED is recorded even when the assignment is hard-deleted.

---

### `asset_return.py` — Formal Return Tracking

**`on_submit`** now additionally calls `_record_deallocated()`.

`_apply_return_to_assignment()` uses `frappe.db.set_value` on both Asset
Assignment and BYT Asset, bypassing all lifecycle hooks.  History is therefore
created explicitly at the end of `on_submit`.  The entry includes:

- `Assigned To` change (old: employee, new: empty)
- `Return Reason` field

---

### `asset_movement.py` — Movement Tracking

**`on_submit`** now additionally calls `_record_moved()`.

`_update_asset_location()` uses `frappe.db.set_value` on BYT Asset.
History is created explicitly in `_record_moved()` with:

- `Location` change (old: from_location, new: to_location)
- `remarks` from the movement document

---

### `asset_deregistration.py` — Full Deregistration Lifecycle

**Added `on_submit`** which calls `_record_deregistration_request()`, firing
a **DEREGISTRATION REQUEST** entry when the deregistration document is first
submitted.

**Refactored `on_update`** to call either `_approve_deregistration()` or
`_record_deregistration_rejected()` based on the `status` change.

`_approve_deregistration()` preserves the original business logic (sets asset
status to Deregistered) and also fires **DEREGISTRATION APPROVED**.

`_record_deregistration_rejected()` fires **DEREGISTRATION REJECTED**.

When the asset is marked Deregistered via `asset.save()` inside
`_approve_deregistration()`, BYT Asset's `on_update` fires and produces a
separate **DEREGISTERED** entry — giving a complete two-entry audit trail for
approved deregistrations.

---

### `damages.py` — Damage Report Tracking

Implemented the previously empty `Damages` controller.

**`after_insert`** calls `_record_marked_damaged()`, which fires **MARKED
DAMAGED** with the physical and working condition values captured at time of
report creation.

Note: The `Damages` DocType uses `asset_id` as its Link field name pointing to
BYT Asset, not `asset`.

---

## Affected Workflows

| Workflow | History entries produced |
|---|---|
| New asset created | NEW REGISTRATION |
| Asset assigned to user | ALLOCATED |
| Asset returned (formal) | DEALLOCATED |
| Asset assignment deleted | DEALLOCATED |
| Asset moved (formal movement doc) | MOVED |
| Asset moved directly via BYT Asset | MOVED |
| Asset put into maintenance | UNDER MAINTENANCE |
| Asset restored from maintenance | RESTORED |
| Asset fields edited | UPDATED |
| Asset specifications changed | SPECIFICATION UPDATED |
| Deregistration submitted | DEREGISTRATION REQUEST |
| Deregistration approved | DEREGISTRATION APPROVED + DEREGISTERED |
| Deregistration rejected | DEREGISTRATION REJECTED |
| Damage report created | MARKED DAMAGED |
| Direct ownership transfer on asset | TRANSFERRED |

---

## Edge Cases Handled

| Edge case | Handling |
|---|---|
| `create_asset_history` called recursively (e.g., history save triggers another hook) | `frappe.local._creating_asset_history` flag blocks re-entry |
| Asset does not exist in DB at time of history creation | Guard returns `None` silently |
| History creation fails (DB error, permission error, etc.) | Caught, logged via `frappe.log_error`, never propagates to caller |
| `on_update` fires during `insert` (both `after_insert` and `on_update` run) | `get_doc_before_save()` returns `None` on insert; `_record_asset_update` exits early |
| Double DEREGISTERED entry (from deregistration approval) | Intentional: DEREGISTRATION APPROVED (from Asset Deregistration controller) + DEREGISTERED (from BYT Asset status change) gives a complete two-step trail |
| `frappe.db.set_value` bypassing hooks | Identified in Asset Return, Asset Movement, and Asset Assignment.on_trash — each fires history explicitly in its own hook |
| `bench migrate` / `bench install` runs | `frappe.flags.in_install` / `in_migrate` guard skips all history creation |
| Missing `asset` reference on Damages (using `asset_id` field) | `_record_marked_damaged` reads `self.asset_id` explicitly |

---

## Migration Requirements

1. Run `bench migrate` on the target site to add the `asset` and `remarks`
   columns to `tabAsset History`.
2. No data migration is required.  Existing Asset History rows will have
   `NULL` in the new columns; this is acceptable.
3. No patches are required.

---

## New Helper / Service Functions

All defined in `asset_system/utils/asset_history_service.py`:

| Function | Purpose |
|---|---|
| `create_asset_history(...)` | Create + submit Asset History record |
| `detect_field_changes(doc, old_doc, ...)` | Return list of changed simple-field dicts |
| `detect_child_table_changes(doc, old_doc, table_fieldname)` | Detect child-table changes, return summaries |
| `_safe_str(value)` | Internal — coerce any value to a clean string |
| `_summarise_child_table(rows)` | Internal — produce deterministic text from child rows |

---

## Hooks Added

No new entries were added to `hooks.py`.  All history tracking uses the
standard Frappe document lifecycle methods (`after_insert`, `on_update`,
`on_submit`, `on_trash`) defined directly on the controller classes.

---
