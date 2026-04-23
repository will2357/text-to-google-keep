-- Local PostgreSQL role + dev database for text-to-google-keep (Django ttgk).
-- Run as superuser (psql meta-commands require the psql client):
--   psql -U postgres -v ON_ERROR_STOP=1 -f scripts/postgres-local.sql
--   sudo -u postgres psql -v ON_ERROR_STOP=1 -f scripts/postgres-local.sql
--
-- Safe to re-run: aligns password with .env.example (ttgk_local) and creates ttgk_dev if missing.

DO $setup$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ttgk') THEN
    CREATE ROLE ttgk WITH LOGIN PASSWORD 'ttgk_local' CREATEDB;
  ELSE
    ALTER ROLE ttgk WITH LOGIN PASSWORD 'ttgk_local' CREATEDB;
  END IF;
END
$setup$;

SELECT format('CREATE DATABASE %I OWNER %I', 'ttgk_dev', 'ttgk')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'ttgk_dev')
\gexec
