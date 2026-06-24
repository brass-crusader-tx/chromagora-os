# Web — Next.js Frontend

The Chromagora OS Operator Cockpit frontend.

## Stack
- Next.js 15+ (App Router)
- TypeScript
- Supabase (@supabase/supabase-js) for auth and data
- Tailwind CSS (when added)

## Routes (planned)
```
/businesses          — list and manage client businesses
/businesses/[id]     — business detail
/businesses/[id]/twin — business twin editor
/command             — command feed (events)
/approvals           — approval inbox
/agents              — agent workforce
/opportunities       — opportunity war room
/ledger              — action ledger
/settings            — settings
/field               — mobile-friendly field mode
/demo                — demo simulation pages
```

## Running
```bash
cd apps/web
npm install
npm run dev
```
