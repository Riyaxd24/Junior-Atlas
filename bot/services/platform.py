from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from bot.models import Economy, ModCase, ModerationCounter, Reminder, Suggestion


class PlatformService:
    def __init__(self,db): self.db=db
    async def case(self,guild_id,target_id,moderator_id,action,reason):
        async with self.db.session() as s:
            await s.execute(
                pg_insert(ModerationCounter)
                .values(guild_id=guild_id, next_case_id=1)
                .on_conflict_do_nothing(index_elements=[ModerationCounter.guild_id])
            )
            counter = await s.scalar(
                select(ModerationCounter)
                .where(ModerationCounter.guild_id == guild_id)
                .with_for_update()
            )
            if counter is None:
                counter = ModerationCounter(guild_id=guild_id, next_case_id=1)
                s.add(counter)
                await s.flush()
                counter = await s.scalar(
                    select(ModerationCounter)
                    .where(ModerationCounter.guild_id == guild_id)
                    .with_for_update()
                )
            case_id = counter.next_case_id
            counter.next_case_id += 1
            row=ModCase(
                guild_id=guild_id,
                case_id=case_id,
                target_id=target_id,
                moderator_id=moderator_id,
                action=action,
                reason=reason,
            )
            s.add(row); await s.commit(); await s.refresh(row); return row.id
    async def cases(self,guild_id,target_id,limit=10):
        async with self.db.session() as s:
            r=await s.execute(select(ModCase).where(ModCase.guild_id==guild_id,ModCase.target_id==target_id).order_by(ModCase.id.desc()).limit(limit)); return r.scalars().all()

    async def case_by_id(self, guild_id, case_id):
        async with self.db.session() as s:
            return await s.scalar(
                select(ModCase).where(
                    ModCase.guild_id == guild_id,
                    ModCase.case_id == case_id,
                )
            )

    async def update_case_reason(self, guild_id, case_id, reason):
        async with self.db.session() as s:
            row = await s.scalar(
                select(ModCase).where(
                    ModCase.guild_id == guild_id,
                    ModCase.case_id == case_id,
                )
            )
            if row is None:
                return None
            row.reason = reason
            await s.commit()
            await s.refresh(row)
            return row
    async def add_reminder(self,guild_id,user_id,channel_id,seconds,message):
        async with self.db.session() as s:
            row=Reminder(guild_id=guild_id,user_id=user_id,channel_id=channel_id,message=message,due_at=datetime.now(UTC)+timedelta(seconds=seconds)); s.add(row); await s.commit(); await s.refresh(row); return row
    async def due_reminders(self,limit=100):
        now=datetime.now(UTC)
        stale=now-timedelta(minutes=10)
        async with self.db.session() as s:
            r=await s.execute(
                select(Reminder)
                .where(
                    Reminder.delivered.is_(False),
                    Reminder.due_at <= now,
                    or_(
                        Reminder.processing.is_(False),
                        Reminder.claimed_at.is_(None),
                        Reminder.claimed_at < stale,
                    ),
                )
                .order_by(Reminder.due_at)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
            rows=list(r.scalars())
            for row in rows:
                row.processing=True
                row.claimed_at=now
            await s.commit()
            return rows

    async def complete_reminder(self, reminder_id: int):
        async with self.db.session() as s:
            r=await s.execute(
                select(Reminder).where(
                    Reminder.id == reminder_id,
                    Reminder.delivered.is_(False),
                ).with_for_update()
            )
            row=r.scalar_one_or_none()
            if row is None: return False
            row.delivered=True
            row.processing=False
            row.claimed_at=None
            await s.commit()
            return True

    async def release_reminder(self, reminder_id: int):
        async with self.db.session() as s:
            r=await s.execute(
                select(Reminder).where(
                    Reminder.id == reminder_id,
                    Reminder.delivered.is_(False),
                ).with_for_update()
            )
            row=r.scalar_one_or_none()
            if row is None: return False
            row.processing=False
            row.claimed_at=None
            await s.commit()
            return True
    async def suggestion(self,guild_id,user_id,channel_id,message_id,content):
        async with self.db.session() as s:
            row=Suggestion(guild_id=guild_id,user_id=user_id,channel_id=channel_id,message_id=message_id,content=content); s.add(row); await s.commit(); return row
    async def suggestion_status(self,guild_id,suggestion_id,status):
        async with self.db.session() as s:
            r=await s.execute(update(Suggestion).where(Suggestion.guild_id==guild_id,Suggestion.id==suggestion_id).values(status=status)); await s.commit(); return r.rowcount
    async def balance(self,guild_id,user_id):
        async with self.db.session() as s:
            r=await s.execute(select(Economy).where(Economy.guild_id==guild_id,Economy.user_id==user_id)); row=r.scalar_one_or_none(); return row.balance if row else 0
    async def change_balance(self,guild_id,user_id,delta):
        async with self.db.session() as s:
            # Establish the row without racing another pod, then lock it for the read/modify/write.
            seed = pg_insert(Economy).values(guild_id=guild_id, user_id=user_id, balance=0).on_conflict_do_nothing(
                index_elements=['guild_id', 'user_id']
            )
            await s.execute(seed)
            r = await s.execute(
                select(Economy).where(Economy.guild_id == guild_id, Economy.user_id == user_id).with_for_update()
            )
            row = r.scalar_one()
            row.balance = max(0, row.balance + delta)
            await s.commit()
            return row.balance
