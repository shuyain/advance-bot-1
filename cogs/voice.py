import discord
from discord.ext import commands
from discord import app_commands

from utils.embeds import success_embed, error_embed


class Voice(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="join-vc",
        description="Join the voice channel you are currently in."
    )
    async def join_vc(
        self,
        interaction: discord.Interaction
    ):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=error_embed(
                    "No Permission",
                    "You need Administrator permission to use this command."
                ),
                ephemeral=True
            )
            return

        if not isinstance(
            interaction.user,
            discord.Member
        ):
            await interaction.response.send_message(
                embed=error_embed(
                    "Error",
                    "This command can only be used inside a server."
                ),
                ephemeral=True
            )
            return

        voice_state = interaction.user.voice

        if voice_state is None or voice_state.channel is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "Not In Voice",
                    "You must be inside a Voice Channel first."
                ),
                ephemeral=True
            )
            return

        channel = voice_state.channel

        try:
            voice_client = interaction.guild.voice_client

            if voice_client is not None:

                if voice_client.channel.id == channel.id:
                    await interaction.response.send_message(
                        embed=error_embed(
                            "Already Connected",
                            f"I am already in {channel.mention}."
                        ),
                        ephemeral=True
                    )
                    return

                await voice_client.move_to(channel)

            else:
                voice_client = await channel.connect()

            await voice_client.guild.change_voice_state(
                channel=channel,
                self_mute=True,
                self_deaf=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                embed=error_embed(
                    "Permission Error",
                    f"I don't have permission to join {channel.mention}."
                ),
                ephemeral=True
            )
            return

        except discord.ClientException:
            await interaction.response.send_message(
                embed=error_embed(
                    "Voice Error",
                    "I couldn't connect to the Voice Channel."
                ),
                ephemeral=True
            )
            return

        except Exception:
            await interaction.response.send_message(
                embed=error_embed(
                    "Voice Error",
                    "Something went wrong while connecting."
                ),
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            embed=success_embed(
                "Joined Voice Channel",
                f"Connected to {channel.mention}.\n"
                "🔇 Self-Muted\n"
                "🔕 Self-Deafened"
            ),
            ephemeral=True
        )

    @app_commands.command(
        name="left-vc",
        description="Leave the current voice channel."
    )
    async def left_vc(
        self,
        interaction: discord.Interaction
    ):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=error_embed(
                    "No Permission",
                    "You need Administrator permission to use this command."
                ),
                ephemeral=True
            )
            return

        voice_client = interaction.guild.voice_client

        if voice_client is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "Not Connected",
                    "I am not connected to any Voice Channel."
                ),
                ephemeral=True
            )
            return

        channel_name = voice_client.channel.name

        try:
            await voice_client.disconnect()

        except discord.ClientException:
            await interaction.response.send_message(
                embed=error_embed(
                    "Voice Error",
                    "I couldn't leave the Voice Channel."
                ),
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            embed=success_embed(
                "Left Voice Channel",
                f"I left **{channel_name}**."
            ),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Voice(bot))