-- Migration: 000023_add_lead_contact_fields
-- Created: 2026-06-25
-- Description: Preserve CRM contact email, phone, company, and title separately.

ALTER TABLE leads ADD COLUMN IF NOT EXISTS contact_email text;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS contact_phone text;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS company_name text;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS contact_title text;

UPDATE leads
SET contact_email = customer_contact
WHERE contact_email IS NULL
  AND customer_contact LIKE '%@%';

UPDATE leads
SET contact_phone = customer_contact
WHERE contact_phone IS NULL
  AND customer_contact IS NOT NULL
  AND customer_contact NOT LIKE '%@%';
