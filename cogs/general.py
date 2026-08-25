import discord
from discord.ext import commands
from discord import app_commands

from utils.embeds import success_embed, error_embed


class General(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ==========================================
    # SEND MESSAGE
    # ==========================================

    @app_commands.command(
        name="send",
        description="Send a message to a selected channel."
    )
    @app_commands.describe(
        channel="The channel where the message will be sent.",
        message="Use | between sections to create spacing."
    )
    async def send(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: str
    ):

        # ======================================
        # ADMIN CHECK
        # ======================================

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                embed=error_embed(
                    "No Permission",
                    "You need Administrator permission to use this command."
                ),
                ephemeral=True
            )

            return

        # ======================================
        # FORMAT MESSAGE
        # ======================================

        # Convert | into blank lines
        formatted_message = message.replace(
            "|",
            "\n\n"
        )

        # ======================================
        # EMPTY MESSAGE CHECK
        # ======================================

        if not formatted_message.strip():

            await interaction.response.send_message(
                embed=error_embed(
                    "Empty Message",
                    "Please provide a message to send."
                ),
                ephemeral=True
            )

            return

        # ======================================
        # DISCORD MESSAGE LIMIT
        # ======================================

        if len(formatted_message) > 2000:

            await interaction.response.send_message(
                embed=error_embed(
                    "Message Too Long",
                    "Discord messages cannot be longer than 2000 characters."
                ),
                ephemeral=True
            )

            return

        # ======================================
        # SEND
        # ======================================

        try:

            await channel.send(
                formatted_message
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                embed=error_embed(
                    "Send Failed",
                    f"I don't have permission to send messages in {channel.mention}."
                ),
                ephemeral=True
            )

            return

        except discord.HTTPException:

            await interaction.response.send_message(
                embed=error_embed(
                    "Send Failed",
                    "Discord rejected the message."
                ),
                ephemeral=True
            )

            return

        # ======================================
        # SUCCESS
        # ======================================

        await interaction.response.send_message(
            embed=success_embed(
                "Message Sent",
                f"Your message was sent to {channel.mention}."
            ),
            ephemeral=True
        )


# ==========================================
# SETUP
# ==========================================

async def setup(bot):

    await bot.add_cog(
        General(bot)
    )
