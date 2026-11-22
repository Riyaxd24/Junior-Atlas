# Junior Atlas Specification

Junior Atlas evolves the FALLEN base into a production-ready, modular, multi-server Discord
bot. The governing specification supplied for this repository defines stack, architecture,
security, module, testing, Docker, documentation, and milestone requirements.

Canonical stage and milestone requirements:

- Stage 0: audit and baseline
- M0: foundation hardening
- M1: moderation
- M2: server logging
- M3: AutoMod
- M4: welcome, verification, and roles
- M5: tickets
- M6: security and anti-nuke
- M7: economy
- M8: leveling and achievements
- M9: games
- M10: collection, voice, giveaways, community, and utility
- M11: background jobs and reliability
- M12: finalization

The mandatory implementation stack is Python 3.12+, discord.py 2.x, PostgreSQL, SQLAlchemy
2.x async, asyncpg, Alembic, Redis, ARQ, Pydantic/Pydantic Settings, pytest, Docker Compose,
and pinned compatible dependencies. The complete requirements are maintained in the project
session request and in [COMPLIANCE_CHECKLIST.md](COMPLIANCE_CHECKLIST.md).
