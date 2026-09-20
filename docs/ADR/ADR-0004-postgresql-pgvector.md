# ADR-0004: PostgreSQL and pgvector persistence

Status: accepted

PostgreSQL 18 is the system of record for research runs, the SecurityMaster, evidence, thesis
history, and later evaluation data. SQLAlchemy 2 provides the application persistence boundary,
asyncpg provides asynchronous access, and Alembic owns schema evolution. pgvector shares the
same database for the later secure-RAG phase so transactional metadata and vector references do
not split across independent stores.

SQLite is permitted only for fast local boundary tests. It does not qualify PostgreSQL-specific
migrations, pgvector behavior, concurrency, or production data semantics. Phase 3 closes only
after the migration is exercised against the Docker Compose PostgreSQL/pgvector service.
