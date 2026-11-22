# Contributing

## Development setup

- Use Python 3.12 or newer.
- Install dependencies with `uv pip install -r requirements.txt`.
- Run `pytest -q` and `ruff check <changed files>` before submitting changes.
- Use PostgreSQL and Redis for integration behavior; do not introduce SQLite or MongoDB.

## Change rules

- Make schema changes with Alembic revisions only.
- Keep presentation commands in cogs and durable logic in services/repositories.
- Every guild-scoped feature must validate the guild ID.
- Add focused tests for behavior and regressions.
- Update `docs/PROGRESS.md`, `docs/COMPLIANCE_CHECKLIST.md`, and relevant manual-test documentation.
