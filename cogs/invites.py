import discord

from discord.ext import commands

from discord import app_commands

from utils.database import (
    get_invite_data,
    save_invite_data
)

from utils.embeds import (
    error_embed,
    invite_embed,
    invite_leaderboard_embed
)


class Invites(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        # Cached Discord invite information
        self.invite_cache = {}

    # ==========================================
    # REFRESH INVITES
    # ==========================================

    async def refresh_invites(
        self,
        guild: discord.Guild
    ):
        """Refresh invite usage cache."""

        try:

            invites = await guild.invites()

        except discord.Forbidden:

            return

        except discord.HTTPException:

            return

        self.invite_cache[guild.id] = {
            invite.code: invite.uses or 0
            for invite in invites
        }

    # ==========================================
    # READY
    # ==========================================

    @commands.Cog.listener()
    async def on_ready(self):

        for guild in self.bot.guilds:

            await self.refresh_invites(
                guild
            )

    # ==========================================
    # INVITE CREATE
    # ==========================================

    @commands.Cog.listener()
    async def on_invite_create(
        self,
        invite: discord.Invite
    ):

        if invite.guild is None:

            return

        await self.refresh_invites(
            invite.guild
        )

    # ==========================================
    # INVITE DELETE
    # ==========================================

    @commands.Cog.listener()
    async def on_invite_delete(
        self,
        invite: discord.Invite
    ):

        if invite.guild is None:

            return

        await self.refresh_invites(
            invite.guild
        )

    # ==========================================
    # MEMBER JOIN
    # ==========================================

    @commands.Cog.listener()
    async def on_member_join(
        self,
        member: discord.Member
    ):

        guild = member.guild

        try:

            current_invites = await guild.invites()

        except discord.Forbidden:

            return

        except discord.HTTPException:

            return

        old_invites = self.invite_cache.get(
            guild.id,
            {}
        )

        used_invite = None

        for invite in current_invites:

            old_uses = old_invites.get(
                invite.code,
                0
            )

            new_uses = invite.uses or 0

            if new_uses > old_uses:

                used_invite = invite

                break

        # Update cache

        self.invite_cache[guild.id] = {
            invite.code: invite.uses or 0
            for invite in current_invites
        }

        if used_invite is None:

            return

        inviter = used_invite.inviter

        if inviter is None:

            return

        guild_id = str(
            guild.id
        )

        data = get_invite_data(
            guild_id
        )

        inviter_id = str(
            inviter.id
        )

        member_id = str(
            member.id
        )

        # ======================================
        # INVITER DATA
        # ======================================

        user_data = data.setdefault(
            inviter_id,
            {
                "joined": 0,
                "left": 0,
                "members": []
            }
        )

        user_data.setdefault(
            "joined",
            0
        )

        user_data.setdefault(
            "left",
            0
        )

        user_data.setdefault(
            "members",
            []
        )

        user_data["joined"] += 1

        # Save member -> inviter relationship

        if member_id not in user_data["members"]:

            user_data["members"].append(
                member_id
            )

        save_invite_data(
            guild_id,
            data
        )

    # ==========================================
    # MEMBER LEAVE
    # ==========================================

    @commands.Cog.listener()
    async def on_member_remove(
        self,
        member: discord.Member
    ):

        guild_id = str(
            member.guild.id
        )

        member_id = str(
            member.id
        )

        data = get_invite_data(
            guild_id
        )

        inviter_id = None

        # Find which inviter invited this member

        for current_inviter_id, user_data in data.items():

            if not isinstance(
                user_data,
                dict
            ):

                continue

            members = user_data.get(
                "members",
                []
            )

            if member_id in members:

                inviter_id = current_inviter_id

                break

        if inviter_id is None:

            return

        inviter_data = data.get(
            inviter_id
        )

        if not isinstance(
            inviter_data,
            dict
        ):

            return

        inviter_data.setdefault(
            "joined",
            0
        )

        inviter_data.setdefault(
            "left",
            0
        )

        inviter_data.setdefault(
            "members",
            []
        )

        # Increase leave count

        inviter_data["left"] += 1

        # Remove member relationship

        if member_id in inviter_data["members"]:

            inviter_data["members"].remove(
                member_id
            )

        save_invite_data(
            guild_id,
            data
        )

    # ==========================================
    # /INVITES
    # ==========================================

    @app_commands.command(
        name="invites",
        description="Show your invite statistics."
    )
    async def invites(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                embed=error_embed(
                    "Server Only",
                    "This command can only be used inside a server."
                ),
                ephemeral=True
            )

            return

        guild_id = str(
            interaction.guild.id
        )

        data = get_invite_data(
            guild_id
        )

        user_id = str(
            interaction.user.id
        )

        user_data = data.get(
            user_id,
            {
                "joined": 0,
                "left": 0,
                "members": []
            }
        )

        joined = user_data.get(
            "joined",
            0
        )

        left = user_data.get(
            "left",
            0
        )

        total = max(
            joined - left,
            0
        )

        embed = invite_embed(
            member=interaction.user,
            total=total,
            joined=joined,
            left=left
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    # ==========================================
    # /LEADERBOARD-INVITES
    # ==========================================

    @app_commands.command(
        name="leaderboard-invites",
        description="Show the top 10 invite leaderboard."
    )
    async def leaderboard_invites(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                embed=error_embed(
                    "Server Only",
                    "This command can only be used inside a server."
                ),
                ephemeral=True
            )

            return

        guild_id = str(
            interaction.guild.id
        )

        data = get_invite_data(
            guild_id
        )

        entries = []

        for user_id, user_data in data.items():

            if not isinstance(
                user_data,
                dict
            ):

                continue

            joined = user_data.get(
                "joined",
                0
            )

            left = user_data.get(
                "left",
                0
            )

            total = max(
                joined - left,
                0
            )

            entries.append(
                {
                    "user_id": user_id,
                    "invites": total
                }
            )

        entries.sort(
            key=lambda item: item["invites"],
            reverse=True
        )

        embed = invite_leaderboard_embed(
            entries[:10]
        )

        await interaction.response.send_message(
            embed=embed
        )


# ==========================================
# SETUP
# ==========================================

async def setup(bot):

    await bot.add_cog(
        Invites(bot)
    )