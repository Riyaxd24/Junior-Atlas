# Changelog

## Unreleased

### Audit and repair (2026-11-23)

- Restored `LICENSE` and `NOTICE.md` with the accurate upstream licensing finding and
  preserved FALLEN attribution.
- Rebranded active runtime, tests, scripts, and deferred dashboard scaffolds to Junior Atlas.
- Disabled the dashboard during bot startup by default and preserved health/readiness.
- Removed duplicate environment entries, corrected `OTEL_SERVICE_NAME`, and added settings
  validation plus a clear missing-token startup error.
- Reconciled status documentation and marked historical audit reports.

### Stage 0

- Added a reproducible audit, compliance checklist, progress log, specification summary,
  and FALLEN attribution.

### M0

- Added Pydantic Settings validation and pinned Python dependencies.
- Added `/config` guild settings commands and guild settings migration.
- Ported the central palette, embed utilities, paginator, confirmation view, and permissions.
- Preserved Redis cache fallback and invalidation behavior.
