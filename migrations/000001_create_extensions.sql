-- Migration: 000001_create_extensions
-- Created: 2026-06-24
-- Description: Enable required PostgreSQL extensions

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
