-- init.sql — Runs once when the Postgres container is first created.
-- Enables the pgvector extension so vector columns work.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- for uuid_generate_v4()