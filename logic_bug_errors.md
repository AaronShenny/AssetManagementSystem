# React ERP - Logic Bugs & Vulnerabilities

This document details logic mistakes, fragile code paths, and bugs identified in the Asset System backend during a deep code inspection.

### 1. Assignment `NameError` crash due to `doc` undefined
* **File/Module**: `asset_assignment.py` (`_assign_asset`)
* **Why it is a bug**: At line 84, the code calls `old_doc = doc.get_doc_before_save()`. In this class scope, `doc` is not defined (it should be `self`). Additionally, at line 90, it references `self.assignment` instead of `self.assigned_to`. Any attempt to assign an asset throws a `NameError` causing a runtime exception.
* **Suggested fix**: Replace `doc.get_doc_before_save()` with `self.get_doc_before_save()`. Fix the typo from `self.assignment` to `self.assigned_to`.
* **Severity**: **High** (Breaks core assignment workflow)

### 2. Asset Return Cancellation leaves Asset Status in an inconsistent state
* **File/Module**: `asset_return.py` (`_revert_assignment`, `on_cancel`)
* **Why it is a bug**: When an `Asset Return` is cancelled, `_revert_assignment()` correctly resets the `Asset Assignment` back to active (`is_active = 1`, `status = "Assigned"`). However, it completely fails to update the underlying `BYT Asset` to restore its `assigned_to` field and its `status` back to `"Assigned"`. This results in severe data inconsistency: the Assignment is active, but the Asset thinks it is `"Available"` and unassigned.
* **Suggested fix**: Add logic in `_revert_assignment` to fetch the linked `BYT Asset` and reset its `assigned_to` and `status` back to the active assignment's details.
* **Severity**: **High** (Stale/inconsistent core data)

### 3. Debugging `print()` left in permission query hook
* **File/Module**: `byt_asset.py` and `asset_issue.py` (`get_permission_query_conditions`)
* **Why it is a bug**: There is a stray `print(escaped_user)` in the permission hook. Since this hook runs on *every single list query* for Employee users, it will aggressively spam the production Frappe console logs.
* **Suggested fix**: Remove `print(escaped_user)`.
* **Severity**: **Low** (Performance/Log bloat)

### 4. Bypassing Validation Hooks during Asset Returns
* **File/Module**: `asset_return.py` (`_apply_return_to_assignment`)
* **Why it is a bug**: The code uses `frappe.db.set_value` to update the `BYT Asset` status to `"Available"` and clear the assignee. A developer note correctly observes: `# use doc.save, frappe.db.set_value dosent triggers validate,on_update things like that`. Because hooks are bypassed, custom status transition validations in `byt_asset.py` (and potential webhook integrations) never execute when an asset is returned.
* **Suggested fix**: Fetch the `BYT Asset` via `frappe.get_doc`, modify the properties, and call `asset.save()`.
* **Severity**: **Medium** (Fragile architecture / Missing triggers)

### 5. `AssetDeregisration` prevents deregistration of "Assigned" but ignores "In Use"
* **File/Module**: `asset_deregistration.py` (`before_save`, `_approve_deregistration`)
* **Why it is a bug**: The code hardcodes a check: `if asset.status == "Assigned": frappe.throw(...)` to prevent deregistering active assets. However, if an asset somehow gets an `"In Use"` status (which was referenced in older assignments), it will bypass this check and successfully deregister an actively allocated asset.
* **Suggested fix**: Instead of checking strings, use the existing helper: `if has_active_assignment(self.asset): frappe.throw(...)`.
* **Severity**: **Medium** (Wrong status transitions allowed)

### 6. Duplicate History Entries generated upon Deregistration
* **File/Module**: `asset_deregistration.py` and `byt_asset.py`
* **Why it is a bug**: In `asset_deregistration.py`, `_approve_deregistration()` explicitly creates a `DEREGISTRATION APPROVED` history entry. Immediately after, it calls `asset.save(ignore_permissions=True)`. This triggers `BYT Asset`'s `on_update` hook in `byt_asset.py`, which sees the status change to "Deregistered" and blindly creates a *second* history entry: `DEREGISTERED in Asset page`.
* **Suggested fix**: Remove the redundant history creation inside `BYT Asset` for deregistration, or pass a flag in `flags` during the save to suppress the duplicate hook.
* **Severity**: **Low** (Duplicate records / UX clutter)

### 7. Terminal State Lock-in on `ALLOWED_TRANSITIONS`
* **File/Module**: `byt_asset.py` (`_validate_status_transition`)
* **Why it is a bug**: The dictionary defines `"Deregistered": []`. If an asset is accidentally marked as Deregistered (e.g. by a misclick or integration error), it is permanently locked in this state. System Managers cannot intervene to restore it because the transition validation strictly blocks it.
* **Suggested fix**: Allow an explicit rollback transition from `"Deregistered"` -> `"Available"` for `System Manager` roles only.
* **Severity**: **Medium** (Broken workflows with no recovery)

### 8. Potential bug restoring from "Scrapped" assignments
* **File/Module**: `asset_assignment.py` (`_unassign_asset`)
* **Why it is a bug**: When deactivating an assignment, the code checks `if current_status not in ("Maintenance", "Deregistered"): update_values["status"] = "Available"`. It fails to account for a `"Scrapped"` status (or similar terminal states if added later). If a scrapped asset's assignment is trashed, the asset incorrectly reverts to `"Available"`.
* **Suggested fix**: Use a whitelist check ensuring the status is only reverted if the current status is strictly `"Assigned"` or `"In Use"`.
* **Severity**: **Medium** (Incorrect status transitions)
