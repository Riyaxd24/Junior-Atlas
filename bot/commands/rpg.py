"""Minecraft RPG commands: mining, hunting, crates, inventory, shop, pets, battle, quests, bank, and more."""
from __future__ import annotations

import random

import discord
from discord import app_commands
from discord.ext import commands

from bot.ui import error_embed, info_embed, success_embed


class RPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==================== MINING ====================
    @app_commands.command(name="mine", description="Go mining for resources")
    @app_commands.guild_only()
    async def mine(self, interaction: discord.Interaction):
        result = await self.bot.rpg.mine(interaction.guild_id, interaction.user.id)

        if result.item_name == "Nothing":
            await interaction.response.send_message(
                embed=info_embed(
                    "⛏️ Mining Expedition",
                    "You swung your pickaxe but found nothing but stone this time. Try again later!"
                ),
                ephemeral=True
            )
            return

        embed = success_embed(
            "⛏️ Mining Successful!",
            f"You found **{result.quantity}x {result.item_name}**!\n+{result.xp_gained} Mining XP"
        )
        embed.add_field(name="Strength Bonus", value=f"Your mining power increased your yield!", inline=True)
        await interaction.response.send_message(embed=embed)

    @commands.hybrid_command(name="mine", description="Go mining for resources")
    @commands.guild_only()
    async def mine_prefix(self, ctx: commands.Context):
        result = await self.bot.rpg.mine(ctx.guild.id, ctx.author.id)

        if result.item_name == "Nothing":
            await ctx.send(embed=info_embed("⛏️ Mining Expedition", "You found nothing but stone this time."))
            return

        embed = success_embed(
            "⛏️ Mining Successful!",
            f"You found **{result.quantity}x {result.item_name}**!\n+{result.xp_gained} Mining XP"
        )
        await ctx.send(embed=embed)

    # ==================== HUNTING (Minecraft-style) ====================
    @app_commands.command(name="hunt", description="Go hunting for mobs and loot")
    @app_commands.guild_only()
    async def hunt(self, interaction: discord.Interaction):
        result = await self.bot.rpg.hunt(interaction.guild_id, interaction.user.id)

        if not result.mobs_found:
            # Charm depleted
            embed = info_embed(
                "🌿 **|** Emerald Charm Depleted",
                f"Your Emerald Charm has run out of charges!\n**Resets in:** <t:{result.reset_timestamp}:R>"
            )
            embed.add_field(
                name="Charm Status",
                value=f"✦ **Emerald Charm** `[{result.charm_charges_remaining}/{result.charm_max_charges}]`",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Build the Minecraft-style hunt output
        mob_display = " ".join(result.mobs_found)
        mob_names = ", ".join(result.mob_names)

        embed = discord.Embed(
            title="🌿 **|** Hunt Results",
            color=discord.Color.green()
        )
        embed.description = (
            f"Hunt is empowered by ✦ **Emerald Charm** `[{result.charm_charges_remaining}/{result.charm_max_charges}]`\n\n"
            f"⚔️ **|** You discovered:\n{mob_display}\n\n"
            f"**{mob_names}**\n\n"
            f"🐉 **gained {result.xp_gained} XP!**"
        )

        if result.loot_chests > 0:
            embed.add_field(
                name="🎁 **|** Loot Chests Found",
                value=f"You found **{result.loot_chests}** Loot Chest{'s' if result.loot_chests > 1 else ''}!",
                inline=False
            )

        embed.add_field(
            name="🕐 **|** Charm Reset",
            value=f"Resets <t:{result.reset_timestamp}:R>",
            inline=True
        )
        embed.add_field(
            name="✦ **|** Charm Charges",
            value=f"`{result.charm_charges_remaining}/{result.charm_max_charges}`",
            inline=True
        )
        embed.set_footer(text="Junior Atlas • Minecraft RPG")

        await interaction.response.send_message(embed=embed)

    @commands.hybrid_command(name="hunt", description="Go hunting for mobs and loot")
    @commands.guild_only()
    async def hunt_prefix(self, ctx: commands.Context):
        result = await self.bot.rpg.hunt(ctx.guild.id, ctx.author.id)

        if not result.mobs_found:
            embed = info_embed(
                "🌿 Emerald Charm Depleted",
                f"Your Emerald Charm has run out of charges!\nResets <t:{result.reset_timestamp}:R>"
            )
            embed.add_field(name="Charm", value=f"`{result.charm_charges_remaining}/{result.charm_max_charges}`")
            await ctx.send(embed=embed)
            return

        mob_display = " ".join(result.mobs_found)
        mob_names = ", ".join(result.mob_names)

        embed = discord.Embed(
            title="🌿 Hunt Results",
            color=discord.Color.green()
        )
        embed.description = (
            f"Hunt is empowered by ✦ **Emerald Charm** `[{result.charm_charges_remaining}/{result.charm_max_charges}]`\n\n"
            f"⚔️ **|** You discovered:\n{mob_display}\n\n"
            f"**{mob_names}**\n\n"
            f"🐉 **gained {result.xp_gained} XP!**"
        )

        if result.loot_chests > 0:
            embed.add_field(name="🎁 Loot Chests", value=f"Found **{result.loot_chests}**!", inline=False)

        embed.add_field(name="🕐 Reset", value=f"<t:{result.reset_timestamp}:R>", inline=True)
        embed.add_field(name="✦ Charges", value=f"`{result.charm_charges_remaining}/{result.charm_max_charges}`", inline=True)

        await ctx.send(embed=embed)

    # ==================== CRATES ====================
    @app_commands.command(name="crate", description="Open a crate from your inventory")
    @app_commands.guild_only()
    @app_commands.describe(crate="Name of the crate to open")
    async def crate(self, interaction: discord.Interaction, crate: str):
        result = await self.bot.rpg.open_crate(interaction.guild_id, interaction.user.id, crate)

        if result is None:
            await interaction.response.send_message(
                embed=error_embed("No Crate", f"You don't have a **{crate}** in your inventory."),
                ephemeral=True
            )
            return

        embed = success_embed(
            "📦 Crate Opened!",
            f"Inside you found **{result.quantity}x {result.item_name}**!\n+{result.xp_gained} XP"
        )
        await interaction.response.send_message(embed=embed)

    @commands.hybrid_command(name="crate", description="Open a crate from your inventory")
    @commands.guild_only()
    async def crate_prefix(self, ctx: commands.Context, *, crate: str):
        result = await self.bot.rpg.open_crate(ctx.guild.id, ctx.author.id, crate)

        if result is None:
            await ctx.send(embed=error_embed("No Crate", f"You don't have a **{crate}**."))
            return

        embed = success_embed(
            "📦 Crate Opened!",
            f"Inside you found **{result.quantity}x {result.item_name}**!\n+{result.xp_gained} XP"
        )
        await ctx.send(embed=embed)

    # ==================== INVENTORY ====================
    @app_commands.command(name="inventory", description="View your inventory")
    @app_commands.guild_only()
    @app_commands.describe(member="Member to view (defaults to you)")
    async def inventory(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        items = await self.bot.rpg.get_inventory(interaction.guild_id, target.id)

        if not items:
            await interaction.response.send_message(
                embed=info_embed("🎒 Inventory", f"{target.mention}'s inventory is empty."),
                ephemeral=True
            )
            return

        loot_items = []
        gear_items = []
        crate_items = []
        other_items = []

        for inv, item in items:
            line = f"**{inv.quantity}x** {item.name} ({item.rarity})"
            if item.kind == "loot":
                loot_items.append(line)
            elif item.kind in ("gear", "shop"):
                gear_items.append(line)
            elif item.kind == "crate":
                crate_items.append(line)
            else:
                other_items.append(line)

        embed = info_embed(f"🎒 {target.display_name}'s Inventory", f"**{len(items)} unique items**")

        if loot_items:
            embed.add_field(name="📦 Loot & Materials", value="\n".join(loot_items[:15]), inline=False)
        if gear_items:
            embed.add_field(name="⚔️ Gear & Items", value="\n".join(gear_items[:10]), inline=False)
        if crate_items:
            embed.add_field(name="🎁 Crates", value="\n".join(crate_items[:10]), inline=False)
        if other_items:
            embed.add_field(name="📋 Other", value="\n".join(other_items[:10]), inline=False)

        embed.set_footer(text="Use /crate <name> to open crates • /equip <item> to equip gear")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="inventory", aliases=["inv"], description="View your inventory")
    @commands.guild_only()
    async def inventory_prefix(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        items = await self.bot.rpg.get_inventory(ctx.guild.id, target.id)

        if not items:
            await ctx.send(embed=info_embed("🎒 Inventory", f"{target.mention}'s inventory is empty."))
            return

        loot_items = []
        gear_items = []
        crate_items = []
        other_items = []

        for inv, item in items:
            line = f"**{inv.quantity}x** {item.name} ({item.rarity})"
            if item.kind == "loot":
                loot_items.append(line)
            elif item.kind in ("gear", "shop"):
                gear_items.append(line)
            elif item.kind == "crate":
                crate_items.append(line)
            else:
                other_items.append(line)

        embed = info_embed(f"🎒 {target.display_name}'s Inventory", f"**{len(items)} unique items**")
        if loot_items: embed.add_field(name="📦 Loot", value="\n".join(loot_items[:15]), inline=False)
        if gear_items: embed.add_field(name="⚔️ Gear", value="\n".join(gear_items[:10]), inline=False)
        if crate_items: embed.add_field(name="🎁 Crates", value="\n".join(crate_items[:10]), inline=False)
        if other_items: embed.add_field(name="📋 Other", value="\n".join(other_items[:10]), inline=False)

        await ctx.send(embed=embed)

    # ==================== EQUIPMENT ====================
    @app_commands.command(name="equip", description="Equip an item from your inventory")
    @app_commands.guild_only()
    @app_commands.describe(item="Item name to equip")
    async def equip(self, interaction: discord.Interaction, item: str):
        # Find item in inventory
        items = await self.bot.rpg.get_inventory(interaction.guild_id, interaction.user.id)
        target_item = None
        for inv, it in items:
            if it.name.lower() == item.lower():
                target_item = it
                break

        if not target_item:
            await interaction.response.send_message(
                embed=error_embed("Item Not Found", f"You don't have **{item}** in your inventory."),
                ephemeral=True
            )
            return

        success, message = await self.bot.rpg.equip_item(interaction.guild_id, interaction.user.id, target_item.id)

        if success:
            await interaction.response.send_message(embed=success_embed("✅ Equipped", message))
        else:
            await interaction.response.send_message(embed=error_embed("Cannot Equip", message), ephemeral=True)

    @commands.hybrid_command(name="equip", description="Equip an item from your inventory")
    @commands.guild_only()
    async def equip_prefix(self, ctx: commands.Context, *, item: str):
        items = await self.bot.rpg.get_inventory(ctx.guild.id, ctx.author.id)
        target_item = None
        for inv, it in items:
            if it.name.lower() == item.lower():
                target_item = it
                break

        if not target_item:
            await ctx.send(embed=error_embed("Item Not Found", f"You don't have **{item}**."))
            return

        success, message = await self.bot.rpg.equip_item(ctx.guild.id, ctx.author.id, target_item.id)

        if success:
            await ctx.send(embed=success_embed("✅ Equipped", message))
        else:
            await ctx.send(embed=error_embed("Cannot Equip", message))

    @app_commands.command(name="unequip", description="Unequip an item from a slot")
    @app_commands.guild_only()
    @app_commands.describe(slot="Slot to unequip (pickaxe, sword, armor, charm)")
    @app_commands.choices(slot=[
        app_commands.Choice(name="Pickaxe", value="pickaxe"),
        app_commands.Choice(name="Sword", value="sword"),
        app_commands.Choice(name="Armor", value="armor"),
        app_commands.Choice(name="Charm", value="charm"),
    ])
    async def unequip(self, interaction: discord.Interaction, slot: str):
        success, message = await self.bot.rpg.unequip_item(interaction.guild_id, interaction.user.id, slot)

        if success:
            await interaction.response.send_message(embed=success_embed("✅ Unequipped", message))
        else:
            await interaction.response.send_message(embed=error_embed("Cannot Unequip", message), ephemeral=True)

    @commands.hybrid_command(name="unequip", description="Unequip an item from a slot")
    @commands.guild_only()
    async def unequip_prefix(self, ctx: commands.Context, slot: str):
        if slot not in ("pickaxe", "sword", "armor", "charm"):
            await ctx.send(embed=error_embed("Invalid Slot", "Use: pickaxe, sword, armor, or charm"))
            return
        success, message = await self.bot.rpg.unequip_item(ctx.guild.id, ctx.author.id, slot)

        if success:
            await ctx.send(embed=success_embed("✅ Unequipped", message))
        else:
            await ctx.send(embed=error_embed("Cannot Unequip", message))

    @app_commands.command(name="equipped", description="View your equipped items")
    @app_commands.guild_only()
    @app_commands.describe(member="Member to view (defaults to you)")
    async def equipped(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        equipped = await self.bot.rpg.get_equipped_items(interaction.guild_id, target.id)

        embed = info_embed(f"⚔️ {target.display_name}'s Equipment", "Currently equipped items")

        for slot, item in equipped.items():
            if item:
                stats = []
                if item.mining_power: stats.append(f"⛏️ Mining: +{item.mining_power}")
                if item.attack_bonus: stats.append(f"⚔️ Attack: +{item.attack_bonus}")
                if item.defense_bonus: stats.append(f"🛡️ Defense: +{item.defense_bonus}")
                if item.luck_bonus: stats.append(f"🍀 Luck: +{item.luck_bonus}")
                stat_text = " | ".join(stats) if stats else "No bonuses"
                embed.add_field(
                    name=f"{slot.title()}: {item.name} ({item.rarity})",
                    value=stat_text,
                    inline=False
                )
            else:
                embed.add_field(name=f"{slot.title()}", value="*Empty*", inline=False)

        if not equipped or not any(equipped.values()):
            embed.description = "No items equipped."

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="equipped", description="View your equipped items")
    @commands.guild_only()
    async def equipped_prefix(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        equipped = await self.bot.rpg.get_equipped_items(ctx.guild.id, target.id)

        embed = info_embed(f"⚔️ {target.display_name}'s Equipment", "Currently equipped items")
        for slot, item in equipped.items():
            if item:
                stats = []
                if item.mining_power: stats.append(f"⛏️ Mining: +{item.mining_power}")
                if item.attack_bonus: stats.append(f"⚔️ Attack: +{item.attack_bonus}")
                if item.defense_bonus: stats.append(f"🛡️ Defense: +{item.defense_bonus}")
                if item.luck_bonus: stats.append(f"🍀 Luck: +{item.luck_bonus}")
                stat_text = " | ".join(stats) if stats else "No bonuses"
                embed.add_field(name=f"{slot.title()}: {item.name} ({item.rarity})", value=stat_text, inline=False)
            else:
                embed.add_field(name=f"{slot.title()}", value="*Empty*", inline=False)

        if not equipped or not any(equipped.values()):
            embed.description = "No items equipped."

        await ctx.send(embed=embed)

    # ==================== BANK SYSTEM ====================
    @app_commands.command(name="bank", description="View your bank balance")
    @app_commands.guild_only()
    @app_commands.describe(member="Member to view (defaults to you)")
    async def bank(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        wallet, bank = await self.bot.rpg.bank_balance(interaction.guild_id, target.id)

        embed = info_embed("🏦 Bank", f"{target.mention}'s finances")
        embed.add_field(name="💰 Wallet", value=f"**{wallet:,}** coins", inline=True)
        embed.add_field(name="🏦 Bank", value=f"**{bank:,}** coins", inline=True)
        embed.add_field(name="💎 Total", value=f"**{wallet + bank:,}** coins", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="bank", description="View your bank balance")
    @commands.guild_only()
    async def bank_prefix(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        wallet, bank = await self.bot.rpg.bank_balance(ctx.guild.id, target.id)

        embed = info_embed("🏦 Bank", f"{target.mention}'s finances")
        embed.add_field(name="💰 Wallet", value=f"**{wallet:,}**", inline=True)
        embed.add_field(name="🏦 Bank", value=f"**{bank:,}**", inline=True)
        embed.add_field(name="💎 Total", value=f"**{wallet + bank:,}**", inline=True)
        await ctx.send(embed=embed)

    @app_commands.command(name="deposit", description="Deposit coins into your bank")
    @app_commands.guild_only()
    @app_commands.describe(amount="Amount to deposit")
    async def deposit(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 1000000]):
        success, message, bank = await self.bot.rpg.bank_deposit(interaction.guild_id, interaction.user.id, amount)

        if success:
            embed = success_embed("🏦 Deposit Successful", message)
            embed.add_field(name="New Bank Balance", value=f"**{bank:,}** coins", inline=True)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(embed=error_embed("Deposit Failed", message), ephemeral=True)

    @commands.hybrid_command(name="deposit", aliases=["dep"], description="Deposit coins into your bank")
    @commands.guild_only()
    async def deposit_prefix(self, ctx: commands.Context, amount: int):
        if amount <= 0:
            await ctx.send(embed=error_embed("Invalid Amount", "Amount must be positive."))
            return
        success, message, bank = await self.bot.rpg.bank_deposit(ctx.guild.id, ctx.author.id, amount)

        if success:
            embed = success_embed("🏦 Deposit Successful", message)
            embed.add_field(name="New Bank Balance", value=f"**{bank:,}**", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=error_embed("Deposit Failed", message))

    @app_commands.command(name="withdraw", description="Withdraw coins from your bank")
    @app_commands.guild_only()
    @app_commands.describe(amount="Amount to withdraw")
    async def withdraw(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 1000000]):
        success, message, bank = await self.bot.rpg.bank_withdraw(interaction.guild_id, interaction.user.id, amount)

        if success:
            embed = success_embed("🏦 Withdrawal Successful", message)
            embed.add_field(name="New Bank Balance", value=f"**{bank:,}** coins", inline=True)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(embed=error_embed("Withdrawal Failed", message), ephemeral=True)

    @commands.hybrid_command(name="withdraw", aliases=["with"], description="Withdraw coins from your bank")
    @commands.guild_only()
    async def withdraw_prefix(self, ctx: commands.Context, amount: int):
        if amount <= 0:
            await ctx.send(embed=error_embed("Invalid Amount", "Amount must be positive."))
            return
        success, message, bank = await self.bot.rpg.bank_withdraw(ctx.guild.id, ctx.author.id, amount)

        if success:
            embed = success_embed("🏦 Withdrawal Successful", message)
            embed.add_field(name="New Bank Balance", value=f"**{bank:,}**", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=error_embed("Withdrawal Failed", message))

    # ==================== PLAYER TRANSFERS ====================
    @app_commands.command(name="pay", description="Pay another player")
    @app_commands.guild_only()
    @app_commands.describe(member="Member to pay", amount="Amount to pay")
    async def pay(self, interaction: discord.Interaction, member: discord.Member, amount: app_commands.Range[int, 1, 1000000]):
        if member.id == interaction.user.id:
            await interaction.response.send_message(embed=error_embed("Invalid Target", "You cannot pay yourself!"), ephemeral=True)
            return
        if member.bot:
            await interaction.response.send_message(embed=error_embed("Invalid Target", "You cannot pay bots!"), ephemeral=True)
            return

        success, message = await self.bot.rpg.transfer(interaction.guild_id, interaction.user.id, member.id, amount)

        if success:
            await interaction.response.send_message(embed=success_embed("💸 Payment Sent", message))
        else:
            await interaction.response.send_message(embed=error_embed("Payment Failed", message), ephemeral=True)

    @commands.hybrid_command(name="pay", description="Pay another player")
    @commands.guild_only()
    async def pay_prefix(self, ctx: commands.Context, member: discord.Member, amount: int):
        if member.id == ctx.author.id:
            await ctx.send(embed=error_embed("Invalid Target", "You cannot pay yourself!"))
            return
        if member.bot:
            await ctx.send(embed=error_embed("Invalid Target", "You cannot pay bots!"))
            return
        if amount <= 0:
            await ctx.send(embed=error_embed("Invalid Amount", "Amount must be positive."))
            return

        success, message = await self.bot.rpg.transfer(ctx.guild.id, ctx.author.id, member.id, amount)

        if success:
            await ctx.send(embed=success_embed("💸 Payment Sent", message))
        else:
            await ctx.send(embed=error_embed("Payment Failed", message))

    # ==================== SHOP ====================
    @app_commands.command(name="shop", description="View the server shop")
    @app_commands.guild_only()
    async def shop(self, interaction: discord.Interaction):
        # Dynamic shop from database
        items = await self.bot.rpg.get_shop_items(interaction.guild_id)

        embed = info_embed("🏪 Server Shop", "Purchase items to help your adventures!")

        crates = [i for i in items if i.kind == "crate"]
        gear = [i for i in items if i.kind in ("gear", "shop")]
        food = [i for i in items if i.kind == "food"]

        if crates:
            embed.add_field(
                name="📦 Crates",
                value="\n".join(f"`{i.name}` - {i.price:,} coins" for i in crates[:5]),
                inline=True
            )
        if gear:
            embed.add_field(
                name="⚔️ Gear & Tools",
                value="\n".join(f"`{i.name}` - {i.price:,} coins" for i in gear[:5]),
                inline=True
            )
        if food:
            embed.add_field(
                name="🍖 Food & Consumables",
                value="\n".join(f"`{i.name}` - {i.price:,} coins" for i in food[:5]),
                inline=True
            )

        embed.set_footer(text="Use /buy <item> [quantity] to purchase • /sell <item> [quantity] to sell")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="shop", description="View the server shop")
    @commands.guild_only()
    async def shop_prefix(self, ctx: commands.Context):
        items = await self.bot.rpg.get_shop_items(ctx.guild.id)

        embed = info_embed("🏪 Server Shop", "Purchase items to help your adventures!")
        crates = [i for i in items if i.kind == "crate"]
        gear = [i for i in items if i.kind in ("gear", "shop")]
        food = [i for i in items if i.kind == "food"]

        if crates: embed.add_field(name="📦 Crates", value="\n".join(f"`{i.name}` - {i.price:,}" for i in crates[:5]), inline=True)
        if gear: embed.add_field(name="⚔️ Gear", value="\n".join(f"`{i.name}` - {i.price:,}" for i in gear[:5]), inline=True)
        if food: embed.add_field(name="🍖 Food", value="\n".join(f"`{i.name}` - {i.price:,}" for i in food[:5]), inline=True)

        await ctx.send(embed=embed)

    @app_commands.command(name="buy", description="Buy an item from the shop")
    @app_commands.guild_only()
    @app_commands.describe(item="Item name to buy", quantity="Quantity to buy")
    async def buy(self, interaction: discord.Interaction, item: str, quantity: app_commands.Range[int, 1, 64] = 1):
        success, message = await self.bot.rpg.buy_item(interaction.guild_id, interaction.user.id, item, quantity)

        if success:
            await interaction.response.send_message(embed=success_embed("✅ Purchase Complete", message))
        else:
            await interaction.response.send_message(embed=error_embed("Purchase Failed", message), ephemeral=True)

    @commands.hybrid_command(name="buy", description="Buy an item from the shop")
    @commands.guild_only()
    async def buy_prefix(self, ctx: commands.Context, item: str, quantity: int = 1):
        if quantity < 1 or quantity > 64:
            await ctx.send(embed=error_embed("Invalid Quantity", "Quantity must be between 1 and 64."))
            return
        success, message = await self.bot.rpg.buy_item(ctx.guild.id, ctx.author.id, item, quantity)

        if success:
            await ctx.send(embed=success_embed("✅ Purchase Complete", message))
        else:
            await ctx.send(embed=error_embed("Purchase Failed", message))

    @app_commands.command(name="sell", description="Sell an item to the shop")
    @app_commands.guild_only()
    @app_commands.describe(item="Item name to sell", quantity="Quantity to sell")
    async def sell(self, interaction: discord.Interaction, item: str, quantity: app_commands.Range[int, 1, 64] = 1):
        success, message = await self.bot.rpg.sell_item(interaction.guild_id, interaction.user.id, item, quantity)

        if success:
            await interaction.response.send_message(embed=success_embed("💰 Sale Complete", message))
        else:
            await interaction.response.send_message(embed=error_embed("Sale Failed", message), ephemeral=True)

    @commands.hybrid_command(name="sell", description="Sell an item to the shop")
    @commands.guild_only()
    async def sell_prefix(self, ctx: commands.Context, item: str, quantity: int = 1):
        if quantity < 1 or quantity > 64:
            await ctx.send(embed=error_embed("Invalid Quantity", "Quantity must be between 1 and 64."))
            return
        success, message = await self.bot.rpg.sell_item(ctx.guild.id, ctx.author.id, item, quantity)

        if success:
            await ctx.send(embed=success_embed("💰 Sale Complete", message))
        else:
            await ctx.send(embed=error_embed("Sale Failed", message))

    # ==================== BALANCE / ECONOMY ====================
    @app_commands.command(name="balance", description="Check your coin balance")
    @app_commands.guild_only()
    @app_commands.describe(member="Member to check (defaults to you)")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        wallet, bank = await self.bot.rpg.bank_balance(interaction.guild_id, target.id)

        embed = info_embed("💰 Balance", f"{target.mention}'s finances")
        embed.add_field(name="💰 Wallet", value=f"**{wallet:,}** coins", inline=True)
        embed.add_field(name="🏦 Bank", value=f"**{bank:,}** coins", inline=True)
        embed.add_field(name="💎 Total", value=f"**{wallet + bank:,}** coins", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="balance", aliases=["bal", "money"], description="Check your coin balance")
    @commands.guild_only()
    async def balance_prefix(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        wallet, bank = await self.bot.rpg.bank_balance(ctx.guild.id, target.id)

        embed = info_embed("💰 Balance", f"{target.mention}'s finances")
        embed.add_field(name="💰 Wallet", value=f"**{wallet:,}**", inline=True)
        embed.add_field(name="🏦 Bank", value=f"**{bank:,}**", inline=True)
        embed.add_field(name="💎 Total", value=f"**{wallet + bank:,}**", inline=True)
        await ctx.send(embed=embed)

    @app_commands.command(name="daily", description="Claim your daily coins")
    @app_commands.guild_only()
    async def daily(self, interaction: discord.Interaction):
        success, message, balance = await self.bot.rpg.daily_reward(interaction.guild_id, interaction.user.id)

        if success:
            embed = success_embed("🎁 Daily Reward", message)
            embed.add_field(name="Total Balance", value=f"**{balance:,}** coins", inline=True)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(embed=error_embed("Daily Already Claimed", message), ephemeral=True)

    @commands.hybrid_command(name="daily", description="Claim your daily coins")
    @commands.guild_only()
    async def daily_prefix(self, ctx: commands.Context):
        success, message, balance = await self.bot.rpg.daily_reward(ctx.guild.id, ctx.author.id)

        if success:
            embed = success_embed("🎁 Daily Reward", message)
            embed.add_field(name="Total Balance", value=f"**{balance:,}**", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=error_embed("Daily Already Claimed", message))

    @app_commands.command(name="work", description="Work for coins")
    @app_commands.guild_only()
    async def work(self, interaction: discord.Interaction):
        success, message, balance = await self.bot.rpg.work(interaction.guild_id, interaction.user.id)

        if success:
            embed = success_embed("💼 Work Complete", message)
            embed.add_field(name="Total Balance", value=f"**{balance:,}** coins", inline=True)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(embed=error_embed("Too Tired", message), ephemeral=True)

    @commands.hybrid_command(name="work", description="Work for coins")
    @commands.guild_only()
    async def work_prefix(self, ctx: commands.Context):
        success, message, balance = await self.bot.rpg.work(ctx.guild.id, ctx.author.id)

        if success:
            embed = success_embed("💼 Work Complete", message)
            embed.add_field(name="Total Balance", value=f"**{balance:,}**", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=error_embed("Too Tired", message))

    # ==================== RPG STATS ====================
    @app_commands.command(name="rpgstats", description="View your RPG stats")
    @app_commands.guild_only()
    @app_commands.describe(member="Member to view (defaults to you)")
    async def rpgstats(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        stats = await self.bot.rpg.get_stats(interaction.guild_id, target.id)

        embed = info_embed(f"⚔️ {target.display_name}'s RPG Stats", "Your mining and hunting prowess")
        embed.add_field(name="💪 Strength", value=f"**{stats.strength}** (Mining bonus)", inline=True)
        embed.add_field(name="🛡️ Defense", value=f"**{stats.defense}** (Survival bonus)", inline=True)
        embed.add_field(name="🍀 Luck", value=f"**{stats.luck}** (Rare drops)", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="rpgstats", description="View your RPG stats")
    @commands.guild_only()
    async def rpgstats_prefix(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        stats = await self.bot.rpg.get_stats(ctx.guild.id, target.id)
        embed = info_embed(f"⚔️ {target.display_name}'s RPG Stats", "Your mining and hunting prowess")
        embed.add_field(name="💪 Strength", value=f"**{stats.strength}**", inline=True)
        embed.add_field(name="🛡️ Defense", value=f"**{stats.defense}**", inline=True)
        embed.add_field(name="🍀 Luck", value=f"**{stats.luck}**", inline=True)
        await ctx.send(embed=embed)

    # ==================== PET SYSTEM ====================
    @app_commands.command(name="pet", description="Manage your pet collection")
    @app_commands.guild_only()
    @app_commands.describe(action="Action to perform")
    @app_commands.choices(action=[
        app_commands.Choice(name="list", value="list"),
        app_commands.Choice(name="active", value="active"),
    ])
    async def pet(self, interaction: discord.Interaction, action: str, pet_id: int = None):
        if action == "list":
            pets = await self.bot.rpg.get_pets(interaction.guild_id, interaction.user.id)

            if not pets:
                await interaction.response.send_message(
                    embed=info_embed("🐾 Pet Collection", "You haven't caught any pets yet! Go hunting to find some."),
                    ephemeral=True
                )
                return

            embed = info_embed(f"🐾 {interaction.user.display_name}'s Pet Collection", f"**{len(pets)} pets caught**")

            for pet in pets[:20]:
                active_marker = " ⚔️" if pet.is_active else ""
                embed.add_field(
                    name=f"{pet.mob.emoji} {pet.name or pet.mob.name} (Lv.{pet.level}){active_marker}",
                    value=f"Rarity: {pet.rarity.title()} | XP: {pet.xp}/{pet.level * 100}",
                    inline=True
                )

            embed.set_footer(text="Use /pet active <id> to set active pet • Hunt to catch more!")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif action == "active":
            if not pet_id:
                await interaction.response.send_message(embed=error_embed("Missing ID", "Provide a pet ID to set as active."), ephemeral=True)
                return

            success, message = await self.bot.rpg.set_active_pet(interaction.guild_id, interaction.user.id, pet_id)

            if success:
                await interaction.response.send_message(embed=success_embed("⚔️ Active Pet Set", message))
            else:
                await interaction.response.send_message(embed=error_embed("Failed", message), ephemeral=True)

    @commands.hybrid_command(name="pet", description="Manage your pet collection")
    @commands.guild_only()
    async def pet_prefix(self, ctx: commands.Context, action: str = "list", pet_id: int = None):
        if action == "list":
            pets = await self.bot.rpg.get_pets(ctx.guild.id, ctx.author.id)

            if not pets:
                await ctx.send(embed=info_embed("🐾 Pet Collection", "You haven't caught any pets yet!"))
                return

            embed = info_embed(f"🐾 {ctx.author.display_name}'s Pet Collection", f"**{len(pets)} pets**")
            for pet in pets[:20]:
                active_marker = " ⚔️" if pet.is_active else ""
                embed.add_field(name=f"{pet.mob.emoji} {pet.name or pet.mob.name} (Lv.{pet.level}){active_marker}", value=f"Rarity: {pet.rarity.title()}", inline=True)

            await ctx.send(embed=embed)

        elif action == "active":
            if not pet_id:
                await ctx.send(embed=error_embed("Missing ID", "Provide a pet ID."))
                return
            success, message = await self.bot.rpg.set_active_pet(ctx.guild.id, ctx.author.id, pet_id)

            if success:
                await ctx.send(embed=success_embed("⚔️ Active Pet Set", message))
            else:
                await ctx.send(embed=error_embed("Failed", message))

    # ==================== BATTLE SYSTEM ====================
    @app_commands.command(name="battle", description="Battle another player with your pets")
    @app_commands.guild_only()
    @app_commands.describe(opponent="Member to battle")
    async def battle(self, interaction: discord.Interaction, opponent: discord.Member):
        if opponent.id == interaction.user.id:
            await interaction.response.send_message(embed=error_embed("Invalid Target", "You cannot battle yourself!"), ephemeral=True)
            return
        if opponent.bot:
            await interaction.response.send_message(embed=error_embed("Invalid Target", "You cannot battle bots!"), ephemeral=True)
            return

        success, message, battle = await self.bot.rpg.start_battle(interaction.guild_id, interaction.user.id, opponent.id)

        if not success:
            await interaction.response.send_message(embed=error_embed("Battle Failed", message), ephemeral=True)
            return

        # Create battle view with action buttons
        view = BattleView(self.bot, battle, interaction.user.id, opponent.id)
        embed = discord.Embed(
            title="⚔️ Battle Started!",
            description=message,
            color=discord.Color.red()
        )
        embed.add_field(name="Your Turn", value="Choose an action below", inline=False)
        embed.add_field(name="Instructions", value="Use the buttons to Attack, Defend, use Special, or Flee", inline=False)

        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()

    @commands.hybrid_command(name="battle", description="Battle another player with your pets")
    @commands.guild_only()
    async def battle_prefix(self, ctx: commands.Context, opponent: discord.Member):
        if opponent.id == ctx.author.id:
            await ctx.send(embed=error_embed("Invalid Target", "You cannot battle yourself!"))
            return
        if opponent.bot:
            await ctx.send(embed=error_embed("Invalid Target", "You cannot battle bots!"))
            return

        success, message, battle = await self.bot.rpg.start_battle(ctx.guild.id, ctx.author.id, opponent.id)

        if not success:
            await ctx.send(embed=error_embed("Battle Failed", message))
            return

        view = BattleView(self.bot, battle, ctx.author.id, opponent.id)
        embed = discord.Embed(title="⚔️ Battle Started!", description=message, color=discord.Color.red())
        embed.add_field(name="Instructions", value="Use buttons to Attack, Defend, Special, or Flee", inline=False)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    # ==================== QUEST SYSTEM ====================
    @app_commands.command(name="quest", description="View and manage quests")
    @app_commands.guild_only()
    @app_commands.describe(action="Action to perform", quest_id="Quest ID for start/claim")
    @app_commands.choices(action=[
        app_commands.Choice(name="list", value="list"),
        app_commands.Choice(name="start", value="start"),
        app_commands.Choice(name="claim", value="claim"),
    ])
    async def quest(self, interaction: discord.Interaction, action: str, quest_id: int = None):
        if action == "list":
            quests = await self.bot.rpg.get_available_quests(interaction.guild_id, interaction.user.id)

            if not quests:
                await interaction.response.send_message(
                    embed=info_embed("📜 Quests", "No available quests at the moment."),
                    ephemeral=True
                )
                return

            embed = info_embed("📜 Available Quests", f"**{len(quests)} quests available**")

            for quest in quests[:10]:
                embed.add_field(
                    name=f"{quest.name} (ID: {quest.id})",
                    value=f"{quest.description}\n**Type:** {quest.type.title()} | **Reward:** {quest.reward_xp} XP + {quest.reward_coins:,} coins",
                    inline=False
                )

            embed.set_footer(text="Use /quest start <id> to begin a quest")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif action == "start":
            if not quest_id:
                await interaction.response.send_message(embed=error_embed("Missing ID", "Provide a quest ID to start."), ephemeral=True)
                return

            success, message = await self.bot.rpg.start_quest(interaction.guild_id, interaction.user.id, quest_id)

            if success:
                await interaction.response.send_message(embed=success_embed("📜 Quest Started", message))
            else:
                await interaction.response.send_message(embed=error_embed("Failed", message), ephemeral=True)

        elif action == "claim":
            if not quest_id:
                await interaction.response.send_message(embed=error_embed("Missing ID", "Provide a quest ID to claim."), ephemeral=True)
                return

            success, message = await self.bot.rpg.claim_quest(interaction.guild_id, interaction.user.id, quest_id)

            if success:
                await interaction.response.send_message(embed=success_embed("🎁 Quest Claimed", message))
            else:
                await interaction.response.send_message(embed=error_embed("Failed", message), ephemeral=True)

    @commands.hybrid_command(name="quest", description="View and manage quests")
    @commands.guild_only()
    async def quest_prefix(self, ctx: commands.Context, action: str = "list", quest_id: int = None):
        if action == "list":
            quests = await self.bot.rpg.get_available_quests(ctx.guild.id, ctx.author.id)

            if not quests:
                await ctx.send(embed=info_embed("📜 Quests", "No available quests."))
                return

            embed = info_embed("📜 Available Quests", f"**{len(quests)} quests**")
            for quest in quests[:10]:
                embed.add_field(name=f"{quest.name} (ID: {quest.id})", value=f"{quest.description}\nReward: {quest.reward_xp} XP + {quest.reward_coins:,} coins", inline=False)

            await ctx.send(embed=embed)

        elif action == "start":
            if not quest_id:
                await ctx.send(embed=error_embed("Missing ID", "Provide a quest ID."))
                return
            success, message = await self.bot.rpg.start_quest(ctx.guild.id, ctx.author.id, quest_id)

            if success:
                await ctx.send(embed=success_embed("📜 Quest Started", message))
            else:
                await ctx.send(embed=error_embed("Failed", message))

        elif action == "claim":
            if not quest_id:
                await ctx.send(embed=error_embed("Missing ID", "Provide a quest ID."))
                return
            success, message = await self.bot.rpg.claim_quest(ctx.guild.id, ctx.author.id, quest_id)

            if success:
                await ctx.send(embed=success_embed("🎁 Quest Claimed", message))
            else:
                await ctx.send(embed=error_embed("Failed", message))

    # ==================== LEADERBOARDS ====================
    @app_commands.command(name="rpgleaderboard", description="View RPG leaderboards")
    @app_commands.guild_only()
    @app_commands.describe(category="Leaderboard category")
    @app_commands.choices(category=[
        app_commands.Choice(name="Strength", value="strength"),
        app_commands.Choice(name="Luck", value="luck"),
        app_commands.Choice(name="Pets Caught", value="pets_caught"),
    ])
    async def rpgleaderboard(self, interaction: discord.Interaction, category: str = "strength"):
        await self.bot.rpg.update_leaderboards(interaction.guild_id)
        leaders = await self.bot.rpg.get_leaderboard(interaction.guild_id, category, 10)

        if not leaders:
            await interaction.response.send_message(
                embed=info_embed(f"🏆 {category.title()} Leaderboard", "No data yet. Start playing to rank up!"),
                ephemeral=True
            )
            return

        embed = info_embed(f"🏆 {category.title()} Leaderboard", f"Top players in **{interaction.guild.name}**")

        for i, entry in enumerate(leaders, 1):
            member = interaction.guild.get_member(entry.user_id)
            name = member.display_name if member else f"User {entry.user_id}"
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`#{i}`"
            embed.add_field(name=f"{medal} {name}", value=f"**{entry.value:,}**", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="rpgleaderboard", description="View RPG leaderboards")
    @commands.guild_only()
    async def rpgleaderboard_prefix(self, ctx: commands.Context, category: str = "strength"):
        await self.bot.rpg.update_leaderboards(ctx.guild.id)
        leaders = await self.bot.rpg.get_leaderboard(ctx.guild.id, category, 10)

        if not leaders:
            await ctx.send(embed=info_embed(f"🏆 {category.title()} Leaderboard", "No data yet."))
            return

        embed = info_embed(f"🏆 {category.title()} Leaderboard", f"Top players in **{ctx.guild.name}**")
        for i, entry in enumerate(leaders, 1):
            member = ctx.guild.get_member(entry.user_id)
            name = member.display_name if member else f"User {entry.user_id}"
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`#{i}`"
            embed.add_field(name=f"{medal} {name}", value=f"**{entry.value:,}**", inline=True)

        await ctx.send(embed=embed)

    # ==================== ACHIEVEMENTS ====================
    @app_commands.command(name="achievements", description="View your achievements")
    @app_commands.guild_only()
    @app_commands.describe(member="Member to view (defaults to you)")
    async def achievements(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        unlocked = await self.bot.rpg.check_achievements(interaction.guild_id, target.id)

        async with self.bot.db.session() as s:
            all_ach = list((await s.execute(
                select(RPGAchievement).where(RPGAchievement.guild_id == interaction.guild_id)
            )).scalars().all())

            user_ach = set(p.achievement_id for p in (await s.execute(
                select(RPGUserAchievement.achievement_id).where(
                    RPGUserAchievement.guild_id == interaction.guild_id,
                    RPGUserAchievement.user_id == target.id
                )
            )).scalars().all())

        embed = info_embed(f"🏆 {target.display_name}'s Achievements", f"**{len(user_ach)}/{len(all_ach)} unlocked**")

        for ach in all_ach[:15]:
            is_unlocked = ach.id in user_ach
            status = "✅" if is_unlocked else "🔒"
            embed.add_field(
                name=f"{status} {ach.icon_emoji} {ach.name}",
                value=ach.description,
                inline=True
            )

        if unlocked:
            embed.add_field(name="🎉 Newly Unlocked!", value="\n".join(f"{a.icon_emoji} {a.name}" for a in unlocked), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="achievements", description="View your achievements")
    @commands.guild_only()
    async def achievements_prefix(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        unlocked = await self.bot.rpg.check_achievements(ctx.guild.id, target.id)

        async with self.bot.db.session() as s:
            all_ach = list((await s.execute(
                select(RPGAchievement).where(RPGAchievement.guild_id == ctx.guild.id)
            )).scalars().all())

            user_ach = set(p.achievement_id for p in (await s.execute(
                select(RPGUserAchievement.achievement_id).where(
                    RPGUserAchievement.guild_id == ctx.guild.id,
                    RPGUserAchievement.user_id == target.id
                )
            )).scalars().all())

        embed = info_embed(f"🏆 {target.display_name}'s Achievements", f"**{len(user_ach)}/{len(all_ach)} unlocked**")
        for ach in all_ach[:15]:
            is_unlocked = ach.id in user_ach
            status = "✅" if is_unlocked else "🔒"
            embed.add_field(name=f"{status} {ach.icon_emoji} {ach.name}", value=ach.description, inline=True)

        if unlocked:
            embed.add_field(name="🎉 Newly Unlocked!", value="\n".join(f"{a.icon_emoji} {a.name}" for a in unlocked), inline=False)

        await ctx.send(embed=embed)


# ==================== BATTLE VIEW ====================
class BattleView(discord.ui.View):
    def __init__(self, bot, battle, challenger_id, opponent_id):
        super().__init__(timeout=120)
        self.bot = bot
        self.battle = battle
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in (self.challenger_id, self.opponent_id):
            await interaction.response.send_message("You are not part of this battle!", ephemeral=True)
            return False
        return True

    async def _process_action(self, interaction: discord.Interaction, action: str):
        success, message, result = await self.bot.rpg.battle_action(
            self.battle.guild_id, self.battle.id, interaction.user.id, action
        )

        if not success:
            await interaction.response.send_message(message, ephemeral=True)
            return

        embed = discord.Embed(
            title="⚔️ Battle Update",
            description=message,
            color=discord.Color.red()
        )

        if result and self.battle.state == "finished":
            winner = self.bot.get_user(result.winner_id)
            embed.title = "🏆 Battle Finished!"
            embed.description = f"**{winner.mention if winner else 'Someone'}** won the battle!\n\n" + "\n".join(self.battle.log[-5:])
            embed.add_field(name="Rewards", value=f"+{result.xp_reward} XP + {result.coin_reward:,} coins", inline=False)
            for child in self.children:
                child.disabled = True
        else:
            embed.add_field(name="Battle Log", value="\n".join(self.battle.log[-3:]), inline=False)
            embed.add_field(name="Your Turn" if self.battle.turn == "challenger" and interaction.user.id == self.challenger_id else "Opponent's Turn", value="Choose an action", inline=False)

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⚔️ Attack", style=discord.ButtonStyle.danger)
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._process_action(interaction, "attack")

    @discord.ui.button(label="🛡️ Defend", style=discord.ButtonStyle.secondary)
    async def defend(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._process_action(interaction, "defend")

    @discord.ui.button(label="✨ Special", style=discord.ButtonStyle.primary)
    async def special(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._process_action(interaction, "special")

    @discord.ui.button(label="🏃 Flee", style=discord.ButtonStyle.success)
    async def flee(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._process_action(interaction, "flee")

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass


async def setup(bot):
    await bot.add_cog(RPG(bot))