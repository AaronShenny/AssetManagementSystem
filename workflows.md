# Workflow UI Reference

This document is the frontend reference for workflow-driven UI behavior.

Sources used:
- `/workflow/1.csv`
- `/workflow/2.csv`
- DocType metadata for workflow state fields

## Global implementation rules

- Keep workflow rendering dynamic.
- Do not hardcode state/action rendering (except explicitly required special-action behavior).
- Do not update `workflow_state_1` directly.
- Use workflow APIs for transitions:
  - `POST /api/method/frappe.model.workflow.get_transitions`
  - `POST /api/method/frappe.model.workflow.apply_workflow`
- After any successful action, refresh the document and fetch transitions again.
- Backend permissions and workflow checks are the source of truth.

## Dynamic UI implementation flow

1. On page load, fetch the document and read current workflow state.
2. Call `get_transitions` for available actions.
3. Render action buttons dynamically from backend transitions.
4. For normal actions, call `apply_workflow` directly.
5. For special actions (Asset Issue `Assign`), run action-specific UI behavior first.
6. After success, reload document + transitions.

---

## 1) Asset Issue

- **Workflow name:** Asset Issue
- **Document type:** `Asset Issue`
- **Workflow state field:** `workflow_state_1`

### All states

| State |
|---|
| Open |
| Assigned |
| In Progress |
| Waiting for IT |
| Waiting for Vendor |
| Resolved |
| Closed |

### All transitions

| Current state | Action label | Next state | Allowed role(s) | Condition | Terminal? |
|---|---|---|---|---|---|
| Open | Assign | Assigned | Ambiguous (not defined in CSV/DocType metadata) | None defined | No |
| Open | Close | Closed | Ambiguous (not defined in CSV/DocType metadata) | None defined | Yes (Closed has no actions) |
| Assigned | Start Work | In Progress | Ambiguous (not defined in CSV/DocType metadata) | None defined | No |
| In Progress | Send to IT | Waiting for IT | Ambiguous (not defined in CSV/DocType metadata) | None defined | No |
| In Progress | Send to Vendor | Waiting for Vendor | Ambiguous (not defined in CSV/DocType metadata) | None defined | No |
| Waiting for IT | Resolve | Resolved | Ambiguous (not defined in CSV/DocType metadata) | None defined | No |
| Waiting for Vendor | Resolve | Resolved | Ambiguous (not defined in CSV/DocType metadata) | None defined | No |
| Resolved | Close | Closed | Ambiguous (not defined in CSV/DocType metadata) | None defined | Yes (Closed has no actions) |

### Canonical transition map (must match UI behavior)

- Open → Assign → Assigned
- Open → Close → Closed
- Assigned → Start Work → In Progress
- In Progress → Send to IT → Waiting for IT
- In Progress → Send to Vendor → Waiting for Vendor
- Waiting for IT → Resolve → Resolved
- Waiting for Vendor → Resolve → Resolved
- Resolved → Close → Closed
- Closed → No actions

### Special UI behavior (Asset Issue: `Assign`)

When user clicks **Assign**:

1. Open popup/modal.
2. Allow search/select of **User** record (`Doctype: User`; requirement text refers to `Users`).
3. Save selected user into `assigned_to`.
4. Apply workflow action `Assign` using `apply_workflow`.
5. After success, reload document and workflow actions.

Important:
- `assigned_to` is business data, not workflow state.
- Do not update `workflow_state_1` directly.

### Important implementation notes

- Keep actions dynamic from `get_transitions`.
- Do not add inferred transitions not present in canonical definition.
- Treat role/condition enforcement as backend-driven.

---

## 2) Asset Deregistration

- **Workflow name:** Asset Deregistration
- **Document type:** `Asset Deregistration`
- **Workflow state field:** `workflow_state_1`

### All states

| State |
|---|
| Submitted |
| HOD Approved |
| Asset Issued |
| Closed |

### All transitions

| Current state | Action label | Next state | Allowed role(s) | Condition | Terminal? |
|---|---|---|---|---|---|
| Submitted | Approve | HOD Approved | Ambiguous (not defined in CSV/DocType metadata) | None defined | No |
| HOD Approved | Issue Asset | Asset Issued | Ambiguous (not defined in CSV/DocType metadata) | None defined | No |
| Asset Issued | Close | Closed | Ambiguous (not defined in CSV/DocType metadata) | None defined | Yes (Closed has no actions in CSV) |

### Special UI behavior

- No action-specific special UI behavior defined in available source files.

### Important implementation notes

- Roles/conditions are not explicit in provided CSVs; mark as ambiguous until verified from actual Frappe Workflow records/API.
- Do not guess additional transitions.

---

## 3) Other workflows found in `/workflow`

No additional workflows found beyond:
- `workflow/1.csv` (Asset Issue)
- `workflow/2.csv` (Asset Deregistration)
