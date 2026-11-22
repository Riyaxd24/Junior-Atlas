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

## M1

1. Create multiple moderation cases quickly for the same guild and confirm case numbers are
   contiguous and unique within that guild.
2. Test ban/kick/timeout hierarchy conflicts with the server owner, self, and a higher-role member.
3. Add warnings, inspect `/warnings`, and confirm only active warning points are counted.
4. Run `/clear` in a text channel and confirm purge limits and Manage Messages permissions.

## M2

1. Run `/logs channel` for message delete/edit and member join/leave events.
2. Delete and edit messages, join/leave a member, update roles/channels, and verify embeds contain
   IDs and timestamps.
3. Enable message content logging, send a bot-authored message, and confirm its content is not
   retained.
4. Exempt a channel and confirm no log record or delivery occurs there.
5. Set retention to a short period and run the cleanup path to confirm expired rows are removed.

## M3

1. Enable a blocked-word rule and verify normal words containing the pattern are not false-positive
   matches.
2. Enable the invite filter and confirm a complete Discord invite is detected while `discord.gg`
   alone is ignored.
3. Configure allow and deny link domains and verify the allow rule takes precedence.
4. Configure a timeout escalation and confirm a member is never acted on above the bot's role.

## M4

1. Post a verification panel and confirm the verified role is below the bot's highest role.
2. Accept verification and confirm only one role is added and repeated clicks remain safe.
3. Create a role menu and confirm role additions/removals honor exclusivity and hierarchy.
4. Assign a temporary role and confirm it is removed after the configured expiry.

## M5

1. Post a ticket panel and open a ticket; confirm only the creator, support role, and bot can
   view it.
2. Claim and close a ticket, then reopen it and confirm illegal transitions are rejected.
3. Create a transcript and confirm message authors and content are stored without exposing
   secrets or tokens.

## M6

1. Create a single channel or role deletion event and confirm it alerts only, not quarantine.
2. Reproduce the configured destructive threshold and confirm owner and administrator actors
   are never quarantined or locked down.
3. Exercise rapid deletes with audit attribution and confirm quarantine/lockdown can be unlocked
   from the preserved snapshot.

## M7

1. Claim daily/work/weekly and confirm each reward is recorded once and cooldown prevents duplicate
   clicks.
2. Deposit and withdraw coins and confirm wallet and bank totals remain non-negative.
3. Pay another member repeatedly with the same interaction and confirm no duplicate debit/credit.
4. Inspect the economy leaderboard and transaction ledger after transfers.

## M8

1. Send messages and confirm XP gains respect ignored channels/roles and cooldown.
2. Cross a level threshold and confirm the level-up reward and achievement unlock occur once.
3. Run `/level leaderboard`, `/level rank`, and `/level achievements` for a test member.

## M9

1. Start `/engage tictactoe` with a member and confirm only the two players can move.
2. Confirm illegal and occupied moves are rejected and a three-in-a-row wins.
3. Start `/engage rps` and confirm choices remain private until both players submit.
4. Start `/engage trivia` and confirm correct/incorrect answers resolve once.

## M10

1. Run `/engage collect` twice quickly and confirm only one daily collectible is granted.
2. Configure a join-to-create voice hub and confirm joining creates and occupies a temp channel.
3. Leave the temp channel empty and confirm it is cleaned up.
4. Create a poll and confirm existing community utility commands remain responsive.

## M11

1. Start the ARQ worker service and confirm `ping` returns `pong`.
2. Stop Redis and confirm the worker reports degraded Redis while database cleanup remains usable.
3. Run cleanup jobs twice and confirm the second run removes no duplicate rows.
4. Schedule a reminder and confirm it remains delivered once despite scheduler restart.
