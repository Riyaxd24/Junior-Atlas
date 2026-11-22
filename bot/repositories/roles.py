from datetime import UTC, datetime

from sqlalchemy import delete, select

from bot.models import RoleMenu, RoleMenuItem, TempRole, VerificationSetting


class RolesRepository:
    def __init__(self, db):
        self.db = db

    async def get_verification(self, guild_id):
        async with self.db.session() as session:
            return await session.scalar(
                select(VerificationSetting).where(
                    VerificationSetting.guild_id == guild_id
                )
            )

    async def save_verification(
        self,
        guild_id,
        *,
        enabled,
        channel_id,
        message_id,
        verified_role_id,
        rules_text,
        log_channel_id,
    ):
        async with self.db.session() as session:
            row = await session.scalar(
                select(VerificationSetting).where(
                    VerificationSetting.guild_id == guild_id
                )
            )
            if row is None:
                row = VerificationSetting(guild_id=guild_id)
                session.add(row)
                await session.flush()
            row.enabled = enabled
            row.channel_id = channel_id
            row.message_id = message_id
            row.verified_role_id = verified_role_id
            row.rules_text = rules_text
            row.log_channel_id = log_channel_id
            await session.commit()
            await session.refresh(row)
            return row

    async def create_role_menu(
        self,
        *,
        guild_id,
        channel_id,
        message_id,
        name,
        is_exclusive,
        max_values,
        items,
    ):
        async with self.db.session() as session:
            menu = RoleMenu(
                guild_id=guild_id,
                channel_id=channel_id,
                message_id=message_id,
                name=name,
                menu_type="select",
                max_values=max_values,
                is_exclusive=is_exclusive,
            )
            session.add(menu)
            await session.flush()
            for role_id, label, emoji, description in items:
                session.add(
                    RoleMenuItem(
                        menu_id=menu.id,
                        role_id=role_id,
                        label=label,
                        emoji=emoji,
                        description=description,
                    )
                )
            await session.commit()
            await session.refresh(menu)
            return menu

    async def get_role_menu(self, message_id):
        async with self.db.session() as session:
            menu = await session.scalar(
                select(RoleMenu).where(RoleMenu.message_id == message_id)
            )
            if menu is None:
                return None
            items = (
                await session.execute(
                    select(RoleMenuItem).where(RoleMenuItem.menu_id == menu.id)
                )
            ).scalars().all()
            return menu, list(items)

    async def list_role_menus(self):
        async with self.db.session() as session:
            menus = (
                await session.execute(select(RoleMenu))
            ).scalars().all()
            result = []
            for menu in menus:
                items = (
                    await session.execute(
                        select(RoleMenuItem).where(RoleMenuItem.menu_id == menu.id)
                    )
                ).scalars().all()
                result.append((menu, list(items)))
            return result

    async def assign_temp_role(self, guild_id, user_id, role_id, expires_at):
        async with self.db.session() as session:
            existing = await session.scalar(
                select(TempRole).where(
                    TempRole.guild_id == guild_id,
                    TempRole.user_id == user_id,
                    TempRole.role_id == role_id,
                )
            )
            if existing is None:
                existing = TempRole(
                    guild_id=guild_id,
                    user_id=user_id,
                    role_id=role_id,
                )
                session.add(existing)
            existing.expires_at = expires_at
            await session.commit()

    async def due_temp_roles(self, limit=100):
        async with self.db.session() as session:
            rows = (
                await session.execute(
                    select(TempRole)
                    .where(TempRole.expires_at <= datetime.now(UTC))
                    .limit(limit)
                )
            ).scalars().all()
            return list(rows)

    async def delete_temp_role(self, row):
        async with self.db.session() as session:
            await session.execute(delete(TempRole).where(TempRole.id == row.id))
            await session.commit()
