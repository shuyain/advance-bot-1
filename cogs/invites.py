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

        # guild_id -> {
        #     invite_code: uses
        # }
        self.invite_cache = {}

    # ==========================================
    # REFRESH INVITE CACHE
    # ==========================================

    async def refresh_invites(
        self,
        guild: discord.Guild
    ):
        """Refresh Discord invite usage cache."""

        try:
            invites = await guild.invites()

        except (
            discord.Forbidden,
            discord.HTTPException
        ):
            return

        self.invite_cache[guild.id] = {
            invite.code: (
                invite.uses or 0
            )
            for invite in invites
        }

    # ==========================================
    # READY
    # ==========================================

    @commands.Cog.listener()
    async def on_ready(self):

        for guild in self.bot.guilds:
            await self.refresh_invites(guild)

        print(
            "🔗 Invite tracking initialized."
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

        except (
            discord.Forbidden,
            discord.HTTPException
        ):
            return

        old_invites = self.invite_cache.get(
            guild.id,
            {}
        )

        used_invite = None

        # ======================================
        # FIND USED INVITE
        # ======================================

        for invite in current_invites:

            old_uses = old_invites.get(
                invite.code,
                0
            )

            new_uses = invite.uses or 0

            if new_uses > old_uses:
                used_invite = invite
                break

        # ======================================
        # UPDATE CACHE
        # ======================================

        self.invite_cache[guild.id] = {
            invite.code: (
                invite.uses or 0
            )
            for invite in current_invites
        }

        if used_invite is None:
            return

        inviter = used_invite.inviter

        if inviter is None:
            return

        # ======================================
        # LOAD DATA
        # ======================================

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
        # GET INVITER DATA
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

        # ======================================
        # PREVENT DUPLICATE
        # ======================================

        if member_id not in user_data["members"]:

            user_data["joined"] += 1

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

        # ======================================
        # FIND INVITER
        # ======================================

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

                inviter_id = (
                    current_inviter_id
                )

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

        # ======================================
        # UPDATE LEAVE
        # ======================================

        inviter_data["left"] += 1

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
        description="Show invite statistics."
    )
    @app_commands.describe(
        member="Check another member's invites."
    )
    async def invites(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None
    ):

        # ======================================
        # SERVER CHECK
        # ======================================

        if interaction.guild is None:

            await interaction.response.send_message(
                embed=error_embed(
                    "Server Only",
                    "This command can only be used inside a server."
                ),
                ephemeral=True
            )

            return

        # ======================================
        # DEFER
        # ======================================

        try:
            await interaction.response.defer()

        except discord.InteractionResponded:
            return

        # ======================================
        # TARGET MEMBER
        # ======================================

        target = (
            member
            if member is not None
            else interaction.user
        )

        # ======================================
        # LOAD DATA
        # ======================================

        guild_id = str(
            interaction.guild.id
        )

        data = get_invite_data(
            guild_id
        )

        user_id = str(
            target.id
        )

        user_data = data.get(
            user_id,
            {
                "joined": 0,
                "left": 0,
                "members": []
            }
        )

        if not isinstance(
            user_data,
            dict
        ):
            user_data = {
                "joined": 0,
                "left": 0,
                "members": []
            }

        # ======================================
        # STATS
        # ======================================

        joined = int(
            user_data.get(
                "joined",
                0
            )
        )

        left = int(
            user_data.get(
                "left",
                0
            )
        )

        total = max(
            joined - left,
            0
        )

        # ======================================
        # CREATE EMBED
        # ======================================

        embed = invite_embed(
            member=target,
            total=total,
            joined=joined,
            left=left
        )

        # ======================================
        # SEND PUBLIC RESPONSE
        # ======================================

        try:

            await interaction.followup.send(
                embed=embed
            )

        except discord.HTTPException as error:

            print(
                f"❌ /invites response failed: {error}"
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

        # ======================================
        # SERVER CHECK
        # ======================================

        if interaction.guild is None:

            await interaction.response.send_message(
                embed=error_embed(
                    "Server Only",
                    "This command can only be used inside a server."
                ),
                ephemeral=True
            )

            return

        # ======================================
        # DEFER
        # ======================================

        try:
            await interaction.response.defer()

        except discord.InteractionResponded:
            return

        # ======================================
        # LOAD DATA
        # ======================================

        guild_id = str(
            interaction.guild.id
        )

        data = get_invite_data(
            guild_id
        )

        entries = []

        # ======================================
        # BUILD LEADERBOARD
        # ======================================

        for user_id, user_data in data.items():

            if not isinstance(
                user_data,
                dict
            ):
                continue

            joined = int(
                user_data.get(
                    "joined",
                    0
                )
            )

            left = int(
                user_data.get(
                    "left",
                    0
                )
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

        # ======================================
        # SORT
        # ======================================

        entries.sort(
            key=lambda item: item["invites"],
            reverse=True
        )

        # ======================================
        # CREATE EMBED
        # ======================================

        embed = invite_leaderboard_embed(
            entries[:10]
        )

        # ======================================
        # SEND PUBLIC RESPONSE
        # ======================================

        try:

            await interaction.followup.send(
                embed=embed
            )

        except discord.HTTPException as error:

            print(
                f"❌ Leaderboard response failed: {error}"
            )

    # ==========================================
    # /INVITES-RESET
    # ==========================================

    @app_commands.command(
        name="invites-reset",
        description="Reset a member's invite statistics."
    )
    @app_commands.describe(
        member="Member whose invite statistics should be reset."
    )
    async def invites_reset(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        # ======================================
        # SERVER CHECK
        # ======================================

        if interaction.guild is None:

            await interaction.response.send_message(
                embed=error_embed(
                    "Server Only",
                    "This command can only be used inside a server."
                ),
                ephemeral=True
            )

            return

        # ======================================
        # ADMIN CHECK
        # ======================================

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                embed=error_embed(
                    "No Permission",
                    "You need Administrator permission."
                ),
                ephemeral=True
            )

            return

        # ======================================
        # DEFER
        # ======================================

        await interaction.response.defer(
            ephemeral=True
        )

        # ======================================
        # LOAD DATA
        # ======================================

        guild_id = str(
            interaction.guild.id
        )

        data = get_invite_data(
            guild_id
        )

        user_id = str(
            member.id
        )

        if user_id not in data:

            await interaction.followup.send(
                embed=error_embed(
                    "No Data",
                    f"No invite data found for {member.mention}."
                ),
                ephemeral=True
            )

            return

        # ======================================
        # RESET
        # ======================================

        data[user_id] = {
            "joined": 0,
            "left": 0,
            "members": []
        }

        save_invite_data(
            guild_id,
            data
        )

        # ======================================
        # SUCCESS
        # ======================================

        await interaction.followup.send(
            embed=discord.Embed(
                title="Invite Data Reset",
                description=(
                    f"Invite statistics for "
                    f"{member.mention} have been reset."
                ),
                color=discord.Color.green()
            ),
            ephemeral=True
        )


# ==========================================
# SETUP
# ==========================================

async def setup(bot):

    await bot.add_cog(
        Invites(bot)
    )
