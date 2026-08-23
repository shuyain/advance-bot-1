import os
import discord
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = "AdvancedBot"

OWNER_ID = 1263489107116425226

EMBED_COLOR = discord.Color.blue()

FOOTER_TEXT = "AdvancedBot"

DATABASE_FILE = "data/database.json"

TOKEN = os.getenv("TOKEN")
