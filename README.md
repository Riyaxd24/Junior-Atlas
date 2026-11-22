# Junior Atlas

Junior Atlas is a modular, multi-guild Discord moderation and community bot derived from
[FALLEN](https://github.com/NOAH-NULL/FALLEN). It uses discord.py 2.x, PostgreSQL, SQLAlchemy
async, Alembic, Redis, ARQ, Pydantic Settings, and Docker Compose.

## Features

- Moderation actions, warnings, cases, purge, slowmode, lock/unlock, and hierarchy checks
- Configurable server event logging with opt-in message content
- AutoMod filters, exemptions, escalation, and safe defaults
- Welcome/goodbye templates and rules panels
- Verification and role-menu persistence
- Ticket panels, claims, close/reopen state, and transcript records
- Anti-nuke detection, snapshots, quarantine, lockdown, and recovery
- Ledger-based economy, leveling, achievements, and multiplayer game foundations
- Collections, temporary voice channels, giveaways, polls, reminders, and utilities
- ARQ maintenance workers and a resilient gateway worker pool

## Prerequisites

- Python 3.12+
- PostgreSQL 17+
- Redis 8+
- Docker and Docker Compose
- A Discord application with the required bot permissions and gateway intents

## Discord application setup

1. Create a Discord application and bot in the Developer Portal.
2. Enable the Server Members and Message Content privileged intents.
3. Invite the bot with slash-command and required moderation permissions.
4. Supply `DISCORD_TOKEN`, `DATABASE_URL`, `REDIS_URL`, `BOT_OWNER_IDS`, `LOG_LEVEL`,
   and `ENVIRONMENT`.
5. For slash commands, restart or rerun command synchronization after deployment.

## Local setup

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env
# Edit .env locally. Never commit it.
pytest -q
```

## Docker deployment

```bash
cp .env.example .env
# Set real POSTGRES_PASSWORD and Discord credentials in .env.
docker compose up -d postgres redis
docker compose up -d migrate
docker compose up -d bot worker
```

PostgreSQL data is persisted in `postgres_data` and Redis data in `redis_data`.

## Migrations

Migrations are append-only and use Alembic:

```bash
alembic upgrade head
alembic current
```

Do not use `create_all()` or `drop_all()` for schema changes.

## Development

```bash
make test
make lint
python scripts/secret_scan.py
python -m compileall -q bot
```

The full architecture separates Discord presentation, application services, repositories,
database models, infrastructure, workers, and tests.

## Configuration

The main environment variables are:

- `DISCORD_TOKEN`
- `DATABASE_URL`
- `REDIS_URL`
- `BOT_OWNER_IDS`
- `LOG_LEVEL`
- `ENVIRONMENT`
- `COMMAND_PREFIX`
- `POSTGRES_PASSWORD`

The control/dashboard API remains localhost-only by default and is not a public dashboard
phase.

## Music

Music support is optional and disabled when Lavalink is not configured. Do not commit
Lavalink credentials.

## Security

- Never commit `.env`, tokens, passwords, or API keys.
- Redis outages degrade cache/rate-limit behavior; PostgreSQL remains durable truth.
- PostgreSQL outages are reported by health checks rather than crash-loops.
- Sensitive Discord replies are ephemeral where appropriate.
- Destructive moderation and anti-nuke actions require permissions and hierarchy checks.

## Known limitations

- Live Discord integration requires credentials supplied by the repository owner.
- Several advanced M5-M10 features are implemented as foundations/checkpoints and require
  manual server testing before production use.
- Music requires an externally hosted Lavalink v4 node.
- Translation providers require explicit configuration.

## Attribution

Junior Atlas is derived from [FALLEN](https://github.com/NOAH-NULL/FALLEN).
See [NOTICE.md](NOTICE.md) for attribution.
