# React ERP - Asset System Exhaustive Test Cases (50+)

This comprehensive document outlines realistic test cases directly derived from the source code of the Asset System module (`apps/asset_system`) and the React ERP frontend. It covers backend validations, API behaviors, UI logic, background hooks, and permission handling.

## 1. Asset Registration & Core Lifecycle (Backend)

### TC-01: Auto-set Asset ID on Registration
* **Module**: `byt_asset.py` (`before_insert`)
* **Steps**: Create a new `BYT Asset` without an `asset_id`.
* **Expected Result**: `asset_id` automatically mirrors the auto-generated `name` of the document.

### TC-02: New Registration History Log
* **Module**: `byt_asset.py` (`_record_new_registration`)
* **Steps**: Save a new `BYT Asset`.
* **Expected Result**: An `Asset History` record is generated with `action_type = "NEW REGISTRATION"`.

### TC-03: Block Invalid Status Transitions
* **Module**: `byt_asset.py` (`_validate_status_transition`)
* **Steps**: Attempt to update a `"Deregistered"` asset's status back to `"Available"`.
* **Expected Result**: Validation error: `"Status transition from 'Deregistered' to 'Available' is not allowed"`.

### TC-04: API Endpoint `create_asset`
* **Module**: `api.py` (`create_asset`)
* **Steps**: POST to `create_asset` with `asset_name` and `category`.
* **Expected Result**: An asset is created with default status `"Available"` and returned in the JSON response.

### TC-05: Missing Required Fields in API
* **Module**: `api.py` (`create_asset`)
* **Steps**: POST to `create_asset` missing `category`.
* **Expected Result**: 400 Bad Request / Validation Error: `"category is required."`

## 2. Asset Assignments (Backend & UI)

### TC-06: Successful Asset Assignment (Backend)
* **Module**: `asset_assignment.py` (`_assign_asset`)
* **Steps**: Create an active `Asset Assignment` for an employee.
* **Expected Result**: Assignment activates, `BYT Asset` status updates to `"Assigned"`, and `"ASSIGNED"` history logs.

### TC-07: Prevent Assigning Unavailable Asset
* **Module**: `asset_assignment.py` (`_validate_asset_available`)
* **Steps**: Try to assign a `"Maintenance"` or `"Deregistered"` asset.
* **Expected Result**: Validation error thrown.

### TC-08: Assignment Date Validation
* **Module**: `asset_assignment.py` (`_validate_dates`)
* **Steps**: Set `return_date` to a date prior to `assigned_date`.
* **Expected Result**: Validation error: `"Return Date cannot be before Assigned Date."`

### TC-09: Assign Asset Button Disabled State
* **Module**: `AssetDetails.jsx`
* **Steps**: View an asset that is `"Assigned"` or `"Deregistered"`.
* **Expected Result**: The `Assign Asset` button is completely disabled.

### TC-10: Redirect to Assignment Form
* **Module**: `AssetDetails.jsx`
* **Steps**: Click `Assign Asset` on an `"Available"` asset.
* **Expected Result**: Routes properly to `/asset/assignment?asset=AST-001`.

## 3. Asset Returns (Backend & UI)

### TC-11: Successful Asset Return
* **Module**: `asset_return.py` (`_apply_return_to_assignment`)
* **Steps**: Submit an `Asset Return` for an active assignment.
* **Expected Result**: Assignment marked inactive (`status = "Returned"`). Asset reverts to `"Available"`.

### TC-12: Asset Return Under Maintenance
* **Module**: `asset_return.py` (`_apply_return_to_assignment`)
* **Steps**: Return an asset currently in `"Maintenance"`.
* **Expected Result**: Assignment deactivated, but Asset status safely **remains** `"Maintenance"`.

### TC-13: Cancel Asset Return (Revert bug test)
* **Module**: `asset_return.py` (`_revert_assignment`)
* **Steps**: Cancel an `Asset Return`.
* **Expected Result**: Assignment reactivates. (Note: Known logic bug where the Asset itself fails to restore its status).

### TC-14: UI Return Drawer Opens
* **Module**: `AssetDetails.jsx`
* **Steps**: Click "Return Asset" on an active assignment view.
* **Expected Result**: The slide-out `Return Asset` drawer successfully overlays the screen.

### TC-15: UI Return Drawer Validation
* **Module**: `AssetDetails.jsx` (Drawer form)
* **Steps**: Try submitting a return with an empty `return_reason`.
* **Expected Result**: Frontend blocks submission and displays field-level error text.

## 4. Asset Issues (Backend & UI)

### TC-16: Raising Issue Moves Asset to Maintenance
* **Module**: `asset_issue.py` (`_apply_issue_state`)
* **Steps**: Employee creates an `Asset Issue` (`"In Progress"`).
* **Expected Result**: `BYT Asset` status automatically becomes `"Maintenance"`.

### TC-17: Resolving Issue Restores Previous State
* **Module**: `asset_issue.py` (`_restore_asset_status`)
* **Steps**: Resolve the open `Asset Issue`.
* **Expected Result**: `BYT Asset` restores to `"Assigned"` (if assignment is active) or `"Available"`.

### TC-18: Multiple Active Issues Resolution
* **Module**: `asset_issue.py` (`_has_other_active_issues`)
* **Steps**: Resolve one of TWO open issues on a single asset.
* **Expected Result**: Asset status stays `"Maintenance"` due to the remaining open issue.

### TC-19: Unauthorized Issue Reporter
* **Module**: `asset_issue.py` (`_validate_reporter_role`)
* **Steps**: Log in as a User with no roles except "Guest" and try to create an issue.
* **Expected Result**: Validation Error: `"Only Employee, System Manager, or Infra Executive can raise Asset Issues."`

### TC-20: Asset Issues UI Row Redirection
* **Module**: `AssetIssues.jsx` / `Reports.jsx`
* **Steps**: Click a table row for an open issue.
* **Expected Result**: User is routed to `/asset/issues/{issue_name}`.

## 5. Asset Deregistration (Backend & UI)

### TC-21: Prevent Deregistration of Assigned Assets
* **Module**: `asset_deregistration.py` (`before_save`)
* **Steps**: Try to deregister an `"Assigned"` asset.
* **Expected Result**: Validation error requesting deallocation first.

### TC-22: Approve Deregistration
* **Module**: `asset_deregistration.py` (`_approve_deregistration`)
* **Steps**: Approve an `Asset Deregistration` request.
* **Expected Result**: Asset status becomes permanently `"Deregistered"`. `"DEREGISTRATION APPROVED"` history log created.

### TC-23: Hidden UI Buttons for Deregistered Assets
* **Module**: `AssetDetails.jsx`
* **Steps**: Open an asset with status `"Deregistered"`.
* **Expected Result**: Both the `Edit` and `Deregister` buttons are hidden from the action bar.

### TC-24: Deregistration Drawer Form Submission
* **Module**: `AssetDetails.jsx`
* **Steps**: Select "Sold" from the dropdown in the Deregister Drawer and submit.
* **Expected Result**: API call completes, UI flashes success banner, and drawer closes automatically.

## 6. Asset Movements (Backend)

### TC-25: Successful Asset Movement
* **Module**: `asset_movement.py`
* **Steps**: Submit an `Asset Movement` document with different `from_location` and `to_location`.
* **Expected Result**: Linked `BYT Asset` updates its `location` field and logs `"MOVED"`.

### TC-26: Identical Locations Validation
* **Module**: `asset_movement.py` (`_validate_locations`)
* **Steps**: Submit an `Asset Movement` where `from_location` == `to_location`.
* **Expected Result**: Throw error: `"'From Location' and 'To Location' cannot be the same."`

### TC-27: Prevent Movement of Deregistered Asset
* **Module**: `asset_movement.py` (`_validate_not_deregistered`)
* **Steps**: Submit movement for a `"Deregistered"` asset.
* **Expected Result**: Throw error: `"Asset ... is deregistered and cannot be moved."`

### TC-28: API Endpoint `move_asset`
* **Module**: `api.py` (`move_asset`)
* **Steps**: Call `move_asset` endpoint passing `asset` and `to_location`.
* **Expected Result**: Automatically creates and submits an `Asset Movement` document.

## 7. Audit Logging & Asset History Service

### TC-29: Ignore Framework Fields from Tracking
* **Module**: `asset_history_service.py` (`detect_field_changes`)
* **Steps**: Modify `owner` or `docstatus` on an asset.
* **Expected Result**: Service returns empty `changes` array; no history log created for noise fields.

### TC-30: Safe String Coercion for Empty Values
* **Module**: `asset_history_service.py` (`_safe_str`)
* **Steps**: Update a text field from `None` (null) to an actual string.
* **Expected Result**: Handled gracefully without crash; `old_data` recorded as `""`.

### TC-31: Recursive Save Guard
* **Module**: `asset_history_service.py`
* **Steps**: Trigger a history save that attempts to recursively trigger another history save.
* **Expected Result**: `frappe.local._creating_asset_history` flag instantly returns `None` and blocks infinite loop.

### TC-32: Specification Child Table Change Tracking
* **Module**: `asset_history_service.py` (`detect_child_table_changes`)
* **Steps**: Add a new row to the `specification` table of a `BYT Asset` and save.
* **Expected Result**: `"SPECIFICATION UPDATED"` history record maps the exact new spec mapping as added.

## 8. Querying & API Data Retrieval

### TC-33: API Pagination - Get Assets
* **Module**: `api.py` (`get_assets`)
* **Steps**: Request `page=2` and `page_length=10`.
* **Expected Result**: Returns items index 10-19 with correct `total` count parameter.

### TC-34: Nested Complex Filters API
* **Module**: `api.py` (`get_filtered_doctype_list`)
* **Steps**: Pass `['status', 'in', ['Open', 'In Progress']]` as `parent_filters`.
* **Expected Result**: Safely translated to Frappe standard list operators and filtered successfully.

### TC-35: KPI Endpoint Filters Ignore Invalid Dates
* **Module**: `api.py` (`get_reports_dashboard_data`)
* **Steps**: Verify `already_expired` query.
* **Expected Result**: Handled cleanly with `< today()`; no postgres `InvalidDatetimeFormat` crash.

### TC-36: KPI Open Issues Count Accuracy
* **Module**: `api.py`
* **Steps**: Fetch `overdue_issues` where status includes `["in", [...]]`.
* **Expected Result**: Backend leverages `len(frappe.get_all(...))` resolving previous complex list issues.

## 9. Frontend UI: Asset Form Rendering & Logic

### TC-37: Create Form - Empty Button Disable
* **Module**: `CreateAsset.jsx`
* **Steps**: Load the Create Asset form. Leave all fields empty.
* **Expected Result**: The `Save Asset` button is greyed out (`cursor-not-allowed`).

### TC-38: Create Form - Dynamic Column Splitting
* **Module**: `CreateAsset.jsx` (`rightSections` logic)
* **Steps**: Inspect form rendering layout.
* **Expected Result**: Fields labeled "Location", "Attachment", "Remark" automatically render in the narrower right column.

### TC-39: Child Table - Add Row Button
* **Module**: `CreateAsset.jsx` / `DynamicDoctypeForm`
* **Steps**: Click `+ Add Row` on the specifications table.
* **Expected Result**: Injects an empty state row mapping to child schema fields.

### TC-40: Child Table - Delete Row
* **Module**: `CreateAsset.jsx`
* **Steps**: Click `Delete` on a specific child table row.
* **Expected Result**: The exact index is spliced from `form[field.fieldname]` and instantly removed from UI.

### TC-41: Form Validation Highlights
* **Module**: `CreateAsset.jsx` (`validateRequiredFields`)
* **Steps**: Submit form with missing `category`.
* **Expected Result**: Local state sets an error object. Text spans render immediately below the offending input field.

### TC-42: Successful Flash Message on Redirect
* **Module**: `CreateAsset.jsx` -> `Assets.jsx`
* **Steps**: Submit a valid form. Wait 1000ms.
* **Expected Result**: Page routes to `/assets` passing `state.flashMessage`. `Assets.jsx` consumes state and shows a banner.

## 10. Frontend UI: List Views, Filtering & Export

### TC-43: Filter Option Parsing
* **Module**: `Assets.jsx` (`statusOptions`)
* **Steps**: Load page.
* **Expected Result**: Status dropdown natively reads options defined directly from `getDoctypeMeta` backend JSON string splits.

### TC-44: Active Filter Chips Rendering
* **Module**: `Assets.jsx` (`activeFilterChips`)
* **Steps**: Apply filter `Status = Available`.
* **Expected Result**: A chip is dynamically rendered indicating `"Status = Available"`.

### TC-45: Empty State UI
* **Module**: `Assets.jsx`
* **Steps**: Search for `gibberishstringxyz`.
* **Expected Result**: Table hides and specifically displays `"No records found."` span.

### TC-46: Disable Next Page Button
* **Module**: `Assets.jsx`
* **Steps**: Navigate to the last page of data where `data.length < pageSize`.
* **Expected Result**: `Next` button switches to disabled/cursor-not-allowed.

### TC-47: CSV Exporter Headers & Map
* **Module**: `Reports.jsx` (`exportCsv`)
* **Steps**: Navigate to Warranty Expiry tab and click `Export Report`.
* **Expected Result**: Generates CSV blob locally with headers: `Asset Code`, `Type`, `Serial Number`, `Warranty Expiry`, `Vendor`, `Alert`.

### TC-48: CSV Exporter Warranty Alerts
* **Module**: `Reports.jsx` (`exportCsv`)
* **Steps**: Export report containing a past date.
* **Expected Result**: Diff math correctly injects the literal string `"Expired"` into the Alert column cell of the CSV.

## 11. Role-Based Permissions & Employee Restrictions

### TC-49: Employee Row-Level Assets Security
* **Module**: `byt_asset.py` (`get_permission_query_conditions`)
* **Steps**: Employee fetches `BYT Asset` list.
* **Expected Result**: Custom SQL condition appended to restrict output solely to records with an active `Asset Assignment` to that specific user.

### TC-50: "No Access" UI State Rendering
* **Module**: `AssetAssignment.jsx`
* **Steps**: User without read permissions accesses `/asset/assignment`.
* **Expected Result**: `permissionDenied` state flips to true; renders lock icon UI: `"You do not have permission to view asset assignments."`

### TC-51: Granular UI Action Toggles
* **Module**: `AssetDetails.jsx` (`perms` state)
* **Steps**: Evaluate header actions array.
* **Expected Result**: The frontend evaluates `hasDoctypePermission(..., 'create')` etc to specifically hide/show `canAssign`, `canEdit`, and `canDeregister` buttons depending on exact granted framework roles.
