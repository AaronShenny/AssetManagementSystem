# Workflows Reference

This reference summarizes the workflows exported from the `workflow/` CSV files for frontend UI development. Each workflow lists the state field, states, transitions, roles, conditions (if any), terminal transitions, and implementation notes.

---

## AD WORKFLOW2 — Asset Deregistration

- **Document Type:** Asset Deregistration
- **Workflow state field:** `status`

### States

| State | Notes |
|---|---|
| Pending | Inferred as an initial state in the transitions; appears in transition rows as the current state |
| Approved | Present as a documented state; no outgoing transitions visible in CSV extract (likely terminal) |
| Clarification Required | Present |
| Rejected | Present; appears to be final/terminal |

### Terminal States

- Rejected
- Approved (unless future transitions are added)

### Transitions

| Current State | Action Label | Next State | Allowed Role(s) | Condition | Terminal |
|---|---:|---|---|---|---:|
| Pending | Review | Clarification Required | Leadership | (none specified) | No |
| Pending | Reject | Rejected | Leadership | (none specified) | Yes (Rejected has no outgoing transitions in CSV) |
| Pending | Approve | Approved | Leadership | (none specified) | Yes (Rejected has no outgoing transitions in CSV) |
Notes:
- The CSV export includes a large `Workflow Data` JSON (layout info) that was truncated in the export; that JSON lists additional state metadata but not needed for UI actions.
- The mapping of flattened CSV columns makes it ambiguous which state some transitions are attached to; where possible above the current state was taken from the `State (Transitions)` column. If you need authoritative mapping, confirm against the backend workflow API or the workflow builder UI.
- `Approved` is listed as a state but no outgoing transition rows were present in the CSV extract — treat it as terminal until confirmed otherwise.

**API hints for frontend**
- Read the `status` field to determine the current workflow state.
- Workflow transitions must be executed through the workflow API; never directly update `status` to move a document between states.
- Transition/action labels to display: `Review`, `Reject` (show only if user role includes `Leadership`).

---

## AD WORKFLOW 2 — Asset Issue (Canonical)

- **Document Type:** Asset Issue
- **Workflow state field:** `workflow_state_1`

Canonical / Source of Truth: the following workflow is the authoritative definition for UI generation, API integration, and state-based action rendering. Do not infer transitions separately — use this definition.

Workflow flow (canonical):

Open
├── Assign → Assigned
└── Close → Closed

Assigned
└── Start Work → In Progress

In Progress
├── Send to IT → Waiting for IT
└── Send to Vendor → Waiting for Vendor

Waiting for IT
└── Resolve → Resolved

Waiting for Vendor
└── Resolve → Resolved

Resolved
└── Close → Closed

Closed
└── No further actions (Terminal State)

### Rules (UI / API)

- `Closed` is a terminal state; no actions should be shown when a document is in `Closed`.
- An issue may be closed directly from `Open` using the `Close` action (for invalid/duplicate/cancelled issues).
- Only show actions reachable from the current state; never show actions that are not directly defined as outgoing from the current state.
- Use this workflow as the source of truth; do not infer additional transitions from CSV exports.

### Terminal States

- Closed

### Expected UI Actions by State

| State | Actions (ordered) |
|---|---|
| Open | Assign, Close |
| Assigned | Start Work |
| In Progress | Send to IT, Send to Vendor |
| Waiting for IT | Resolve |
| Waiting for Vendor | Resolve |
| Resolved | Close |
| Closed | (none) |

### Transitions (for implementation)

| Current State | Action Label | Next State | Role | Notes |
|---|---:|---|---|---|
| Open | Assign | Assigned | Infra Executive | Typical path for valid issues |
| Open | Close | Closed | Infra Executive | Direct close for invalid/duplicate/cancelled issues |
| Assigned | Start Work | In Progress | Infra Executive | |
| In Progress | Send to IT | Waiting for IT | Infra Executive | |
| In Progress | Send to Vendor | Waiting for Vendor | Infra Executive | |
| Waiting for IT | Resolve | Resolved | Infra Executive | |
| Waiting for Vendor | Resolve | Resolved | Infra Executive | |
| Resolved | Close | Closed | Infra Executive | Terminal transition |

### API & UI integration hints

- Read `workflow_state_1` to determine the current workflow state.
- Workflow transitions must be executed through the workflow API. Never directly update `workflow_state_1` to move a document between states.
- The backend should expose available transitions for the current user/document. If it does not, the frontend may compute available actions by matching the user's roles against transition `Allowed` values, but the backend remains the source of truth for permissions.
- When rendering buttons, label them with the `Action Label` (e.g., `Start Work`, `Send to IT`). On click, call the workflow transition API with the action identifier; after a successful transition, reload the document to get the updated `workflow_state_1` value from the server.

- The frontend should fetch available actions using `get_transitions`.
- The frontend should render action buttons based on the returned actions (do not hard-code actions client-side).
- The frontend should execute transitions using `apply_workflow` (server API) rather than mutating state fields.
- After a successful transition, reload the document to obtain the updated workflow state.
- Treat the workflow definition in this document as documentation; the backend remains the source of truth for permissions and which actions are actually available to the current user.

### Notes

- This section replaces the CSV-derived interpretation. Treat this canonical listing as authoritative for all UI and API work.

## Workflow APIs

### Get Available Actions

Endpoint:

POST /api/method/frappe.model.workflow.get_transitions

Request:

{
  "doc": {
    "doctype": "Asset Issue",
    "name": "<document_name>"
  }
}

Purpose:
Returns the workflow actions available to the current user for the current document state.

### Apply Workflow Action

Endpoint:

POST /api/method/frappe.model.workflow.apply_workflow

Request:

{
  "doc": {
    "doctype": "Asset Issue",
    "name": "<document_name>"
  },
  "action": "<action_name>"
}

Purpose:
Executes a workflow transition and updates the document's workflow state.

---

## Global notes & recommendations

- The CSVs are flattened exports from a workflow builder and include layout metadata which was truncated in this extraction. For authoritative, up-to-date transition metadata (roles, conditions, allow-self-approval flags), call the server-side workflow endpoint or inspect the workflow via the builder UI.
- For UI behavior:
  - Query the backend for available transitions for the current user/document (server should return only those allowed). If the backend does not filter, the frontend should compute visibility by matching the user's roles against `Allowed Role(s)`.
  - Render action buttons using the `Action (Transitions)` label; on click, call the workflow API to perform the transition (e.g., `apply_workflow`) and then reload the document to obtain the updated workflow state rather than attempting to write state fields directly.

If you want, I can:
- Attempt a second-pass parse that reconstructs the full JSON `Workflow Data` (requires the original un-truncated CSV export), or
- Generate a small JSON file mapping states → actions for each workflow for direct use in UI storybook/mock data.
