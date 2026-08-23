import discord
from discord.ext import commands
from discord import app_commands

from utils.embeds import success_embed, error_embed


class General(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="send",
        description="Send a message to a selected channel."
    )
    @app_commands.describe(
        channel="The channel where the message will be sent.",
        message="The message to send."
    )
    async def send(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: str
    ):

        # Administrator check
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=error_embed(
                    "No Permission",
                    "You need Administrator permission to use this command."
                ),
                ephemeral=True
            )
            return

        try:
            await channel.send(message)

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

        await interaction.response.send_message(
            embed=success_embed(
                "Message Sent",
                f"Your message was sent to {channel.mention}."
            ),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(General(bot))