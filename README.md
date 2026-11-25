# Junior Atlas

Junior Atlas is a modular, multi-guild Discord bot. It provides moderation, security,
server logging, welcome/goodbye automation, verification, role management,
tickets, economy, leveling, achievements, games, community features, voice
utilities, music, ARQ background work, and operator health tooling.

Junior Atlas keeps Discord-specific presentation thin and uses PostgreSQL as
the durable source of truth. Redis provides cache and coordination support;
it can degrade gracefully without PostgreSQL and does not replace PostgreSQL.

## Project status (audit snapshot: 2026-11-23)

This repository is under active development and is **not** a production-complete
release. Status terms are used consistently across this README and the documents
in `docs/`:

- **Implemented and tested** — code exists and automated unit/regression tests
  exercise the behavior. Live Discord integration is still required before
  claiming production readiness.
- **Implemented but not integration-tested** — code exists, but only external
  services or a live Discord guild can validate it end to end.
- **Partially implemented** — a working subset exists; the remaining behavior is
  explicitly listed as a limitation.
- **Planned** — designed or catalogued, but no production implementation exists.
- **Not implemented** — not present in the runtime.

| Area | Status | Notes |
|---|---|---|
| Configuration and startup validation | Implemented and tested | Missing `DISCORD_TOKEN` now fails with an actionable error. |
| PostgreSQL/Redis infrastructure, migrations, health endpoints | Implemented and tested | Migration execution requires a reachable database. |
| Moderation core (warn/case/timeout/ban/kick/clear) | Implemented and tested | Live permission and audit-log behavior needs a real guild. |
| Server logging | Implemented and tested | Listener wiring and persistence covered by tests. |
| AutoMod core rules and escalation | Partially implemented | Catalog-only rules remain disabled; see `docs/EXTREME_HARDENING.md`. |
| Welcome/goodbye and rules panel | Implemented and tested | Previously published rules panels must be republished after the rebrand. |
| Verification, role menus, temporary roles | Partially implemented | Persistence and views exist; full live flows are not integration-tested. |
| Tickets | Partially implemented | Core lifecycle and V16 metadata exist; add/remove/staff workflows remain incomplete. |
| Anti-nuke and recovery | Partially implemented | Selected destructive-action defenses exist; many catalog capabilities are disabled. |
| Economy ledger | Implemented and tested | Service-level ledger and locking tested; Discord shop UI is incomplete. |
| Leveling and achievements | Implemented and tested | Math, ranks, and achievement records tested. |
| Games (tic-tac-toe, RPS, trivia) | Implemented and tested | No wagering. |
| Community/collection/voice/giveaways | Partially implemented | Several foundation models and commands; full workflows are planned. |
| Music | Implemented but not integration-tested | Requires an external Lavalink v4 node. |
| Gateway queue, sharding, scheduler, ARQ jobs | Implemented and tested | Multi-process chaos testing against real Redis/PostgreSQL remains required. |
| Dashboard/control center | Planned (deferred) | Disabled by default; not part of the supported bot runtime. |
| Dashboard production UI/API | Planned | Do not treat the preview scaffolds as operational. |

## Dashboard status: deferred and disabled

Dashboard development is postponed. `DashboardAPI` is **not** started during
normal bot startup, and the bot starts without `DASHBOARD_API_KEY` or any
dashboard credentials.

- `DASHBOARD_ENABLED=false` by default.
- `bot/web/api.py` is retained in isolation for future work.
- `control-center/`, `control_center_api/`, and `control-center-api/` are
  preview scaffolds, not part of the bot runtime.
- Liveness and readiness endpoints (`/healthz`, `/readyz`) remain active through
  the separate health server.


## Technology

- Python 3.12+
- discord.py 2.x
- PostgreSQL 17+
- SQLAlchemy 2 async and asyncpg
- Alembic migrations
- Redis 8
- ARQ background workers
- Pydantic and pydantic-settings
- pytest and pytest-asyncio
- Ruff
- Docker and Docker Compose
- Optional Wavelink/Lavalink v4 music

## Implemented modules

### Configuration

- Per-guild prefix and core settings
- `/config show`
- `/config prefix`
- `/config mod-log`
- `/config mod-role`
- `/prefix show`, `/prefix set`, and `/prefix reset`
- Slash and configurable prefix interfaces
- Pydantic environment validation
- Health (`/healthz`) and readiness (`/readyz`) endpoints
- Dashboard API disabled by default; see “Dashboard status” above

### Moderation

- `/warn`
- `/warnings`
- `/timeout`
- `/ban`
- `/kick`
- `/clear`
- `/purge` through the prefix/text surface
- `/slowmode`
- `/lock`
- `/unlock`
- `/v16 temp-timeout`
- Permanent warning records and warning counts
- Per-guild moderation cases
- Race-safe per-guild case IDs
- Role hierarchy and bot-permission validation
- Reason and mod-log support
- Confirmation utilities for sensitive operations

### Server logging

- `/logs channel`
- `/logs toggle`
- `/logs privacy`
- `/logs exempt`
- Message delete/edit
- Member join/leave/update
- Role create/update/delete
- Channel create/update/delete
- Voice-state changes
- Ban/unban events
- Moderation event records
- Privacy-conscious opt-in message content
- Capped and retained persisted log content
- Exempt-channel support
- Redis cache with PostgreSQL fallback

### AutoMod

- `/automod rule`
- `/automod exempt-role`
- `/automod exempt-channel`
- `/automod word`
- `/automod link-domain`
- `/automod escalation`
- Spam and repeated-message detection
- Mention and invite-link detection
- Blocked words with word-boundary matching
- Allow/deny link-domain rules
- Emoji, caps, and message-length limits
- Role/channel exemptions
- Warn, timeout, kick, and delete escalation actions
- Bots, owners, administrators, manage-guild/manage-message members, and
  members above the bot are protected from enforcement
- Redis windows with PostgreSQL/local fallback
- Violation and message-fingerprint records

### Welcome, goodbye, and verification

- Welcome/goodbye channel configuration
- Static and GIF banner support
- Custom embed title, description, color, footer, and image fields
- Placeholder templates for member, guild, invite, account-age, boost, and ID data
- Advanced welcome engine with deduplication and delivery retries
- Autorole and welcome buttons
- Persistent rules-panel role buttons
- Persistent verification button infrastructure
- Verified-role, rules-text, and verification-log persistence
- Persistent role-menu/select infrastructure
- Temporary-role assignment and expiry records
- Role-hierarchy and managed/elevated-role safeguards

### Tickets

- `/ticket` to open a support ticket
- `/ticket-panel` to create a persistent ticket button panel
- Persistent `TicketPanel`, `Ticket`, and `TicketMessage` records
- Open, claimed, closed, and reopened state transitions
- Opening/claim/close controls attached to ticket channels
- Strict `@everyone` denial plus opener/staff/bot permissions
- Staff category/support-role routing
- Ticket transcripts stored for export
- V16 ticket claim, priority, notes, rating, transcript, reopen, and statistics adapters
- Illegal state-transition tests

### Security and anti-nuke

- Anti-raid join tracking
- Redis sliding windows
- Automatic and manual lockdown
- Quarantine and member role recovery
- Security-state snapshots
- Channel, role, webhook, ban, kick, permission, and destructive-action detection
- Audit-log actor resolution with Discord latency tolerance
- Threshold plus confidence safeguards
- Owners and administrators are trusted and never quarantined by anti-nuke logic
- Automated containment is limited to a second threshold with sufficient confidence
- Security event timeline for manual and automated actions
- `/v16` status, help, validate, snapshot, restore, security-log, unlockdown,
  unquarantine, security-backup, and lockdown controls

### Economy

- `/balance`
- `/daily`
- Wallet and bank balances
- PostgreSQL row-lock balance changes
- Immutable economy transaction ledger
- Idempotency keys and duplicate-click protection
- Redis cooldowns with database fallback
- Shop item and inventory schema
- Reusable service foundations for weekly rewards, work, pay, deposit,
  withdraw, and leaderboard operations
- No negative balances
- No gambling or real-money features

### Leveling and achievements

- `/level show`
- `/level rank`
- `/level leaderboard`
- `/level achievements`
- `/level settings`
- `/level channel`
- `/level channel-reset`
- `/level xp-channel`
- `/level xp-add`, `/level xp-remove`, `/level xp-set`
- `/rank`
- Server leaderboard
- Per-character or random message XP
- Per-guild XP cooldown
- Ignored channels and ignored roles
- XP whitelist channels
- Bonus-role multipliers
- Level roles with stack/non-stack behavior
- Cumulative level threshold math
- Automatic level-up announcements
- Achievement definitions and member unlock records

### Games

- `/engage tictactoe`
- `/engage rps`
- `/engage trivia`
- Tic-Tac-Toe engine and 3x3 button board
- Rock-Paper-Scissors simultaneous choices
- Trivia multiple-choice view
- Illegal-move and occupied-square protection
- Turn validation and timeout-safe views
- Game session and game-stat models
- No wagering or gambling

### Collection and community

- `/engage collect`
- `/engage tempvoice`
- Guild-scoped collectible catalog
- User collection counts
- Daily collectible cooldown
- Common/rare/epic/legendary-ready rarity field
- Join-to-create temporary voice settings
- Temporary voice ownership and locked state
- Temporary voice cleanup service
- Giveaway model and duplicate-safe entry records
- Poll model and vote storage
- Starboard model
- Suggestions with persistent status
- `/suggest`
- `/engage poll`
- `/engage 8ball`
- `/engage choose`

### Utility and community commands

- `/ping`
- `/health`
- `/remind`
- `/case`
- `/balance`
- `/coinflip`
- `/invite`
- `/inviteleaderboard`
- `/serverinfo`
- `/userinfo`
- `/avatar`
- `/banner`
- `/play`, `/skip`, `/stop`, `/pause`, `/resume`, `/queue`, `/music-status`
- Prefix aliases for many community and moderation commands
- Safe command-prefix per guild
- Consistent Junior Atlas embed theme
- Ephemeral private responses where appropriate

### Music

- Optional Lavalink/Wavelink playback
- Play/skip/stop/pause/resume/queue/status commands
- Music remains unavailable by default until Lavalink is configured
- Lavalink URL/password stay in environment configuration only

### V16 compatibility

- `/v16` and `,v16` hybrid capability surface
- Persistent feature flags
- Security timeline
- Scheduled actions
- Warning expiration/points
- AutoMod rule persistence
- Member profiles, reputation, and playlists
- Ticket metadata
- Configuration snapshots and restore
- Catalog-only capabilities remain disabled rather than falsely reported as implemented

## Architecture

```text
Discord presentation
  -> application services
  -> repositories
  -> SQLAlchemy async models
  -> PostgreSQL

Redis provides cache, cooldown, lock, sliding-window, and temporary coordination.
ARQ provides maintenance jobs and scheduled background work.
```

Main directories:

- `bot/commands` - Discord cogs, slash commands, prefix commands, and views
- `bot/services` - reusable guild-scoped business logic
- `bot/repositories` - SQL and row-lock operations
- `bot/models` - feature-domain SQLAlchemy models
- `bot/core` - configuration, database, health, logging, gateway, and shutdown
- `bot/cache` - Redis cache, single-flight, and rate limiting
- `bot/workers` - gateway, greetings, scheduler, and ARQ workers
- `alembic/versions` - append-only database migrations
- `tests` - unit, integration, and regression coverage
- `docker/` and `deploy/` - container and deployment support
- `scripts/` - backup, build, restore, startup, and secret-scan utilities

## Prerequisites

- Python 3.12 or newer
- PostgreSQL 17 or newer
- Redis 8 or newer
- Docker and Docker Compose
- A Discord application and bot
- Server Members and Message Content privileged intents for the relevant features

## Discord application setup

1. Create an application and bot in the Discord Developer Portal.
2. Enable Server Members and Message Content privileged intents.
3. Configure required moderation, channel, role, voice, webhook, audit-log, and
   message permissions.
4. Generate an invite with slash-command permissions.
5. Supply the bot token and application environment variables.
6. Start migrations before starting the Discord gateway.
7. Synchronize slash commands after deployment.

Application commands are registered in exactly one scope: **global**. Startup
syncs the global tree and removes stale global definitions. When `GUILD_ID` is
set, startup also cleans up stale guild-scoped copies left by older releases;
it never copies the global tree into that guild, because that produces duplicate
slash commands in Discord. To audit live registrations before or after a
deployment, run `python -m scripts.audit_commands --check-local` and use its
opt-in guild cleanup flags if stale guild commands are found.

## Required and optional environment variables

Required application variables:

Required to start a usable Discord session:

- `DISCORD_TOKEN` (startup fails with a clear error when missing)

Required for any non-local deployment (defaults point at `localhost`):

- `DATABASE_URL` (`postgresql+asyncpg://`; `postgresql://` and `postgres://` are normalized)
- `REDIS_URL` (`redis://` or `rediss://`)

Recommended variables:

- `BOT_OWNER_IDS`
- `LOG_LEVEL`
- `ENVIRONMENT`

Important optional variables:

- `COMMAND_PREFIX`
- `GUILD_ID`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `DB_USE_PGBOUNCER`
- `SHARD_COUNT`
- `SHARD_IDS`
- `INSTANCE_ID`
- `DASHBOARD_ENABLED` (default `false`; dashboard is deferred)
- `DASHBOARD_HOST`
- `DASHBOARD_PORT`
- `DASHBOARD_API_KEY` (only needed if the deferred dashboard is explicitly enabled)
- `LAVALINK_URL`
- `LAVALINK_PASSWORD`
- `OTEL_ENABLED`
- `OTEL_SERVICE_NAME`
- `OTEL_EXPORTER_OTLP_ENDPOINT`

See `.env.example` for the full, validated list. Empty optional values are
normalized (`SHARD_COUNT=`, `INSTANCE_ID=`, and `GUILD_ID=0` are treated as unset).

Never commit `.env`, Discord tokens, database passwords, Redis credentials,
API keys, or Lavalink passwords.

## Local setup

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env
# Edit only the local .env file.
pytest -q
python scripts/secret_scan.py
```

## Docker setup

```bash
cp .env.example .env
# Set real POSTGRES_PASSWORD and Discord credentials locally.

docker compose up -d postgres redis
docker compose up -d migrate
docker compose up -d bot worker
```

PostgreSQL uses `postgres_data`; Redis uses `redis_data`.

The Compose stack includes:

- PostgreSQL
- Redis
- PgBouncer
- Migration service
- Junior Atlas bot
- ARQ worker
- OpenTelemetry collector

## Alembic migrations

```bash
alembic upgrade head
alembic current
alembic history
```

Every schema change must use an Alembic revision. Do not use `create_all()` or
`drop_all()` for production schema changes.

## Development

```bash
pytest -q
ruff check .
python -m compileall -q bot
python scripts/secret_scan.py
pip check
docker compose config
docker compose build
```

Tested milestones include foundation/configuration, moderation cases, server
logging, AutoMod boundaries, tickets, anti-nuke safeguards, economy ledger,
level/achievement math, and game engines.

## Health and reliability

- `/health` reports PostgreSQL, Redis, and Discord gateway readiness.
- `/readyz` reports dependency readiness with HTTP 503 on degradation.
- `/healthz` remains a process liveness endpoint.
- Redis outages fall back to PostgreSQL or local bounded state.
- PostgreSQL outages produce clear dependency failures rather than crash-loops.
- Gateway events use bounded queues, guild serialization, and shard fencing.
- Scheduled jobs use database claims and stale-claim recovery.
- ARQ cleanup jobs cover logs, AutoMod fingerprints, temp roles, and maintenance.

## Security

Security boundaries include:

- No secrets in Discord replies or application logs
- Ephemeral private command output
- Audit-log input handling
- Role-hierarchy and bot-permission checks
- Owner/admin anti-nuke trust
- Configurable thresholds and confidence
- Channel exemptions and bot exemptions
- Retention-limited message content
- Redis/PostgreSQL degradation handling
- `scripts/secret_scan.py` for repository secret-name/value-pattern checks

See [SECURITY.md](SECURITY.md) for reporting.

## Backup and restore

Linux scripts are available in `scripts/backup.sh` and `scripts/restore.sh`.
Review and test restore procedures against a separate database before using
them in production.

## Known limitations

- **Licensing blocker:** upstream FALLEN has no license, so this derivative is
  All rights reserved and must not be publicly redistributed without written
  permission. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
- Live Discord login requires credentials supplied by the repository owner.
- Discord slash commands are subject to Discord's global command limit.
- Advanced M5-M10 features are foundations/checkpoints and require live-server testing.
- Real Giveaway reroll, full temp-voice ownership controls, and some M10 workflows
  remain manual checkpoints rather than a complete production UI.
- The dashboard is deferred and disabled by default. The preview scaffolds are
  not supported runtime components.
- Previously published rules-panel messages use the old custom-ID prefix and
  must be republished once after the rebrand. Existing ticket channels remain
  readable through legacy topic compatibility.
- Lavalink requires an external provider.
- Translation providers require explicit configuration.
- Rank-card images require an optional image-generation path.
- `downgrade base` is destructive and was not executed without approval.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Specification summary](docs/SPEC.md)
- [Feature matrix](docs/FEATURE_MATRIX.md)
- [Audit (historical Stage 0 + current addendum)](docs/AUDIT.md)
- [Compliance checklist](docs/COMPLIANCE_CHECKLIST.md)
- [Progress (historical log + current status)](docs/PROGRESS.md)
- [Final report (historical snapshot)](docs/FINAL_REPORT.md)
- [Manual tests](docs/MANUAL_TESTS.md)
- [License status](LICENSE)
- [Notice and attribution](NOTICE.md)

## Attribution

Junior Atlas is derived from [FALLEN](https://github.com/NOAH-NULL/FALLEN),
copyright (c) 2026 NOAH-NULL and FALLEN contributors.

The upstream repository contains no LICENSE, COPYING, or NOTICE file and no
license metadata. Under copyright law that means the upstream work is
**All rights reserved**; this derivative cannot be relicensed or publicly
distributed without written permission from the upstream copyright holder.
The full finding and required follow-up action are documented in
[LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
