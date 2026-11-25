# NOTICE

Upstream project: https://github.com/NOAH-NULL/FALLEN

The upstream repository has **no LICENSE, COPYING, or NOTICE file** and no
license metadata (`"license": null` in the GitHub API). A history search found
no license file in any upstream commit. The upstream README references a
license file that does not exist.

Consequently, the upstream work is **All rights reserved**. No open-source
license is granted, and this derivative cannot be relicensed or publicly
redistributed without written permission from the upstream copyright holder.
See [LICENSE](LICENSE) for the full status and the required follow-up action.

## Junior Atlas modifications

Copyright (c) 2026 Junior Atlas contributors. All rights reserved.

The Junior Atlas modifications preserve the upstream architecture (Python,
discord.py, PostgreSQL, Redis, SQLAlchemy, Alembic, and ARQ) while rebranding
the runtime, documentation, and tests.

## Historical audit records

The following documents intentionally retain the name **FALLEN** because they
record the pre-rebrand baseline and upstream provenance. They are historical
records, not current product branding:

- `docs/AUDIT.md` — Stage 0 upstream audit.
- `docs/PROGRESS.md` — historical milestone log.
- `docs/FINAL_REPORT.md` — pre-audit finalization snapshot.
- `Fallen-v1.2-uwuify.zip` — upstream source archive.
- Git history and the preserved `upstream` remote.

Do not remove these records without a separate, explicit decision.

## Principal third-party dependencies

The following packages are used under their respective licenses. The license
text shipped with each installed package is authoritative.

| Dependency | Purpose | License |
|---|---|---|
| discord.py | Discord API client | MIT |
| SQLAlchemy | Async ORM and SQL toolkit | MIT |
| Alembic | Database migrations | MIT |
| asyncpg | PostgreSQL driver | Apache-2.0 |
| aiohttp | HTTP server/client | Apache-2.0 |
| pydantic / pydantic-settings | Configuration validation | MIT |
| redis-py | Redis client | MIT |
| ARQ | Background job worker | MIT |
| wavelink | Lavalink client | MIT |
| prometheus-client | Metrics endpoint | Apache-2.0 |
| OpenTelemetry SDK/exporter | Tracing | Apache-2.0 |
| Pillow | Image rendering | HPND |
| FastAPI | Dashboard API only (deferred) | MIT |
| Uvicorn | Dashboard API only (deferred) | BSD-3-Clause |
| httpx | Dashboard API only (deferred) | BSD-3-Clause |
| itsdangerous | Dashboard sessions only (deferred) | BSD-3-Clause |

## Repository action required

Before any public release, the repository owner must do one of the following:

1. Obtain written permission from the FALLEN copyright holder and record it
   here, or
2. Confirm that upstream has adopted a license and reproduce that license text
   verbatim in `LICENSE`, or
3. Remove or replace all upstream-derived code before publishing.

Until then, treat this repository as private and proprietary.
