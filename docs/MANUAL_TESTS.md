# Manual Tests

## Stage 0

1. Supply a real Discord token and run `python -m bot`.
2. Confirm PostgreSQL and Redis become healthy.
3. Confirm the bot logs in and slash commands register.

## M0

1. Set `BOT_OWNER_IDS` to a comma-separated list and restart; confirm startup validation accepts
   only integer IDs.
2. Run `/config show` in a server and confirm prefix, timezone, moderation log, and moderation
   role are displayed ephemerally.
3. Run `/config prefix` and confirm the per-guild prefix changes.
4. Run `/config mod-log` and `/config mod-role`; verify role hierarchy and channel behavior.
5. Stop Redis temporarily and confirm guild configuration reads fall back to PostgreSQL.
6. Stop PostgreSQL temporarily and confirm the health endpoint reports degraded state rather than
   crashing the process.
