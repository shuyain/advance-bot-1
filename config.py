import os
import discord
from dotenv import load_dotenv

# Load .env
load_dotenv()

# ==============================
# BOT SETTINGS
# ==============================

BOT_NAME = "AdvancedBot"

# Discord Bot Owner ID
OWNER_ID = 1263489107116425226

# ==============================
# EMBED SETTINGS
# ==============================

EMBED_COLOR = discord.Color.blue()

FOOTER_TEXT = "AdvancedBot"

# ==============================
# DATABASE SETTINGS
# ==============================

DATABASE_FILE = "data/database.json"

# ==============================
# ENVIRONMENT
# ==============================

TOKEN = os.getenv("TOKEN")