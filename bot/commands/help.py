"""Dynamic, searchable help for the commands that are actually registered.

Both prefix and application-command help use the same command inventory. This
module deliberately never advertises roadmap-only or unregistered commands.
"""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

PAGE_SIZE = 10
HOME_TITLE = "Junior Atlas · Command Help"


def _clean(value: str, limit: int = 90) -> str:
    value = " ".join((value or "").split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _category(command: commands.Command) -> str:
    cog = getattr(command, "cog", None)
    name = getattr(cog, "qualified_name", None) or getattr(cog, "__cog_name__", None)
    if name:
        return name
    root = command.qualified_name.split(" ", 1)[0]
    return root.title()


def _prefix_inventory(bot: commands.Bot) -> list[tuple[str, str, str]]:
    """Return registered prefix commands only, excluding hidden commands."""
    items: list[tuple[str, str, str]] = []
    for command in bot.walk_commands():
        if command.hidden:
            continue
        # Groups are useful help entries too; subcommands appear independently.
        usage = command.signature.strip()
        syntax = f"<prefix>{command.qualified_name}"
        if usage:
            syntax += f" {usage}"
        items.append((_category(command), syntax, command.short_doc or command.help or "No description provided."))
    return items


def _slash_inventory(bot: commands.Bot) -> list[tuple[str, str, str]]:
    """Walk registered application commands, including nested command groups."""
    items: list[tuple[str, str, str]] = []

    def visit(command, prefix: str = "") -> None:
        qualified = f"{prefix} {command.name}".strip()
        children = getattr(command, "commands", None)
        if children:
            for child in children:
                visit(child, qualified)
        else:
            description = getattr(command, "description", "") or "No description provided."
            category = _category_of_slash(command)
            items.append((category, f"/{qualified}", description))

    for command in bot.tree.get_commands():
        visit(command)
    return items


def _category_of_slash(command) -> str:
    root = getattr(command, "qualified_name", getattr(command, "name", "Slash"))
    root = str(root).split(" ", 1)[0]
    return root.replace("-", " ").title()


def _inventory(bot: commands.Bot) -> list[tuple[str, str, str]]:
    # Prefix and slash interfaces are shown separately so users can discover
    # the interface they can invoke. Deduplicate only exact interface entries.
    seen: set[tuple[str, str]] = set()
    result = []
    for category, syntax, description in _prefix_inventory(bot) + _slash_inventory(bot):
        key = (category, syntax)
        if key not in seen:
            seen.add(key)
            result.append((category, syntax, description))
    return sorted(result, key=lambda item: (item[0].casefold(), item[1].casefold()))


def _permission_summary(bot: commands.Bot | None, syntax: str) -> str:
    """Return a human-readable permission hint for a help entry."""
    if bot is None:
        return "No special permissions advertised."
    if syntax.startswith("/"):
        command = _find_slash(bot, syntax)
        if command is None:
            return "No special permissions advertised."
        permissions = getattr(command, "default_permissions", None)
        if permissions:
            names = [name.replace("_", " ").title() for name, value in permissions if value]
            if names:
                return "Requires: " + ", ".join(names)
        if getattr(command, "guild_only", False):
            return "Server only."
        return "Available to everyone."
    command = _find_prefix(bot, syntax)
    if command is None:
        return "No special permissions advertised."
    if getattr(command, "checks", None):
        names = {getattr(check, "__name__", "") for check in command.checks}
        if "guild_only" in names:
            return "Server only; command-specific checks may also apply."
        return "Permission checks apply (see the command documentation)."
    return "Available to everyone."


def _find_prefix(bot: commands.Bot, syntax: str):
    name = syntax.removeprefix("<prefix>").split(" ", 1)[0]
    return bot.get_command(name)


def _find_slash(bot: commands.Bot, syntax: str):
    parts = [part for part in syntax.removeprefix("/").split() if part]
    if not parts:
        return None
    command = bot.tree.get_command(parts[0])
    for part in parts[1:]:
        if command is None:
            return None
        children = getattr(command, "commands", ())
        command = next((child for child in children if child.name == part), None)
    return command


class HelpSearchModal(discord.ui.Modal, title="Search commands"):
    query: discord.ui.TextInput = discord.ui.TextInput(
        label="Command or category",
        placeholder="e.g. moderation, ticket, poll",
        max_length=80,
        required=False,
    )

    def __init__(self, view: "HelpPager"):
        super().__init__()
        self.view_ref = view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.view_ref.apply_search(self.query.value)
        await self.view_ref._refresh(interaction)


class HelpPager(discord.ui.View):
    """Paginated help browser with category, search, home and detail controls."""

    def __init__(
        self,
        entries: list[tuple[str, str, str]],
        title: str,
        *,
        page: int = 0,
        bot: commands.Bot | None = None,
    ):
        super().__init__(timeout=180)
        self.all_entries = list(entries)
        self.entries = list(entries)
        self.title_text = title
        self.query = ""
        self.page = page
        self.bot = bot
        self.message: discord.Message | None = None
        self._sync_category_options()
        self._sync_buttons()

    # ---------------------------------------------------------------- state
    def categories(self) -> list[str]:
        return sorted({entry[0] for entry in self.entries}, key=str.casefold)

    def apply_search(self, query: str | None) -> None:
        self.query = (query or "").strip()
        if not self.query:
            self.entries = list(self.all_entries)
        else:
            needle = self.query.casefold()
            self.entries = [
                entry
                for entry in self.all_entries
                if needle in entry[1].casefold()
                or needle in entry[2].casefold()
                or needle in entry[0].casefold()
            ]
        self.title_text = f"Help search: {self.query[:80]}" if self.query else HOME_TITLE
        self.page = 0
        self._sync_category_options()
        self._sync_buttons()

    def apply_category(self, category: str | None) -> None:
        if not category or category == "All categories":
            self.entries = list(self.all_entries)
        else:
            self.entries = [entry for entry in self.all_entries if entry[0] == category]
        self.page = 0
        self._sync_buttons()

    def _sync_category_options(self) -> None:
        select = self._category_select
        values = ["All categories", *self.categories()]
        select.options = [
            discord.SelectOption(label=_clean(value, 90), value=value, default=value == "All categories")
            for value in values[:25]
        ]

    def _sync_buttons(self) -> None:
        pages = max(1, (len(self.entries) + PAGE_SIZE - 1) // PAGE_SIZE)
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "help:prev":
                child.disabled = self.page <= 0
            elif isinstance(child, discord.ui.Button) and child.custom_id == "help:next":
                child.disabled = self.page >= pages - 1
        self._sync_detail_options()

    def _sync_detail_options(self) -> None:
        start = self.page * PAGE_SIZE
        chunk = self.entries[start:start + PAGE_SIZE]
        select = self._detail_select
        select.options = [
            discord.SelectOption(label=_clean(syntax, 100), value=syntax)
            for _, syntax, _ in chunk
        ] or [discord.SelectOption(label="No command on this page", value="none")]
        select.disabled = not chunk

    # ---------------------------------------------------------------- render
    def make_embed(self) -> discord.Embed:
        pages = max(1, (len(self.entries) + PAGE_SIZE - 1) // PAGE_SIZE)
        start = self.page * PAGE_SIZE
        chunk = self.entries[start:start + PAGE_SIZE]
        footer = "Only registered commands are listed. Some actions require server permissions."
        embed = discord.Embed(
            title=self.title_text,
            description=(
                f"**{len(self.entries)} registered entries** · Page {self.page + 1}/{pages}\n"
                "Use the category menu, search button, or `/help <term>` to filter. "
                "Your server prefix is configurable."
            ),
            colour=discord.Colour.blurple(),
        )
        if not chunk:
            empty_text = "No commands are currently registered." if not self.entries else "No matching commands. Try a shorter search term."
            embed.add_field(name="No matching commands", value=empty_text, inline=False)
        else:
            for category, syntax, description in chunk:
                embed.add_field(
                    name=_clean(syntax, 240),
                    value=f"{_clean(description, 180)}\n*{category}*",
                    inline=False,
                )
        embed.set_footer(text=footer)
        return embed

    async def _refresh(self, interaction: discord.Interaction) -> None:
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    # ---------------------------------------------------------------- controls
    @discord.ui.select(
        placeholder="Filter by category",
        custom_id="help:category",
        min_values=1,
        max_values=1,
        options=[discord.SelectOption(label="All categories", value="All categories")],
    )
    async def _category_select(self, interaction: discord.Interaction, select: discord.ui.Select) -> None:
        self.apply_category(select.values[0])
        select.options = [
            discord.SelectOption(
                label=_clean(option.label, 90),
                value=option.value,
                default=option.value == select.values[0],
            )
            for option in select.options
        ]
        await self._refresh(interaction)

    @discord.ui.button(label="Home", style=discord.ButtonStyle.secondary, emoji="🏠", custom_id="help:home")
    async def home(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.entries = list(self.all_entries)
        self.query = ""
        self.title_text = HOME_TITLE
        self.page = 0
        self._sync_category_options()
        self._sync_buttons()
        await self._refresh(interaction)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, custom_id="help:prev")
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.page = max(0, self.page - 1)
        await self._refresh(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, custom_id="help:next")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        pages = max(1, (len(self.entries) + PAGE_SIZE - 1) // PAGE_SIZE)
        self.page = min(pages - 1, self.page + 1)
        await self._refresh(interaction)

    @discord.ui.button(label="Search", style=discord.ButtonStyle.success, emoji="🔎", custom_id="help:search")
    async def search(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(HelpSearchModal(self))

    @discord.ui.select(
        placeholder="Show command details",
        custom_id="help:detail",
        min_values=1,
        max_values=1,
        options=[discord.SelectOption(label="Select a command", value="none")],
    )
    async def _detail_select(self, interaction: discord.Interaction, select: discord.ui.Select) -> None:
        start = self.page * PAGE_SIZE
        chunk = self.entries[start:start + PAGE_SIZE]
        visible = {syntax: (category, description) for category, syntax, description in chunk}
        if not visible:
            await interaction.response.send_message("No command is available on this page.", ephemeral=True)
            return
        # The menu always lists the current page so values stay valid.
        select.options = [
            discord.SelectOption(label=_clean(syntax, 100), value=syntax)
            for syntax in visible
        ]
        picked = select.values[0]
        if picked not in visible:
            picked = next(iter(visible))
        category, description = visible[picked]
        embed = discord.Embed(
            title=picked,
            description=_clean(description, 2000),
            colour=discord.Colour.blurple(),
        )
        embed.add_field(name="Category", value=category, inline=True)
        embed.add_field(name="Permissions", value=_permission_summary(self.bot, picked), inline=False)
        embed.add_field(
            name="Usage",
            value=f"`{picked}` — mention a member or reply to their message where supported.",
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def on_timeout(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
            if isinstance(child, discord.ui.Select):
                child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass


# Backwards-compatible descriptive alias used by older internal tests.
HelpPages = HelpPager


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _registered_entries(self) -> list[tuple[str, str, str]]:
        return _inventory(self.bot)

    def _view(self, entries, title: str) -> HelpPager:
        return HelpPages(entries, title, bot=self.bot)

    async def _send_prefix(self, ctx: commands.Context, query: str = "") -> None:
        entries = self._registered_entries()
        if query:
            needle = query.casefold().strip()
            entries = [
                entry for entry in entries
                if needle in entry[1].casefold()
                or needle in entry[2].casefold()
                or needle in entry[0].casefold()
            ]
            title = f"Help search: {query[:80]}"
        else:
            title = HOME_TITLE
        view = self._view(entries, title)
        message = await ctx.send(embed=view.make_embed(), view=view)
        view.message = message

    @commands.command(name="help", aliases=["commands", "cmds"], help="Browse registered prefix and slash commands. Optional search term.")
    async def prefix_help(self, ctx: commands.Context, *, query: str = "") -> None:
        await self._send_prefix(ctx, query)

    @app_commands.command(name="help", description="Browse and search registered bot commands")
    @app_commands.describe(query="Optional command/category search")
    async def slash_help(self, interaction: discord.Interaction, query: str = "") -> None:
        entries = self._registered_entries()
        if query.strip():
            needle = query.casefold().strip()
            entries = [
                entry for entry in entries
                if needle in entry[1].casefold()
                or needle in entry[2].casefold()
                or needle in entry[0].casefold()
            ]
            title = f"Help search: {query[:80]}"
        else:
            title = HOME_TITLE
        view = self._view(entries, title)
        await interaction.response.send_message(embed=view.make_embed(), view=view, ephemeral=True)
        try:
            view.message = await interaction.original_response()
        except discord.HTTPException:
            pass

    @commands.command(name="help-category", aliases=["helpcat"], help="List registered commands in one category.")
    async def prefix_category(self, ctx: commands.Context, *, category: str) -> None:
        needle = category.casefold().strip()
        entries = [entry for entry in _inventory(self.bot) if needle in entry[0].casefold()]
        view = self._view(entries, f"Help category: {category[:80]}")
        message = await ctx.send(embed=view.make_embed(), view=view)
        view.message = message


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))
