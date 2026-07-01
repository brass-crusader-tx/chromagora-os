# Database Conventions

## Primary Keys
```sql
id uuid PRIMARY KEY DEFAULT gen_random_uuid()
```
Never use serial or auto-increment. UUIDs are globally unique and safe for distributed systems.

## Tenant Isolation
All tenant-scoped tables include:
```sql
tenant_id uuid NOT NULL REFERENCES tenants(id)
```
With RLS policy:
```sql
USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
```

## Timestamps
```sql
created_at timestamptz NOT NULL DEFAULT now(),
updated_at timestamptz NOT NULL DEFAULT now()
```
`timestamptz` (timestamp with time zone) is always preferred over `timestamp`.

## JSON Data
```sql
payload jsonb NOT NULL DEFAULT '{}'
```
Always use `jsonb` (binary JSON), never `json` (text). JSONB supports indexing and operators.

## Enums
Use CHECK constraints instead of PostgreSQL ENUM types for flexibility:
```sql
status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'archived'))
```
This allows adding new statuses without ALTER TYPE.

## Arrays
PostgreSQL arrays are allowed for simple lists:
```sql
required_documents text[] NOT NULL DEFAULT '{}',
missing_documents text[] NOT NULL DEFAULT '{}'
```

## Indexes
- Every foreign key gets an index
- Status columns get an index when filtered
- Composite indexes for common query patterns (tenant_id + created_at DESC)

## Naming
- Tables: snake_case, plural for entity collections, matching existing migrations.
- Columns: snake_case
- Indexes: idx_{table}_{column}
- Policies: {rule_name} ON {table}

## Triggers
Auto-update `updated_at`:
```sql
CREATE TRIGGER update_{table}_updated_at
    BEFORE UPDATE ON {table}
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```
