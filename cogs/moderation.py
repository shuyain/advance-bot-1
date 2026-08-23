from datetime import timedelta
import re

import discord
from discord.ext import commands
from discord import app_commands

from config import OWNER_ID

from utils.database import (
    set_activity_log_channel,
    get_activity_log_channel
)

from utils.embeds import (
    success_embed,
    error_embed,
    moderation_embed
)


# ==========================================
# PERMISSION CHECK
# ==========================================

def is_admin(
    interaction: discord.Interaction
) -> bool:

    if interaction.guild is None:
        return False

    if interaction.user.id == OWNER_ID:
        return True

    return interaction.user.guild_permissions.administrator


# ==========================================
# TIMEOUT PARSER
# ==========================================

def parse_timeout_duration(
    duration: str
):

    match = re.fullmatch(
        r"(\d+)\s*(s|m|h|d|w)",
        duration.lower().strip()
    )

    if not match:
        return None

    value = int(
        match.group(1)
    )

    unit = match.group(2)

    multipliers = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
        "w": 604800
    }

    return value * multipliers[unit]


# ==========================================
# MODERATION COG
# ==========================================

class Moderation(commands.Cog):

    def __init__(
        self,
        bot
    ):

        self.bot = bot

    # ======================================
    # ACTIVITY LOG
    # ======================================

    async def send_activity_log(
        self,
        guild: discord.Guild,
        action: str,
        user: discord.Member,
        moderator: discord.Member,
        reason: str
    ):

        channel_id = get_activity_log_channel(
            guild.id
        )

        if not channel_id:
            return False

        try:

            channel = guild.get_channel(
                int(channel_id)
            )

        except (
            TypeError,
            ValueError
        ):

            return False

        if channel is None:
            return False

        embed = moderation_embed(
            action=action,
            user=user,
            moderator=moderator,
            reason=reason
        )

        try:

            await channel.send(
                embed=embed
            )

            return True

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            return False

    # ======================================
    # /ACTIVITYLOG
    # ======================================

    @app_commands.command(
        name="activitylog",
        description="Set the moderation activity log channel."
    )
    @app_commands.describe(
        channel="Channel where moderation logs will be sent."
    )
    async def activitylog(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        if not is_admin(
            interaction
        ):

            await interaction.response.send_message(
                embed=error_embed(
                    "No Permission",
                    "You need Administrator permission to use this command."
                ),
                ephemeral=True
            )

            return

        set_activity_log_channel(
            interaction.guild.id,
            channel.id
        )

        await interaction.response.send_message(
            embed=success_embed(
                "Activity Log Updated",
                f"Moderation logs will now be sent to {channel.mention}."
            ),
            ephemeral=True
        )

    # ======================================
    # /KICK
    # ======================================

    @app_commands.command(
        name="kick",
        description="Kick a member from the server."
    )
    @app_commands.describe(
        user="Member to kick.",
        reason="Reason for the kick."
    )
    async def kick(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str
    ):

        if not is_admin(
            interaction
        ):

            await interaction.response.send_message(
                embed=error_embed(
                    "No Permission",
                    "You need Administrator permission to use this command."
                ),
                ephemeral=True
            )

            return

        if user.id == interaction.user.id:

            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Target",
                    "You cannot kick yourself."
                ),
                ephemeral=True
            )

            return

        if user.id == self.bot.user.id:

            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Target",
                    "I cannot kick myself."
                ),
                ephemeral=True
            )

            return

        if not user.kickable:

            await interaction.response.send_message(
                embed=error_embed(
                    "Cannot Kick",
                    "I cannot kick this member. "
                    "Check the bot's role position."
                ),
                ephemeral=True
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        try:

            await user.kick(
                reason=reason
            )

        except discord.Forbidden:

            await interaction.followup.send(
                embed=error_embed(
                    "Kick Failed",
                    "Discord denied the kick action."
                ),
                ephemeral=True
            )

            return

        except discord.HTTPException:

            await interaction.followup.send(
                embed=error_embed(
                    "Kick Failed",
                    "Discord rejected the kick request."
                ),
                ephemeral=True
            )

            return

        await self.send_activity_log(
            guild=interaction.guild,
            action="Kicked",
            user=user,
            moderator=interaction.user,
            reason=reason
        )

        await interaction.followup.send(
            embed=success_embed(
                "Member Kicked",
                f"{user.mention} was kicked successfully."
            ),
            ephemeral=True
        )

    # ======================================
    # /BAN
    # ======================================

    @app_commands.command(
        name="ban",
        description="Ban a member from the server."
    )
    @app_commands.describe(
        user="Member to ban.",
        reason="Reason for the ban."
    )
    async def ban(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str
    ):

        if not is_admin(
            interaction
        ):

            await interaction.response.send_message(
                embed=error_embed(
                    "No Permission",
                    "You need Administrator permission to use this command."
                ),
                ephemeral=True
            )

            return

        if user.id == interaction.user.id:

            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Target",
                    "You cannot ban yourself."
                ),
                ephemeral=True
            )

            return

        if user.id == self.bot.user.id:

            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Target",
                    "I cannot ban myself."
                ),
                ephemeral=True
            )

            return

        if not user.banable:

            await interaction.response.send_message(
                embed=error_embed(
                    "Cannot Ban",
                    "I cannot ban this member. "
                    "Check the bot's role position."
                ),
                ephemeral=True
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        try:

            await user.ban(
                reason=reason,
                delete_message_days=0
            )

        except discord.Forbidden:

            await interaction.followup.send(
                embed=error_embed(
                    "Ban Failed",
                    "Discord denied the ban action."
                ),
                ephemeral=True
            )

            return

        except discord.HTTPException:

            await interaction.followup.send(
                embed=error_embed(
                    "Ban Failed",
                    "Discord rejected the ban request."
                ),
                ephemeral=True
            )

            return

        await self.send_activity_log(
            guild=interaction.guild,
            action="Banned",
            user=user,
            moderator=interaction.user,
            reason=reason
        )

        await interaction.followup.send(
            embed=success_embed(
                "Member Banned",
                f"{user.mention} was banned successfully."
            ),
            ephemeral=True
        )

    # ======================================
    # /TIMEOUT
    # ======================================

    @app_commands.command(
        name="timeout",
        description="Timeout a member."
    )
    @app_commands.describe(
        user="Member to timeout.",
        duration="Examples: 10s, 10m, 2h, 1d, 1w.",
        reason="Reason for the timeout."
    )
    async def timeout(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        duration: str,
        reason: str
    ):

        if not is_admin(
            interaction
        ):

            await interaction.response.send_message(
                embed=error_embed(
                    "No Permission",
                    "You need Administrator permission to use this command."
                ),
                ephemeral=True
            )

            return

        if user.id == interaction.user.id:

            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Target",
                    "You cannot timeout yourself."
                ),
                ephemeral=True
            )

            return

        if user.id == self.bot.user.id:

            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Target",
                    "I cannot timeout myself."
                ),
                ephemeral=True
            )

            return

        seconds = parse_timeout_duration(
            duration
        )

        if seconds is None:

            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Duration",
                    "Use `10s`, `10m`, `2h`, `1d`, or `1w`."
                ),
                ephemeral=True
            )

            return

        # Discord maximum timeout = 28 days

        if seconds > 28 * 86400:

            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Duration",
                    "Discord allows a maximum timeout of 28 days."
                ),
                ephemeral=True
            )

            return

        if not user.moderatable:

            await interaction.response.send_message(
                embed=error_embed(
                    "Cannot Timeout",
                    "I cannot timeout this member. "
                    "Check the bot's role position."
                ),
                ephemeral=True
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        timeout_until = (
            discord.utils.utcnow()
            + timedelta(
                seconds=seconds
            )
        )

        try:

            await user.timeout(
                timeout_until,
                reason=reason
            )

        except discord.Forbidden:

            await interaction.followup.send(
                embed=error_embed(
                    "Timeout Failed",
                    "Discord denied the timeout action."
                ),
                ephemeral=True
            )

            return

        except discord.HTTPException:

            await interaction.followup.send(
                embed=error_embed(
                    "Timeout Failed",
                    "Discord rejected the timeout request."
                ),
                ephemeral=True
            )

            return

        await self.send_activity_log(
            guild=interaction.guild,
            action="Timed Out",
            user=user,
            moderator=interaction.user,
            reason=(
                f"{reason}\n"
                f"Duration: `{duration}`"
            )
        )

        await interaction.followup.send(
            embed=success_embed(
                "Member Timed Out",
                f"{user.mention} was timed out for `{duration}`."
            ),
            ephemeral=True
        )


# ==========================================
# SETUP
# ==========================================

async def setup(bot):

    await bot.add_cog(
        Moderation(bot)
    )