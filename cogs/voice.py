import discord
from discord.ext import commands
from discord import app_commands

from utils.embeds import success_embed, error_embed


class Voice(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ==========================================
    # JOIN VC
    # ==========================================

    @app_commands.command(
        name="join-vc",
        description="Join the voice channel you are currently in."
    )
    async def join_vc(
        self,
        interaction: discord.Interaction
    ):

        # --------------------------------------
        # SERVER CHECK
        # --------------------------------------

        if interaction.guild is None:

            await interaction.response.send_message(
                embed=error_embed(
                    "Server Only",
                    "This command can only be used inside a server."
                ),
                ephemeral=True
            )

            return

        # --------------------------------------
        # ADMIN CHECK
        # --------------------------------------

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                embed=error_embed(
                    "No Permission",
                    "You need Administrator permission to use this command."
                ),
                ephemeral=True
            )

            return

        # --------------------------------------
        # USER VOICE CHECK
        # --------------------------------------

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

        # --------------------------------------
        # CHECK CHANNEL TYPE
        # --------------------------------------

        if not isinstance(
            channel,
            (discord.VoiceChannel, discord.StageChannel)
        ):

            await interaction.response.send_message(
                embed=error_embed(
                    "Invalid Channel",
                    "This is not a valid voice channel."
                ),
                ephemeral=True
            )

            return

        # --------------------------------------
        # BOT PERMISSIONS
        # --------------------------------------

        permissions = channel.permissions_for(
            interaction.guild.me
        )

        if not permissions.connect:

            await interaction.response.send_message(
                embed=error_embed(
                    "Permission Error",
                    f"I don't have **Connect** permission in {channel.mention}."
                ),
                ephemeral=True
            )

            return

        if not permissions.speak:

            await interaction.response.send_message(
                embed=error_embed(
                    "Permission Error",
                    f"I don't have **Speak** permission in {channel.mention}."
                ),
                ephemeral=True
            )

            return

        # --------------------------------------
        # DEFER
        # --------------------------------------

        await interaction.response.defer(
            ephemeral=True
        )

        try:

            # ----------------------------------
            # EXISTING VOICE CLIENT
            # ----------------------------------

            voice_client = interaction.guild.voice_client

            if voice_client is not None:

                # Already in requested channel

                if voice_client.channel is not None:

                    if voice_client.channel.id == channel.id:

                        await interaction.followup.send(
                            embed=error_embed(
                                "Already Connected",
                                f"I am already in {channel.mention}."
                            ),
                            ephemeral=True
                        )

                        return

                # Move to new channel

                await voice_client.move_to(
                    channel
                )

            else:

                # ----------------------------------
                # CONNECT
                # ----------------------------------

                voice_client = await channel.connect(
                    timeout=60.0,
                    reconnect=True
                )

            # ----------------------------------
            # SELF MUTE + SELF DEAF
            # ----------------------------------

            try:

                await voice_client.guild.change_voice_state(
                    channel=channel,
                    self_mute=True,
                    self_deaf=True
                )

            except Exception as error:

                print(
                    f"⚠️ Voice state update error: "
                    f"{type(error).__name__}: {error}"
                )

            # ----------------------------------
            # SUCCESS
            # ----------------------------------

            await interaction.followup.send(
                embed=success_embed(
                    "Joined Voice Channel",
                    f"Connected to {channel.mention}.\n"
                    "🔇 Self-Muted\n"
                    "🔕 Self-Deafened"
                ),
                ephemeral=True
            )

        # --------------------------------------
        # PERMISSION ERROR
        # --------------------------------------

        except discord.Forbidden as error:

            print(
                f"❌ Voice Forbidden: "
                f"{type(error).__name__}: {error}"
            )

            await interaction.followup.send(
                embed=error_embed(
                    "Permission Error",
                    f"I don't have permission to join {channel.mention}."
                ),
                ephemeral=True
            )

        # --------------------------------------
        # ALREADY CONNECTED / CLIENT ERROR
        # --------------------------------------

        except discord.ClientException as error:

            print(
                f"❌ Voice ClientException: "
                f"{type(error).__name__}: {error}"
            )

            await interaction.followup.send(
                embed=error_embed(
                    "Voice Error",
                    f"Discord voice client error:\n`{error}`"
                ),
                ephemeral=True
            )

        # --------------------------------------
        # TIMEOUT
        # --------------------------------------

        except TimeoutError as error:

            print(
                f"❌ Voice Timeout: "
                f"{type(error).__name__}: {error}"
            )

            await interaction.followup.send(
                embed=error_embed(
                    "Voice Timeout",
                    "Discord voice connection timed out."
                ),
                ephemeral=True
            )

        # --------------------------------------
        # OPUS ERROR
        # --------------------------------------

        except discord.opus.OpusNotLoaded as error:

            print(
                f"❌ Opus Error: "
                f"{type(error).__name__}: {error}"
            )

            await interaction.followup.send(
                embed=error_embed(
                    "Voice Dependency Error",
                    "Opus is not loaded on the server."
                ),
                ephemeral=True
            )

        # --------------------------------------
        # ALL OTHER ERRORS
        # --------------------------------------

        except Exception as error:

            print(
                "========================================"
            )

            print(
                "❌ UNKNOWN VOICE ERROR"
            )

            print(
                f"Type: {type(error).__name__}"
            )

            print(
                f"Error: {error}"
            )

            print(
                "========================================"
            )

            await interaction.followup.send(
                embed=error_embed(
                    "Voice Error",
                    f"`{type(error).__name__}: {error}`"
                ),
                ephemeral=True
            )

    # ==========================================
    # LEAVE VC
    # ==========================================

    @app_commands.command(
        name="left-vc",
        description="Leave the current voice channel."
    )
    async def left_vc(
        self,
        interaction: discord.Interaction
    ):

        # --------------------------------------
        # SERVER CHECK
        # --------------------------------------

        if interaction.guild is None:

            await interaction.response.send_message(
                embed=error_embed(
                    "Server Only",
                    "This command can only be used inside a server."
                ),
                ephemeral=True
            )

            return

        # --------------------------------------
        # ADMIN CHECK
        # --------------------------------------

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                embed=error_embed(
                    "No Permission",
                    "You need Administrator permission to use this command."
                ),
                ephemeral=True
            )

            return

        # --------------------------------------
        # GET VOICE CLIENT
        # --------------------------------------

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

        channel_name = (
            voice_client.channel.name
            if voice_client.channel
            else "Voice Channel"
        )

        # --------------------------------------
        # DISCONNECT
        # --------------------------------------

        try:

            await voice_client.disconnect(
                force=True
            )

        except Exception as error:

            print(
                f"❌ Voice Disconnect Error: "
                f"{type(error).__name__}: {error}"
            )

            await interaction.response.send_message(
                embed=error_embed(
                    "Voice Error",
                    f"`{type(error).__name__}: {error}`"
                ),
                ephemeral=True
            )

            return

        # --------------------------------------
        # SUCCESS
        # --------------------------------------

        await interaction.response.send_message(
            embed=success_embed(
                "Left Voice Channel",
                f"I left **{channel_name}**."
            ),
            ephemeral=True
        )


# ==========================================
# SETUP
# ==========================================

async def setup(bot):

    await bot.add_cog(
        Voice(bot)
    )
