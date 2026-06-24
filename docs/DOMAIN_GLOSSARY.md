# Chromagora OS — Domain Glossary

## A

**ActionExecution** — An immutable ledger record of a tool call. Includes tool name, redacted arguments, result, actor, timestamps, and trace_id.

**ActionLedger** — The complete, append-only record of all actions proposed, approved, executed, or failed for a business.

**ActionProposal** — A structured proposal for an action, submitted by an agent or subagent. Passes through Policy Kernel before execution.

**AgentDefinition** — A template defining an agent type: name, standing mission, default events, tools, authority level, and default model tier.

**AgentRun** — A tracked instance of an agent execution. Records input, output, status, cost, model used, and trace_id.

**ApprovalRequest** — A human-in-the-loop approval record linked to an ActionProposal. Status: pending, approved, rejected, cancelled, expired.

**AuthorityEnvelope** — Defines the scope of action for an agent: which tools, which action types, max dollar exposure, autonomy level, and conditions.

## B

**Business** (ClientBusiness) — A client company operating on the platform. Has one Business Twin, multiple agents, and scoped data.

**Business Cell** — The runtime container for one business. All agents, workflows, and data are scoped to a Cell.

**BusinessTwin** — The canonical structured mirror of a business: services, capacity, areas, preferences, and claims.

**BusinessToolPermission** — Enables or disables a specific tool for a specific business, with optional autonomy and approval overrides.

## C

**CallRecord** — A phone call record with transcript, consent, and summary fields. Created in Chapter 23 (Voice).

**ClientBusiness** — See Business.

**Command Feed** — The real-time event display in the Operator Cockpit. Powered by Supabase Realtime.

**ComplianceRule** — A jurisdiction-specific rule governing actions (CASL, privacy, procurement rules, etc).

**ContextBudget** — Defines token and retrieval limits for an agent run.

**Context Packet** — A compact, task-specific context object built for each agent run. Contains only what's needed.

## D

**Department Agent** — A persistent, named agent owning a domain: Sales, Reputation, Growth, Procurement, Operations, Compliance, etc.

## E

**Event** — An immutable record of something that happened. All major state changes emit events. Event types include:
- business.created, business_twin.updated
- lead.created, lead.qualified
- quote.sent, quote.stale
- job.completed
- review.requested, review.received
- opportunity.detected
- approval.required
- action.proposed, action.approved, action.rejected, action.executed, action.failed
- policy.violation_detected
- agent.run_started, agent.run_completed, agent.run_failed

**Event Stream** — Supabase Realtime channel for live event feeds. Scoped by tenant and business.

## F

**ForbiddenBusinessClaim** — A claim that an agent or the system must NEVER make on behalf of a business.

**ApprovedBusinessClaim** — A verified claim that agents MAY make (insured, licensed, response time, etc).

## L

**Lead** — A potential customer or deal in the CRM-lite system.

## M

**MessageDraft** — A draft email or SMS message. Must be approved before sending (never sent in dry-run mode).

**ModelTier** — Routing tier (0-4) determining which model class to use for a task.

## O

**Opportunity** — A procurement opportunity detected or created for a business. Tracked through qualification stages.

**Operator Cockpit** — The web-based command surface: Command Feed, Approvals, Business Manager, Agents, Opportunities, Ledger, Settings.

## P

**PolicyDecision** — The output of Policy Kernel evaluation: allowed, requires_approval, denied, with reasons and recommendations.

**Policy Kernel** — The deterministic evaluation layer that checks every proposed action against Authority Envelopes and Compliance Rules.

## Q

**Quote** — A price estimate sent to a lead. Tracked for stale-quote workflows.

## R

**RLS (Row Level Security)** — Supabase PostgreSQL feature enforcing tenant isolation at the database level.

## S

**ServiceArea** — Geography or zone a business services.

**SpawnContract** — A structured contract defining a subagent's objective, scope, tools, token budget, and TTL.

**Supabase** — The primary database, auth, realtime, and storage layer for Chromagora OS.

## T

**Tenant** — The top-level organizational unit. All data is tenant-scoped. Multi-tenancy enforced via RLS.

**TokenBudgetPolicy** — Service that selects model tier and context budget based on task type and risk.

**ToolBroker** — The single gateway for all real-world actions. No agent calls tools directly.

**ToolDefinition** — A catalog entry for a tool: name, description, target system, schemas, risk level, autonomy level.

**Trace ID** — A unique identifier propagated through all records in a workflow execution chain.

## V

**Vector Memory** — Optional pgvector-based semantic memory (not canonical state). Feature-flagged.

## W

**WorkflowDefinition** — A template for a workflow: name, type, version, config.

**WorkflowEngine (Workflow Lite)** — Database-backed state machine engine for orchestrating workflows.

**WorkflowRun** — An instance of a workflow execution. Tracks state, steps, and result.

**WorkflowStepLog** — Log of each step execution within a WorkflowRun.
