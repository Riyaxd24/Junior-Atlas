# Junior Atlas Progress

## Stage 0 - Audit and baseline

Status: complete

- Captured the baseline status, audit, and migration head.
- PostgreSQL and Redis were started and healthy.
- Alembic reached `0018_guild_command_prefix`.
- Baseline: 346 tests passed, 8 failed.
- Baseline Ruff: 244 findings.
- No real Discord token was available for live gateway testing.

## M0 - Foundation hardening

Status: complete

- Added Pydantic Settings validation and pinned dependencies.
- Added ARQ compatibility and required environment settings.
- Added `/config`, theme/paginator/confirmation utilities, permissions, Redis fallback, and
  migration `0019_m0_guild_settings`.
- Verification: 359 tests passed, 1 warning.
- Commit: `d891b17 M0: foundation hardening`.

## M1 - Moderation

Status: checkpoint complete

- Added race-safe per-guild moderation case IDs and migration `0020_m1_moderation_cases`.
- Added clear-warning service support and retained existing moderation surfaces.
- Verification: 359 tests passed, 1 warning.
- Commit: `52e1da3 M1: moderation case hardening`.

## M2 - Server logging

Status: complete

- Added guild log settings, privacy settings, exemptions, records, and migration
  `0021_m2_server_logging`.
- Added `/logs` configuration and message/member/role/channel/voice/ban/unban listeners.
- Redis cache degrade-to-database behavior is implemented.
- Verification: 364 tests passed, 1 warning.
- Commit: `e1f6572 M2: server logging`.

## M3 - AutoMod

Status: implementation complete

- Added rule, repetition, mention, invite, blocked-word, link, emoji, caps, and length
  inspection.
- Added `/automod` rule, exemption, word, link-domain, and escalation configuration.
- Added bot/owner/admin/higher-role safety guards and moderation logging tables.
- Migration: `0022_m3_automod`.
- Verification: 370 tests passed, 1 warning; M3 Ruff checks passed.

## M4 - Welcome, verification, and roles

Status: checkpoint complete

- Preserved existing welcome/goodbye engine and rules-panel role controls.
- Added verification, role-menu, role-menu-item, and temporary-role models.
- Added migration `0023_m4_roles_verification`.
- Added persistent verification and role-select views plus temporary-role expiry service.
- Verification: 373 tests passed, 1 warning.

## M5 - Tickets

Status: checkpoint complete

- Added ticket panel, ticket, and transcript models with migration `0024_m5_tickets`.
- Added persistent open/claim/close/reopen controls and strict ticket channel permission setup.
- Replaced the extra top-level close command with controls on the ticket panel.
- Verification: 375 tests passed, 1 warning; M5 migration reached head.

## M6 - Security and anti-nuke

Status: checkpoint complete

- Added threshold-plus-confidence anti-nuke assessment.
- Added trusted owner/admin exemptions and destructive-action integration.
- Preserved audit-log event timelines and lockdown/quarantine recovery.
- Verification: 379 tests passed, 1 warning; M6 Ruff checks passed.

## M7 - Economy

Status: checkpoint complete

- Added wallet/bank columns and an immutable economy transaction ledger.
- Added shop and inventory schema with row-locked balance modifications.
- Added pay idempotency, deposit/withdraw, work/weekly, and leaderboard services.
- Migration: `0025_m7_economy_ledger`.
- Verification: 382 tests passed, 1 warning; M7 Ruff checks passed.

## M8 - Leveling and achievements

Status: checkpoint complete

- Preserved existing cumulative XP math, Redis cooldown, role rewards, rank, and leaderboard.
- Added achievement definitions/member unlocks and migration `0026_m8_achievements`.
- Added `/level achievements` and automatic level/XP unlock evaluation.
- Verification: 385 tests passed, 1 warning; M8 Ruff checks passed.

## M9 - Games

Status: checkpoint complete

- Added game session/stat models and migration `0027_m9_games`.
- Added tested Tic-Tac-Toe, RPS, and trivia engines.
- Added timeout-safe Discord views under `/engage tictactoe`, `/engage rps`, and `/engage trivia`.
- Verification: 392 tests passed, 1 warning; M9 Ruff checks passed.

## M10 - Collection, voice, giveaways, community, and utility

Status: checkpoint complete

- Added collectible, user collection, giveaway entry, temp voice, poll, and starboard models.
- Added migration `0028_m10_community`.
- Added `/engage collect` and `/engage tempvoice` subcommands with Redis cooldown fallback.
- Verification: 394 tests passed, 1 warning; M10 Ruff checks passed.

## M11 - Background jobs and reliability

Status: checkpoint complete

- Added ARQ worker entrypoint and Docker Compose worker service.
- Added ping, log/automod/temp-role cleanup, and database health maintenance jobs.
- Preserved the existing reminder/scheduled-action scheduler.
- Verification: 396 tests passed, 1 warning; M11 worker lint passes.

## M11 - Background jobs and reliability

Status: in progress

### Starting scope

- Add an ARQ worker entrypoint with health startup/shutdown.
- Add idempotent cleanup jobs for server logs, AutoMod fingerprints, temp roles, and old tickets.
- Preserve the existing scheduler for reminders and scheduled moderation actions.
- Add retry/idempotency tests and worker configuration documentation.

## M10 - Collection, voice, giveaways, community, and utility

Status: in progress

### Starting scope

- Add guild-scoped collectible catalog/user collection and daily reward service.
- Add join-to-create temporary voice settings/channels and cleanup service.
- Add giveaway entries and reroll/history persistence.
- Add polls, starboard, reminders, and existing utility surfaces.
- Keep all entry points under existing command groups to respect Discord limits.

## M9 - Games

Status: in progress

### Starting scope

- Add persisted game sessions and per-player/per-game statistics.
- Add tested Tic-Tac-Toe, Rock-Paper-Scissors, and trivia engines/views.
- Expose game commands under the existing `/engage` command group.
- Preserve timeout-safe turn validation and no-gambling behavior.

## M8 - Leveling and achievements

Status: in progress

### Starting scope

- Preserve existing cumulative XP math, Redis cooldown, role rewards, and rank/leaderboard surfaces.
- Add guild achievement definitions and member achievement unlock records.
- Add level/XP unlock evaluation and `/level achievements` listing.
- Add rank-card-safe data helpers for future image rendering.

## M7 - Economy

Status: in progress

### Starting scope

- Centralize wallet/bank balance changes with PostgreSQL row locks and an immutable ledger.
- Add idempotency keys and duplicate-click protection.
- Add pay, work, weekly, deposit, withdraw, shop, inventory, buy, sell, and leaderboard workflows.
- Keep Redis cooldowns and degrade safely to database-backed fallbacks.

## M6 - Security and anti-nuke

Status: in progress

### Starting scope

- Add threshold-plus-confidence anti-nuke assessment for channel/role/ban/kick/raid events.
- Preserve trusted-owner/admin and audit-log safeguards.
- Extend security event persistence for every automated action.
- Preserve reviewable lockdown/quarantine recovery workflows.

## M5 - Tickets

Status: in progress

### Starting scope

- Add persistent ticket panels, tickets, and transcript messages.
- Add open/claimed/closed state transitions.
- Add panel button opening, claim/unclaim, close/reopen, add/remove member controls.
- Preserve strict channel permissions and transcript retention.

## M4 - Welcome, verification, and roles

Status: in progress

### Starting scope

- Preserve and test existing welcome/goodbye placeholder and embed behavior.
- Add persistent button verification with rules acceptance.
- Add button/select role menus with role-hierarchy and exclusivity controls.
- Add temporary-role records and expiry cleanup support.

## M12 - Finalization

Status: in progress

### Starting scope

- Complete README and final architecture/report documentation.
- Add a secret-scanning script that reports only counts and file locations.
- Run pytest, dependency checks, Ruff, Docker build, Compose configuration, and migration current.
- Complete compliance status and known-limitations report.

### Final validation

- Pytest: 396 passed, 1 warning.
- Secret scan: no potential worktree assignments; no secret-like `.env` paths in history.
- Docker image build: `junior-atlas:final` built successfully.
- Docker Compose interpolation/configuration: valid.
- Alembic current: `0028_m10_community` (head).
- Ruff full-repository baseline: 203 findings remaining, primarily pre-existing formatting debt.
- Dependency check: project virtual environment reported only environment-level
  `python-debian`/`nala`/`h11`/`typer` conflicts outside the pinned application requirements.
