# Chromagora OS v0.1

A multi-agent operating system for SMBs.

Chromagora OS is not a chatbot, CRM skin, or generic automation tool. It is a structured operating cell where autonomous agents operate under explicit policies and authority, execute business workflows, maintain a live Business Twin mirror of real business state, and enable human-in-the-loop oversight through an Operator Cockpit.

## Architecture

```
Business Twin + Department Agents + Bounded Tactical Subagents +
Workflow Engine + Policy Kernel + Tool Broker + Action Ledger +
Operator Cockpit + Context Economy Layer
```

## Database

Supabase (PostgreSQL + Auth + Realtime + RLS) is the primary and only datastore. No SQLite, no local Postgres.

## Build Sequence

See [docs/CHAPTERBOOK.md](docs/CHAPTERBOOK.md) for the 26-chapter build plan.

## Local Development

- No Docker required
- Python 3.12+ for backend
- Node.js 20+ for frontend
- Supabase project credentials in `.env`

## Warning

Agents cannot directly execute tools. All tool calls route through the Tool Broker. This is a development project — agents must never bypass the Policy Kernel, Tool Broker, or Action Ledger.

## License

Proprietary — All rights reserved.
