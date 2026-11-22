# Compliance Checklist

Status: `[x]` implemented and verified, `[~]` partial, `[ ]` missing.

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
- [~] License and repository policy documents.

## M1-M11

M1 moderation: `[~]` existing moderation surfaces plus race-safe per-guild case IDs; remaining
M1 command and history hardening is in progress.

M2 server logging: `[x]` per-guild settings, privacy, exempt channels, retention, and
message/member/role/channel/voice/ban/unban listeners are implemented and tested.

All Module D through K, M, N, and L work remains `[ ]` until implementation and testing.

## M12

- [ ] Full test matrix.
- [ ] Security review and secret scan.
- [ ] Docker finalization.
- [ ] Complete documentation and final report.
