import asyncio

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


# ==========================================
# INVITES COG
# ==========================================

class Invites(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        # Guild ID -> {
        #     invite_code: uses
        # }
        self.invite_cache = {}

        # Prevent multiple refresh operations
        self.refresh_locks = {}

    # ==========================================
    # GET LOCK
    # ==========================================

    def get_refresh_lock(
        self,
        guild_id: int
    ):

        if guild_id not in self.refresh_locks:

            self.refresh_locks[guild_id] = (
                asyncio.Lock()
            )

        return self.refresh_locks[guild_id]

    # ==========================================
    # REFRESH INVITES
    # ==========================================

    async def refresh_invites(
        self,
        guild: discord.Guild
    ):

        lock = self.get_refresh_lock(
            guild.id
        )

        async with lock:

            try:

                invites = await guild.invites()

            except discord.Forbidden:

                print(
                    f"⚠️ Missing permission to read invites "
                    f"in {guild.name}"
                )

                return False

            except discord.HTTPException as error:

                print(
                    f"⚠️ Failed to refresh invites "
                    f"in {guild.name}: {error}"
                )

                return False

            except Exception as error:

                print(
                    f"⚠️ Unexpected invite refresh error "
                    f"in {guild.name}: {error}"
                )

                return False

            self.invite_cache[guild.id] = {

                invite.code: (
                    invite.uses or 0
                )

                for invite in invites
            }

            return True

    # ==========================================
    # READY
    # ==========================================

    @commands.Cog.listener()
    async def on_ready(self):

        print(
            "🔄 Loading invite cache..."
        )

        for guild in self.bot.guilds:

            try:

                await self.refresh_invites(
                    guild
                )

            except Exception as error:

                print(
                    f"⚠️ Invite cache error "
                    f"in {guild.name}: {error}"
                )

        print(
            "✅ Invite cache ready."
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

        # ======================================
        # GET CURRENT INVITES
        # ======================================

        try:

            current_invites = await guild.invites()

        except discord.Forbidden:

            print(
                f"⚠️ Cannot detect invite used in "
                f"{guild.name}: missing permission."
            )

            return

        except discord.HTTPException:

            return

        except Exception as error:

            print(
                f"⚠️ Invite detection error: {error}"
            )

            return

        # ======================================
        # OLD CACHE
        # ======================================

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

        # ======================================
        # NO INVITE FOUND
        # ======================================

        if used_invite is None:

            return

        # ======================================
        # GET INVITER
        # ======================================

        inviter = used_invite.inviter

        if inviter is None:

            return

        guild_id = str(
            guild.id
        )

        inviter_id = str(
            inviter.id
        )

        member_id = str(
            member.id
        )

        # ======================================
        # DATABASE
        # ======================================

        try:

            data = await asyncio.to_thread(
                get_invite_data,
                guild_id
            )

        except Exception as error:

            print(
                f"⚠️ Failed to load invite data: {error}"
            )

            return

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

        # ======================================
        # PREVENT DUPLICATE
        # ======================================

        if member_id not in user_data["members"]:

            user_data["joined"] += 1

            user_data["members"].append(
                member_id
            )

        # ======================================
        # SAVE
        # ======================================

        try:

            await asyncio.to_thread(
                save_invite_data,
                guild_id,
                data
            )

        except Exception as error:

            print(
                f"⚠️ Failed to save invite data: {error}"
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

        # ======================================
        # LOAD DATABASE
        # ======================================

        try:

            data = await asyncio.to_thread(
                get_invite_data,
                guild_id
            )

        except Exception as error:

            print(
                f"⚠️ Failed to load invite data: {error}"
            )

            return

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

                inviter_id = current_inviter_id

                break

        # ======================================
        # NOT FOUND
        # ======================================

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

        # ======================================
        # SAVE
        # ======================================

        try:

            await asyncio.to_thread(
                save_invite_data,
                guild_id,
                data
            )

        except Exception as error:

            print(
                f"⚠️ Failed to save invite data: {error}"
            )

    # ==========================================
    # /INVITES
    # ==========================================

    @app_commands.command(
        name="invites",
        description="Show invite statistics."
    )
    @app_commands.describe(
        member="Optional member to check."
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
        # DEFER IMMEDIATELY
        # ======================================

        try:

            await interaction.response.defer()

        except discord.HTTPException:

            return

        # ======================================
        # TARGET MEMBER
        # ======================================

        target = (
            member
            if member is not None
            else interaction.user
        )

        guild_id = str(
            interaction.guild.id
        )

        user_id = str(
            target.id
        )

        # ======================================
        # LOAD DATABASE
        # ======================================

        try:

            data = await asyncio.to_thread(
                get_invite_data,
                guild_id
            )

        except Exception as error:

            print(
                f"❌ Invite database error: {error}"
            )

            await interaction.followup.send(
                embed=error_embed(
                    "Database Error",
                    "I couldn't load the invite statistics."
                )
            )

            return

        # ======================================
        # USER DATA
        # ======================================

        user_data = data.get(
            user_id,
            {
                "joined": 0,
                "left": 0,
                "members": []
            }
        )

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

        try:

            embed = invite_embed(
                member=target,
                total=total,
                joined=joined,
                left=left
            )

        except Exception as error:

            print(
                f"❌ Invite embed error: {error}"
            )

            await interaction.followup.send(
                embed=error_embed(
                    "Embed Error",
                    "I couldn't create the invite statistics message."
                )
            )

            return

        # ======================================
        # PUBLIC RESPONSE
        # ======================================

        try:

            await interaction.followup.send(
                embed=embed
            )

        except discord.HTTPException as error:

            print(
                f"❌ Failed to send invite stats: {error}"
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

        except discord.HTTPException:

            return

        guild_id = str(
            interaction.guild.id
        )

        # ======================================
        # LOAD DATABASE
        # ======================================

        try:

            data = await asyncio.to_thread(
                get_invite_data,
                guild_id
            )

        except Exception as error:

            print(
                f"❌ Leaderboard database error: {error}"
            )

            await interaction.followup.send(
                embed=error_embed(
                    "Database Error",
                    "I couldn't load the invite leaderboard."
                )
            )

            return

        entries = []

        # ======================================
        # BUILD ENTRIES
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
        # TOP 10
        # ======================================

        top_entries = entries[:10]

        # ======================================
        # CREATE EMBED
        # ======================================

        try:

            embed = invite_leaderboard_embed(
                top_entries
            )

        except Exception as error:

            print(
                f"❌ Leaderboard embed error: {error}"
            )

            await interaction.followup.send(
                embed=error_embed(
                    "Embed Error",
                    "I couldn't create the leaderboard."
                )
            )

            return

        # ======================================
        # PUBLIC RESPONSE
        # ======================================

        try:

            await interaction.followup.send(
                embed=embed
            )

        except discord.HTTPException as error:

            print(
                f"❌ Failed to send leaderboard: {error}"
            )


# ==========================================
# SETUP
# ==========================================

async def setup(bot):

    await bot.add_cog(
        Invites(
            bot
        )
    )
```
