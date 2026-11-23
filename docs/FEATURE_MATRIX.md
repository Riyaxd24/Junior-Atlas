# Junior Atlas V16 — exact 100 capability matrix

This matrix is a **catalog**, not an implementation claim. Only entries in the runtime's
`IMPLEMENTED_FEATURES` allowlist are active. Maturity values use the project status
vocabulary from the README. See `docs/EXTREME_HARDENING.md` for the current list of
intentionally disabled capabilities.

| # | Domain | Capability | Runtime owner | Maturity |
|---:|---|---|---|---|
| 1-15 | Security | anti-bot, account age, suspicious names, raid rate, lockdown/recovery, deletion/webhook/permission/mass-ban protection, timeline, trusted admins, emergency lock, backup | `bot/services/v16_runtime.py`, `ExtremeService` | Partial: join heuristics, deletion bursts, lockdown/recovery are implemented; webhook/permission-escalation/mass-ban/trusted-admin entries are not |
| 16-30 | Moderation | temporary/scheduled punishments, warning expiry/points, escalation, notes, case tools, reports, approvals, statistics | `ModerationService`, `ExtremeService`, scheduler | Partial: warnings, cases, scheduled punishments, expiry, statistics foundations exist; reports/approvals are not implemented |
| 31-40 | AutoMod | regex, duplicate/flood/emoji/sticker/attachment, domain allow/deny, mention spam, custom actions | `V16Runtime`, `AutoModRule` | Partial: duplicate/flood/emoji/caps/length/mentions/invites/domains/words exist; sticker/attachment and some catalog actions are not implemented |
| 41-50 | Leveling | voice/activity XP, boosters/multipliers, weekends, seasons, prestige, rank customization, level-up behavior | `LevelService`, V16 settings | Partial: message XP, multipliers, roles, announcements, achievements exist; voice XP/seasons/prestige/rank cards are not implemented |
| 51-60 | Community | reputation, profiles, badges/colors, birthdays, anniversaries, milestones, challenges, quests, achievements | `ExtremeService`, profile/reputation models | Partial: profiles, reputation, playlists, achievements exist; birthdays/milestones/quests are not implemented |
| 61-70 | Engagement | rewards, streaks, trivia, word/number/reaction games, tournaments, voting, challenges, events | engagement commands/services + V16 settings | Partial: tic-tac-toe, RPS, trivia, polls, collectibles exist; tournaments/events are not implemented |
| 71-80 | Music | DJ/permissions, queues/presets, personal/server playlists, autoplay/recovery/persistence/history | music adapter + playlist persistence | Partial: optional Lavalink playback and playlist persistence exist; DJ/presets/autoplay are not implemented |
| 81-90 | Tickets | categories/forms/claiming/priority/transcripts/ratings/statistics/auto-close/staff notes/reopen | `TicketService`, V16 ticket model | Partial: panels, claim/close/reopen, priority, notes, transcripts, ratings/stat foundations exist; forms/auto-close/staff assignment are incomplete |
| 91-100 | Administration | snapshots/import-export/setup, permission/hierarchy/channel checks, health/diagnostics/validation, backup/restore | `ExtremeService`, core health, snapshots | Partial: snapshots, validation, health, backup/restore foundations exist; import/export and full diagnostics are not implemented |

The numbered list is a capability catalog, not a claim that every item is currently implemented. Check the runtime's implemented-feature allowlist before treating a capability as active. Capabilities that require an external provider (for example actual Lavalink audio playback) remain provider adapters rather than fake local implementations.
