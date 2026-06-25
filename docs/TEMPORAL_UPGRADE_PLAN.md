# Temporal Upgrade Plan

Chromagora OS uses workflow-lite (database-backed state machines) for v0.1. This document plans the migration to Temporal for durable workflows.

## Why Temporal Later

- workflow-lite is sufficient for v0.1 and does not require Docker
- Temporal adds operational complexity (Temporal Server, Workers, Namespaces)
- Temporal Cloud is the target (no local Docker)
- Migration happens only after product loops are proven

## What Stays in Workflow-Lite

- Simple CRUD workflows (create, update, delete records)
- Status tracking with deterministic transitions
- Workflows that complete in seconds

## What Moves to Temporal

- Approval pauses with long waits (hours/days)
- Timer-based retries and scheduled follow-ups
- Tool Broker calls that need retry logic with backoff
- Multi-step workflows with compensation/rollback
- Cross-business workflows (supplier coordination)

## Migration Strategy

1. Define Temporal workflows in Python SDK
2. Keep WorkflowRun table as the source of truth for status
3. Temporal Workflow ID stored in WorkflowRun.temporal_workflow_id
4. WorkflowLiteAdapter and TemporalAdapter share the same interface
5. Feature flag: USE_TEMPORAL for gradual rollout

## Interface

```
start_workflow(workflow_type, input_data) -> workflow_id
signal_workflow(workflow_id, signal_name, signal_data)
get_workflow_status(workflow_id) -> status
cancel_workflow(workflow_id)
```

Current adapter: WorkflowLiteAdapter
Future adapter: TemporalAdapter (documented, not implemented)

## Timeline

Not in v0.1. Targeted for v0.2 after real-world workflow volume justifies the operational cost.
