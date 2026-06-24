# Chromagora OS v0.1 Build Chapterbook

## Build doctrine

Chromagora OS should be built as a multi-agent operating cell for SMBs. The system must not become:
* a chatbot with tools
* a CRM skin
* a generic automation dashboard
* a swarm of ungoverned agents
* a token-burning research toy
* a brittle prompt pile

The correct product architecture is:
```
Business Twin + Department Agents + Bounded Tactical Subagents + Workflow Engine + Policy Kernel + Tool Broker + Action Ledger + Operator Cockpit + Context Economy Layer
```

The additional runtime principle is:
```
Use the smallest sufficient context and model for the task, but never reduce context, model quality, evidence, or verification when business performance, trust, compliance, money, or external commitments are at stake.
```

This chapterbook assumes:
* local Docker is broken
* local development should start with SQLite (Supabase for hosted)
* no Temporal at first
* no real external actions at first
* no uncontrolled LLM agents early
* dry-run execution before real execution
* mock tools before real integrations
* web cockpit before Android companion app
* Android readiness from day one
* GitHub repo as source of truth
