-- Local PostgreSQL role + dev database for text-to-google-keep (Django ttgk).
-- Run as a superuser, e.g.:
--   psql -U postgres -v ON_ERROR_STOP=1 -f scripts/postgres-local.sql
--   sudo -u postgres psql -v ON_ERROR_STOP=1 -f scripts/postgres-local.sql
--
-- Defaults match ttgk/settings.py and .env.example:
--   user:     ttgk
--   password: ttgk_local
--   dev db:   ttgk_dev
-- manage.py test creates/drops DB named ttgk_test (see DB_TEST_NAME); role needs CREATEDB.

CREATE ROLE ttgk WITH LOGIN PASSWORD 'ttgk_local' CREATEDB;
CREATE DATABASE ttgk_dev OWNER ttgk;
