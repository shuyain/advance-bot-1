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


# ==========================================
# DURATION
# ==========================================

def parse_duration(duration: str):
    """Convert duration text into seconds."""

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


# ==========================================
# GIVEAWAY BUTTON
# ==========================================

class GiveawayView(discord.ui.View):

    def __init__(self, giveaway_id: str):

        super().__init__(
            timeout=None
        )

        self.giveaway_id = giveaway_id

        # Unique button ID for each giveaway
        self.children[0].custom_id = (
            f"giveaway_enter:{giveaway_id}"
        )

    @discord.ui.button(
        label="Enter Giveaway",
        emoji="🎉",
        style=discord.ButtonStyle.primary
    )
    async def enter_giveaway(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                embed=error_embed(
                    "Server Only",
                    "This button can only be used inside a server."
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

        if giveaway.get(
            "ended",
            False
        ):

            await interaction.response.send_message(
                embed=error_embed(
                    "Giveaway Ended",
                    "This giveaway has already ended."
                ),
                ephemeral=True
            )

            return

        user_id = str(
            interaction.user.id
        )

        participants = giveaway.setdefault(
            "participants",
            []
        )

        # ==================================
        # LEAVE
        # ==================================

        if user_id in participants:

            participants.remove(
                user_id
            )

            save_giveaway_data(
                guild_id,
                giveaways
            )

            await interaction.response.send_message(
                "❌ You left the giveaway.",
                ephemeral=True
            )

            return

        # ==================================
        # ENTER
        # ==================================

        participants.append(
            user_id
        )

        save_giveaway_data(
            guild_id,
            giveaways
        )

        await interaction.response.send_message(
            "🎉 You entered the giveaway!",
            ephemeral=True
        )


# ==========================================
# GIVEAWAY COG
# ==========================================

class Giveaway(commands.Cog):

    giveaway = app_commands.Group(
        name="giveaway",
        description="Giveaway commands."
    )

    def __init__(
        self,
        bot
    ):

        self.bot = bot

        self.tasks = {}

        self.restored = False

    # ======================================
    # RESTORE
    # ======================================

    async def restore_giveaways(self):

        if self.restored:
            return

        self.restored = True

        for guild in self.bot.guilds:

            guild_id = str(
                guild.id
            )

            giveaways = get_giveaway_data(
                guild_id
            )

            for giveaway_id, giveaway in giveaways.items():

                if giveaway.get(
                    "ended",
                    False
                ):
                    continue

                message_id = giveaway.get(
                    "message_id"
                )

                if message_id:

                    try:

                        self.bot.add_view(
                            GiveawayView(
                                giveaway_id
                            ),
                            message_id=message_id
                        )

                    except Exception as error:

                        print(
                            f"⚠️ Failed to restore giveaway "
                            f"{giveaway_id}: {error}"
                        )

                if giveaway_id in self.tasks:
                    continue

                task = asyncio.create_task(
                    self.finish_giveaway(
                        guild.id,
                        giveaway_id
                    )
                )

                self.tasks[
                    giveaway_id
                ] = task

        print(
            "🔄 Active giveaways restored."
        )

    # ======================================
    # CREATE
    # ======================================

    @giveaway.command(
        name="create",
        description="Create a giveaway."
    )
    @app_commands.describe(
        prize="Giveaway prize.",
        duration="Duration: 10s, 10m, 2h, 1d.",
        winners="Number of winners.",
        channel="Giveaway channel.",
        image="Optional image URL."
    )
    async def create(
        self,
        interaction: discord.Interaction,
        prize: str,
        duration: str,
        winners: int,
        channel: discord.TextChannel,
        image: str | None = None
    ):

        # ==================================
        # PERMISSION
        # ==================================

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                embed=error_embed(
                    "No Permission",
                    "You need Administrator permission."
                ),
                ephemeral=True
            )

            return

        # ==================================
        # DURATION
        # ==================================

        seconds = parse_duration(
            duration
        )

        if seconds is None:

            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Duration",
                    "Use `10s`, `10m`, `2h`, or `1d`."
                ),
                ephemeral=True
            )

            return

        if seconds < 10:

            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Duration",
                    "Giveaway must run for at least 10 seconds."
                ),
                ephemeral=True
            )

            return

        # ==================================
        # WINNERS
        # ==================================

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

        # ==================================
        # DEFER
        # ==================================

        await interaction.response.defer(
            ephemeral=True
        )

        # ==================================
        # GIVEAWAY ID
        # ==================================

        giveaway_id = (
            f"{interaction.guild.id}-"
            f"{int(time.time() * 1000)}"
        )

        end_timestamp = int(
            time.time() + seconds
        )

        end_text = (
            f"<t:{end_timestamp}:R>\n"
            f"<t:{end_timestamp}:F>"
        )

        # ==================================
        # EMBED
        # ==================================

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

        # ==================================
        # SEND GIVEAWAY
        # ==================================

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

        # ==================================
        # DATABASE
        # ==================================

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

        # ==================================
        # FINISH TASK
        # ==================================

        task = asyncio.create_task(
            self.finish_giveaway(
                interaction.guild.id,
                giveaway_id
            )
        )

        self.tasks[
            giveaway_id
        ] = task

        # ==================================
        # SUCCESS
        # ==================================

        await interaction.followup.send(
            embed=success_embed(
                "Giveaway Created",
                f"Giveaway created in {channel.mention}."
            ),
            ephemeral=True
        )

    # ======================================
    # FINISH GIVEAWAY
    # ======================================

    async def finish_giveaway(
        self,
        guild_id: int,
        giveaway_id: str
    ):

        guild_id = str(
            guild_id
        )

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

            try:

                await asyncio.sleep(
                    remaining
                )

            except asyncio.CancelledError:

                return

        # Reload database
        giveaways = get_giveaway_data(
            guild_id
        )

        giveaway = giveaways.get(
            giveaway_id
        )

        if giveaway is None:
            return

        if giveaway.get(
            "ended",
            False
        ):
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

        # ==================================
        # GUILD
        # ==================================

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

        # ==================================
        # MESSAGE
        # ==================================

        message = None

        try:

            message = await channel.fetch_message(
                giveaway["message_id"]
            )

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException
        ):

            pass

        # ==================================
        # HOST
        # ==================================

        host = (
            guild.get_member(
                giveaway["host_id"]
            )
            or guild.me
        )

        # ==================================
        # NO PARTICIPANTS
        # ==================================

        if not participants:

            if message:

                ended_embed = giveaway_embed(
                    prize=giveaway["prize"],
                    winners=giveaway["winners"],
                    end_text="Ended",
                    host=host
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

                try:

                    await message.edit(
                        embed=ended_embed,
                        view=None
                    )

                except discord.HTTPException:

                    pass

            return

        # ==================================
        # SELECT WINNERS
        # ==================================

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

        # ==================================
        # UPDATE EMBED
        # ==================================

        if message:

            ended_embed = giveaway_embed(
                prize=giveaway["prize"],
                winners=giveaway["winners"],
                end_text="Ended",
                host=host
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

            try:

                await message.edit(
                    embed=ended_embed,
                    view=None
                )

            except discord.HTTPException:

                pass

        # ==================================
        # WINNER ANNOUNCEMENT
        # ==================================

        try:

            await channel.send(
                f"🎉 Congratulations {mentions}!\n"
                f"You won **{giveaway['prize']}**!"
            )

        except discord.HTTPException:

            pass

    # ======================================
    # REROLL
    # ======================================

    @giveaway.command(
        name="reroll",
        description="Reroll an ended giveaway."
    )
    @app_commands.describe(
        message_id="The giveaway message ID."
    )
    async def reroll(
        self,
        interaction: discord.Interaction,
        message_id: str
    ):

        # ==================================
        # PERMISSION
        # ==================================

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                embed=error_embed(
                    "No Permission",
                    "You need Administrator permission."
                ),
                ephemeral=True
            )

            return

        # ==================================
        # MESSAGE ID
        # ==================================

        if not message_id.isdigit():

            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Message ID",
                    "Please provide a valid Discord message ID."
                ),
                ephemeral=True
            )

            return

        message_id_int = int(
            message_id
        )

        # ==================================
        # DATABASE
        # ==================================

        guild_id = str(
            interaction.guild.id
        )

        giveaways = get_giveaway_data(
            guild_id
        )

        giveaway = None

        for data in giveaways.values():

            if data.get(
                "message_id"
            ) == message_id_int:

                giveaway = data

                break

        # ==================================
        # NOT FOUND
        # ==================================

        if giveaway is None:

            await interaction.response.send_message(
                embed=error_embed(
                    "Giveaway Not Found",
                    "That message is not a saved giveaway."
                ),
                ephemeral=True
            )

            return

        # ==================================
        # ACTIVE
        # ==================================

        if not giveaway.get(
            "ended",
            False
        ):

            await interaction.response.send_message(
                embed=error_embed(
                    "Giveaway Active",
                    "You can only reroll an ended giveaway."
                ),
                ephemeral=True
            )

            return

        # ==================================
        # PARTICIPANTS
        # ==================================

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

        # ==================================
        # NEW WINNER
        # ==================================

        winner_id = random.choice(
            participants
        )

        await interaction.response.send_message(
            embed=success_embed(
                "Giveaway Rerolled",
                f"🎉 New winner: <@{winner_id}>"
            )
        )

        # ==================================
        # CHANNEL
        # ==================================

        channel = interaction.guild.get_channel(
            giveaway.get(
                "channel_id"
            )
        )

        if channel is None:
            return

        try:

            await channel.send(
                f"🎉 New giveaway winner: <@{winner_id}>!\n"
                f"Prize: **{giveaway['prize']}**"
            )

        except discord.HTTPException:

            pass


# ==========================================
# SETUP
# ==========================================

async def setup(bot):

    cog = Giveaway(
        bot
    )

    await bot.add_cog(
        cog
    )

    # Restore active giveaways
    await cog.restore_giveaways()
