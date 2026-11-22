# Stage 0 Audit

## Baseline

- Repository: `NOAH-NULL/FALLEN`
- Baseline branch/worktree: `junior-atlas`, clean before audit
- Upstream remote preserved: `https://github.com/NOAH-NULL/FALLEN.git`
- Baseline runtime: Python 3.12.16 via uv
- `discord.py`: 2.7.1
- SQLAlchemy: 2.1.9
- Alembic: 1.20.1
- PostgreSQL: container-backed PostgreSQL 17
- Redis: container-backed Redis 8
- Baseline tests: **346 passed, 8 failed** (354 total)
- Baseline Ruff: **244 errors** (169 fixable)

## Runtime and dependency findings

| Area | Status | Notes |
|---|---|---|
| Python floor | Partial | `pyproject.toml` permits Python 3.11, below the required 3.12 minimum. |
| Dependency versions | Missing | Requirements use lower/upper ranges rather than a lock or a pinned, verified set. |
| Pydantic Settings | Partial | Pydantic is installed, but `bot/core/config.py` uses dataclass plus `os.getenv`, not Pydantic Settings. |
| ARQ | Missing | No ARQ dependency or worker implementation found. |
| PostgreSQL | Met | Async SQLAlchemy/asyncpg and Alembic are present. |
| Redis | Partial | Redis integration exists, but configuration and fallback behavior need M0 hardening. |
| Discord.py | Met | Discord.py 2.x is pinned to a compatible major range. |
| Docker | Partial | Compose has PostgreSQL, Redis, PgBouncer, bot, migration, and observability services; no dedicated test database is configured. |

## Architecture findings

- The repository has `bot/commands`, `bot/services`, `bot/models`, `bot/core`, `bot/cache`,
  `bot/workers`, `bot/web`, and tests, so the major layer boundaries exist.
- Discord cogs and command modules contain substantial business logic in places; M0-M11
  should move guild-scoped operations behind application services and repositories.
- No raw `create_all()` or `drop_all()` usage was found in bot/Alembic code. Alembic is the
  migration path, and the baseline migration chain reaches revision `0018_guild_command_prefix`.
- The 18 revisions are append-only and are reported by Alembic as one linear head.
- Guild configuration includes a `command_prefix` field, but `Settings.command_prefix` is
  hardcoded to `,` and needs per-guild environment-independent validation in M0.
- The gateway queue, shard lease, and distributed worker infrastructure is substantial.
  Retain only after M0 test/documentation review.

## Module audit

| Module | Status | Evidence |
|---|---|---|
| Moderation | Partial | Existing moderation commands, warnings, cases, locks, and purge/timeout code exist; races, hierarchy, centralized permissions, and tests require M1 hardening. |
| Server logging | Partial | Service/listener paths exist, but configuration and event coverage require M2 completion. |
| AutoMod | Partial | Existing automod and heat logic exist; guild settings, false positives, and escalation require M3 completion. |
| Welcome/verification/roles | Partial | Greetings, rules, role menus, and welcome engine exist; button verification and temporary roles need M4 completion. |
| Tickets | Partial | Ticket commands/services/models exist; strict permissions, state transitions, transcripts, and cleanup require M5 completion. |
| Security/anti-nuke | Partial | Anti-raid, quarantine, lockdown, snapshots, and security event code exist; thresholds and recovery safeguards require M6 hardening. |
| Economy | Partial | Basic economy/coinflip-adjacent code exists, but M7 requires ledger, locking, idempotency, and shop/transactions. |
| Leveling | Partial | XP, levels, roles, and leaderboards exist; M8 needs Redis cooldown and rank-card hardening. |
| Games | Partial | Limited text and interaction games exist; M9 needs full engines, Redis sessions, and result history. |
| Community/utility | Partial | Suggestions, polls, 8ball, choose, coin flip, custom commands, and utility commands exist. Coin flip is harmless and has no wagering. |
| Voice | Partial | Music is present and default-off configuration exists; join-to-create voice requires M10. |
| Giveaways | Partial | Model/service paths exist; M10/M11 need winner, reroll, eligibility, and expiry-job completion. |
| Background jobs | Partial | Custom scheduler/workers exist; M11 ARQ standardization is required. |

## Duplicate, dead, and cleanup findings

- Committed archive: `Fallen-v1.2-uwuify.zip`.
- Duplicate dashboard implementations/directories:
  `control-center/` and `control_center_api/` versus `control-center-api/`.
- The control API must be audited in M0 to determine whether it remains local-only and
  authentication-key protected.
- Music support depends on Lavalink/Wavelink and should remain optional/default-off.
- Licensing: no repository `LICENSE` file was found.
- Missing repository files: `NOTICE.md`, `SECURITY.md`, `CONTRIBUTING.md`, and
  `CHANGELOG.md` for M0; `AUDIT.md`, `SPEC.md`, checklist, and progress log for Stage 0.

## Security and secret review

- No `.env` file is present in the worktree.
- `.env.example` contains placeholders and variable names only.
- The secret-pattern count in tracked text, excluding `.env.example`, was 7. These matches
  require M12 manual review because broad variable-name matching can include code constants.
- Git history name scan found `.env.example` files in historical trees, not a secret-bearing
  `.env` file. No secret values were printed or committed during this audit.
- The control API has a key setting and should remain bound to `127.0.0.1` by default.
- Discord startup errors must not expose stack traces or secrets in Discord/log surfaces.

## Windows/Linux findings

- Docker Compose and shell scripts cover Linux.
- `scripts/start_windows.ps1` exists for Windows startup.
- Backup/restore shell scripts are Linux-oriented and need Windows documentation in M12.
- The repository ignores `.env` and virtual environments.

## Baseline command output

```text
pytest -q:
346 passed, 8 failed, 1 warning

ruff check .:
Found 244 errors

alembic upgrade head:
0018_guild_command_prefix (head)

PostgreSQL public tables:
25

Redis ping:
PONG

Bot startup without DISCORD_TOKEN:
LoginFailure - improper token
```

The bot startup test used an empty token only; no real Discord credentials are available.
