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

Status: in progress

### Starting scope

- Preserve and test existing welcome/goodbye placeholder and embed behavior.
- Add persistent button verification with rules acceptance.
- Add button/select role menus with role-hierarchy and exclusivity controls.
- Add temporary-role records and expiry cleanup support.
