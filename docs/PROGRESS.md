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
