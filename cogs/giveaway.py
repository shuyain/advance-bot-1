import asyncio
import random
import re
import time

import discord
from discord.ext import commands
from discord import app_commands

from utils.database import (
    get_giveaway_data,
    save_giveaway_data
)

from utils.embeds import (
    success_embed,
    error_embed,
    giveaway_embed
)


def parse_duration(duration: str):
    """
    Convert duration text into seconds.

    Examples:
    10s
    10m
    2h
    1d
    """

    match = re.fullmatch(
        r"(\d+)\s*(s|m|h|d)",
        duration.lower().strip()
    )

    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    multipliers = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400
    }

    return value * multipliers[unit]


def format_duration(seconds: int):
    """Format seconds into readable duration."""

    if seconds < 60:
        return f"{seconds}s"

    if seconds < 3600:
        return f"{seconds // 60}m"

    if seconds < 86400:
        return f"{seconds // 3600}h"

    return f"{seconds // 86400}d"


class GiveawayView(discord.ui.View):

    def __init__(self, giveaway_id: str):
        super().__init__(timeout=None)

        self.giveaway_id = giveaway_id

    @discord.ui.button(
        label="Enter Giveaway",
        emoji="🎉",
        style=discord.ButtonStyle.primary,
        custom_id="giveaway_enter"
    )
    async def enter_giveaway(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild_id = str(interaction.guild.id)

        giveaways = get_giveaway_data(
            guild_id
        )

        giveaway = giveaways.get(
            self.giveaway_id
        )

        if giveaway is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "Giveaway Not Found",
                    "This giveaway no longer exists."
                ),
                ephemeral=True
            )
            return

        if giveaway["ended"]:
            await interaction.response.send_message(
                embed=error_embed(
                    "Giveaway Ended",
                    "This giveaway has already ended."
                ),
                ephemeral=True
            )
            return

        user_id = str(interaction.user.id)

        participants = giveaway.setdefault(
            "participants",
            []
        )

        if user_id in participants:

            participants.remove(user_id)

            save_giveaway_data(
                guild_id,
                giveaways
            )

            await interaction.response.send_message(
                "❌ You left the giveaway.",
                ephemeral=True
            )

            return

        participants.append(user_id)

        save_giveaway_data(
            guild_id,
            giveaways
        )

        await interaction.response.send_message(
            "🎉 You entered the giveaway!",
            ephemeral=True
        )


class Giveaway(commands.Cog):

    def __init__(self, bot):

        self.bot = bot
        self.tasks = {}

    async def restore_giveaways(self):
        """Restore saved active giveaways after bot restart."""

        for guild in self.bot.guilds:

            guild_id = str(guild.id)

            giveaways = get_giveaway_data(
                guild_id
            )

            for giveaway_id, giveaway in giveaways.items():

                if giveaway.get("ended"):
                    continue

                self.bot.add_view(
                    GiveawayView(giveaway_id),
                    message_id=giveaway.get("message_id")
                )

                task = asyncio.create_task(
                    self.finish_giveaway(
                        guild.id,
                        giveaway_id
                    )
                )

                self.tasks[giveaway_id] = task

    @app_commands.command(
        name="giveaway-create",
        description="Create a giveaway."
    )
    @app_commands.describe(
        prize="Giveaway prize.",
        duration="Duration: 10s, 10m, 2h, 1d.",
        winners="Number of winners.",
        channel="Giveaway channel.",
        image="Optional image URL."
    )
    async def giveaway_create(
        self,
        interaction: discord.Interaction,
        prize: str,
        duration: str,
        winners: int,
        channel: discord.TextChannel,
        image: str | None = None
    ):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=error_embed(
                    "No Permission",
                    "You need Administrator permission."
                ),
                ephemeral=True
            )
            return

        seconds = parse_duration(duration)

        if seconds is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Duration",
                    "Use formats like `10s`, `10m`, `2h`, or `1d`."
                ),
                ephemeral=True
            )
            return

        if seconds < 10:
            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Duration",
                    "Giveaway duration must be at least 10 seconds."
                ),
                ephemeral=True
            )
            return

        if winners < 1:
            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Winners",
                    "There must be at least 1 winner."
                ),
                ephemeral=True
            )
            return

        if winners > 100:
            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Winners",
                    "Maximum winners is 100."
                ),
                ephemeral=True
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        giveaway_id = str(
            int(time.time() * 1000)
        )

        end_timestamp = int(
            time.time() + seconds
        )

        end_text = (
            f"<t:{end_timestamp}:R>\n"
            f"<t:{end_timestamp}:F>"
        )

        embed = giveaway_embed(
            prize=prize,
            winners=winners,
            end_text=end_text,
            host=interaction.user
        )

        embed.add_field(
            name="👥 Entries",
            value="`0`",
            inline=False
        )

        if image:
            embed.set_image(
                url=image
            )

        try:

            message = await channel.send(
                embed=embed,
                view=GiveawayView(
                    giveaway_id
                )
            )

        except discord.Forbidden:

            await interaction.followup.send(
                embed=error_embed(
                    "Send Failed",
                    f"I don't have permission to send messages in {channel.mention}."
                ),
                ephemeral=True
            )

            return

        except discord.HTTPException:

            await interaction.followup.send(
                embed=error_embed(
                    "Send Failed",
                    "Discord rejected the giveaway message."
                ),
                ephemeral=True
            )

            return

        guild_id = str(
            interaction.guild.id
        )

        giveaways = get_giveaway_data(
            guild_id
        )

        giveaways[giveaway_id] = {
            "message_id": message.id,
            "channel_id": channel.id,
            "prize": prize,
            "winners": winners,
            "host_id": interaction.user.id,
            "end_time": end_timestamp,
            "participants": [],
            "ended": False
        }

        save_giveaway_data(
            guild_id,
            giveaways
        )

        task = asyncio.create_task(
            self.finish_giveaway(
                interaction.guild.id,
                giveaway_id
            )
        )

        self.tasks[giveaway_id] = task

        await interaction.followup.send(
            embed=success_embed(
                "Giveaway Created",
                f"Giveaway created in {channel.mention}."
            ),
            ephemeral=True
        )

    async def finish_giveaway(
        self,
        guild_id: int,
        giveaway_id: str
    ):

        guild_id = str(guild_id)

        giveaways = get_giveaway_data(
            guild_id
        )

        giveaway = giveaways.get(
            giveaway_id
        )

        if giveaway is None:
            return

        remaining = (
            giveaway["end_time"]
            - int(time.time())
        )

        if remaining > 0:
            await asyncio.sleep(
                remaining
            )

        giveaways = get_giveaway_data(
            guild_id
        )

        giveaway = giveaways.get(
            giveaway_id
        )

        if giveaway is None:
            return

        if giveaway["ended"]:
            return

        participants = giveaway.get(
            "participants",
            []
        )

        giveaway["ended"] = True

        save_giveaway_data(
            guild_id,
            giveaways
        )

        guild = self.bot.get_guild(
            int(guild_id)
        )

        if guild is None:
            return

        channel = guild.get_channel(
            giveaway["channel_id"]
        )

        if channel is None:
            return

        try:
            message = await channel.fetch_message(
                giveaway["message_id"]
            )
        except discord.HTTPException:
            message = None

        if not participants:

            if message:

                ended_embed = giveaway_embed(
                    prize=giveaway["prize"],
                    winners=giveaway["winners"],
                    end_text="Ended",
                    host=guild.get_member(
                        giveaway["host_id"]
                    ) or guild.me
                )

                ended_embed.add_field(
                    name="👥 Entries",
                    value="`0`",
                    inline=False
                )

                ended_embed.add_field(
                    name="🏆 Winner",
                    value="No valid entries.",
                    inline=False
                )

                await message.edit(
                    embed=ended_embed,
                    view=None
                )

            return

        winner_count = min(
            giveaway["winners"],
            len(participants)
        )

        selected = random.sample(
            participants,
            winner_count
        )

        mentions = " ".join(
            f"<@{user_id}>"
            for user_id in selected
        )

        if message:

            ended_embed = giveaway_embed(
                prize=giveaway["prize"],
                winners=giveaway["winners"],
                end_text="Ended",
                host=guild.get_member(
                    giveaway["host_id"]
                ) or guild.me
            )

            ended_embed.add_field(
                name="👥 Entries",
                value=f"`{len(participants)}`",
                inline=False
            )

            ended_embed.add_field(
                name="🏆 Winner(s)",
                value=mentions,
                inline=False
            )

            await message.edit(
                embed=ended_embed,
                view=None
            )

        await channel.send(
            f"🎉 Congratulations {mentions}!\n"
            f"You won **{giveaway['prize']}**!"
        )

    @app_commands.command(
        name="giveaway-reroll",
        description="Reroll a giveaway winner."
    )
    @app_commands.describe(
        message="The giveaway message."
    )
    async def giveaway_reroll(
        self,
        interaction: discord.Interaction,
        message: discord.Message
    ):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=error_embed(
                    "No Permission",
                    "You need Administrator permission."
                ),
                ephemeral=True
            )
            return

        guild_id = str(
            interaction.guild.id
        )

        giveaways = get_giveaway_data(
            guild_id
        )

        giveaway = None
        giveaway_id = None

        for gid, data in giveaways.items():

            if data["message_id"] == message.id:

                giveaway = data
                giveaway_id = gid
                break

        if giveaway is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "Giveaway Not Found",
                    "That message is not a saved giveaway."
                ),
                ephemeral=True
            )
            return

        if not giveaway["ended"]:
            await interaction.response.send_message(
                embed=error_embed(
                    "Giveaway Active",
                    "You can only reroll an ended giveaway."
                ),
                ephemeral=True
            )
            return

        participants = giveaway.get(
            "participants",
            []
        )

        if not participants:
            await interaction.response.send_message(
                embed=error_embed(
                    "No Participants",
                    "There are no participants to reroll."
                ),
                ephemeral=True
            )
            return

        winner_id = random.choice(
            participants
        )

        await interaction.response.send_message(
            embed=success_embed(
                "Giveaway Rerolled",
                f"🎉 New winner: <@{winner_id}>"
            )
        )

        await message.channel.send(
            f"🎉 New giveaway winner: <@{winner_id}>!\n"
            f"Prize: **{giveaway['prize']}**"
        )


async def setup(bot):
    await bot.add_cog(
        Giveaway(bot)
    )