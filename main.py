import asyncio

import discord
from discord.ext import commands

from config import TOKEN


# ==========================================
# BOT INTENTS
# ==========================================

intents = discord.Intents.default()

intents.guilds = True
intents.members = True
intents.invites = True
intents.voice_states = True


# ==========================================
# BOT
# ==========================================

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ==========================================
# LOAD COGS
# ==========================================

async def load_cogs():

    extensions = [
        "cogs.general",
        "cogs.voice",
        "cogs.giveaway",
        "cogs.invites",
        "cogs.moderation"
    ]

    for extension in extensions:

        try:

            await bot.load_extension(
                extension
            )

            print(
                f"✅ Loaded: {extension}"
            )

        except Exception as error:

            print(
                f"❌ Failed to load {extension}: "
                f"{type(error).__name__}: {error}"
            )

            raise


# ==========================================
# BOT READY
# ==========================================

@bot.event
async def on_ready():

    print(
        f"✅ Logged in as {bot.user}"
    )

    print(
        f"🆔 Bot ID: {bot.user.id}"
    )

    print(
        f"🌐 Servers: {len(bot.guilds)}"
    )

    # Sync slash commands

    try:

        synced = await bot.tree.sync()

        print(
            f"🔄 Synced {len(synced)} slash commands."
        )

    except discord.HTTPException as error:

        print(
            f"❌ Slash command sync failed: {error}"
        )

    print(
        "🚀 Bot is ready!"
    )


# ==========================================
# MAIN
# ==========================================

async def main():

    if not TOKEN:

        raise RuntimeError(
            "TOKEN environment variable is missing."
        )

    await load_cogs()

    try:

        await bot.start(
            TOKEN
        )

    finally:

        if not bot.is_closed():

            await bot.close()


# ==========================================
# START
# ==========================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print(
            "🛑 Bot stopped."
        )
