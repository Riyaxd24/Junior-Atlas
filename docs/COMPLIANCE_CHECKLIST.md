# Compliance Checklist

Status: `[x]` implemented and verified, `[~]` partial, `[ ]` missing.

## Audit and repair (2026-11-23)

- [x] Upstream FALLEN repository inspected; no license file or metadata found.
- [x] `LICENSE` and `NOTICE.md` restored with accurate All-rights-reserved status.
- [x] Upstream copyright and repository attribution preserved.
- [~] Public distribution and relicensing remain blocked pending written upstream permission.
- [x] Inherited product branding replaced with Junior Atlas in active runtime code.
- [x] Historical audit records clearly marked and retained.
- [x] `DashboardAPI` no longer starts during normal bot startup.
- [x] Bot starts without dashboard credentials (`DASHBOARD_ENABLED=false`).
- [x] `/healthz` and `/readyz` remain available.
- [x] Duplicate `DB_USE_PGBOUNCER` and related environment entries removed.
- [x] `OTEL_SERVICE_NAME` corrected to `junior-atlas`.
- [x] `pyproject.toml` metadata updated for `junior-atlas`.
- [x] Environment settings validated, with regression tests.
- [x] Missing `DISCORD_TOKEN` produces a clear startup error.
- [x] No new secrets added to tracked files.
- [x] Regression tests added for the audit repairs.
- [ ] Live Discord gateway and slash-command verification (requires a real token).

## Stage 0

- [~] Source-of-truth documents restored; repository `SPEC.md` is now present.
- [x] Clean baseline status captured.
- [x] Runtime, dependencies, and remotes identified.
- [x] Pytest baseline run.
- [x] Ruff baseline run.
- [x] PostgreSQL and Redis containers started and healthy.
- [x] Alembic upgrade head verified.
- [ ] Alembic downgrade/upgrade round trip pending explicit approval.
- [x] Empty-token bot startup failure verified.
- [x] NOTICE attribution added.
- [ ] Archive and duplicate cleanup pending explicit approval.

## M0 - Foundation

- [x] Python 3.12 floor and pinned dependencies.
- [x] Pydantic Settings validation.
- [x] Redis cache invalidation and down behavior.
- [x] Guild configuration service and `/config`.
- [x] Central permission and error layers.
- [x] Theme, paginator, and confirmation utilities.
- [x] PostgreSQL/Redis health and graceful shutdown.
- [x] LICENSE and NOTICE.md restored with accurate upstream licensing status.
- [~] Public distribution/relicensing permission from the upstream copyright holder.

## M1-M11

M1 moderation: `[~]` existing moderation surfaces plus race-safe per-guild case IDs; remaining
M1 command and history hardening is in progress.

M2 server logging: `[x]` per-guild settings, privacy, exempt channels, retention, and
message/member/role/channel/voice/ban/unban listeners are implemented and tested.

M3 AutoMod: `[~]` rule engine, `/automod` configuration, false-positive boundaries, exemptions,
and escalation are implemented; broader integration and Redis sliding-window coverage continue.

M4 welcome/verification/roles: `[~]` existing welcome/goodbye engine retained; verification,
role-menu, and temporary-role persistence infrastructure is implemented, with slash surfaces
consolidated to respect Discord's command limit.

M5 tickets: `[~]` persistent panels/tickets/transcripts, open/claim/close/reopen transitions,
and strict permission construction are implemented; add/remove/staff assignment and cleanup
remain in progress.

M6 security/anti-nuke: `[~]` destructive-action assessment, threshold/confidence safeguards,
trusted owner/admin exemptions, and quarantine/lockdown recovery remain implemented; Redis
sliding windows and full event-stream confidence tuning continue.

M7 economy: `[~]` existing balance/daily workflows plus wallet/bank migration, immutable
transaction ledger, pay/transfer locking, idempotency, deposit/withdraw, work/weekly, and
leaderboard services are implemented; shop inventory and Discord command surfaces continue.

M8 leveling/achievements: `[~]` existing XP math, Redis cooldown, role rewards, rank/leaderboard,
and rank-card data are retained; achievement definitions/unlocks and `/level achievements`
are implemented.

M9 games: `[~]` session/stat schema, tested Tic-Tac-Toe/RPS/trivia engines, timeout-safe Discord
views, and `/engage` subcommands are implemented; remaining multiplayer games continue.

M10 collection/voice/community/utility: `[~]` collectible, giveaway-entry, temp-voice, poll,
starboard, and utility persistence is implemented; full giveaway/voice controls and
additional utility providers continue.

M11 background jobs: `[~]` ARQ worker entrypoint, cron cleanup jobs, health startup/shutdown,
and idempotency tests are implemented; reminder/temp-role/giveaway ARQ execution continues
through the existing scheduler.

All Module D through K, M, N, and L work remains `[ ]` until implementation and testing.

## M12

- [x] Full test suite run; exact counts recorded in the audit final report.
- [x] Security review and secret scan.
- [x] Docker validation performed for this milestone.
- [~] Historical final report retained; reconciled by the audit addendum.
