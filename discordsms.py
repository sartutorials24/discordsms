# --- Compatibility patch for Python 3.12+ ---
# Discord.py sometimes imports 'audioop', which was removed from Python 3.12.
# Since this bot does NOT use voice features, we safely stub it.
import sys
sys.modules['audioop'] = None

import os
import requests
from urllib.parse import quote_plus
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

BASE_URL_TEMPLATE = "https://sms-spoofer.itxkaal.workers.dev/?mo={number}&text={message}"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

banner = (
    "```\n"
    "____  ___       _________   _____    _________\n"
    "\\   \\/  /      /   _____/  /     \\  /   _____/\n"
    " \\     /       \\_____  \\  /  \\ /  \\ \\_____  \\ \n"
    " /     \\       /        \\/    Y    \\/        \\\n"
    "/___/\\  \\_____/_______  /\\____|__  /_______  /\n"
    "      \\_/_____/       \\/         \\/        \\/\n\n"
    "POWERED BY Hackerhacked\n"
    "```"
)

def build_url(number: str, message: str) -> str:
    enc_num = quote_plus(number.strip(), safe="")
    enc_msg = quote_plus(message, safe="")
    return BASE_URL_TEMPLATE.replace("{number}", enc_num).replace("{message}", enc_msg)

def send_sms(number: str, message: str):
    url = build_url(number, message)
    try:
        resp = requests.get(url, timeout=30)
        success = 200 <= resp.status_code < 300
        return success, resp.status_code, resp.text.strip()
    except requests.RequestException as e:
        return False, 0, f"Error: {e}"

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"⚠️ Sync failed: {e}")

@bot.tree.command(name="start", description="Show information about the SMS bot")
async def start(interaction: discord.Interaction):
    await interaction.response.send_message(
        banner + "\n📱 **SMS Sender Bot**\nUse `/send` to send messages!", ephemeral=True
    )

@bot.tree.command(name="send", description="Send an SMS via API")
@app_commands.describe(
    number="Phone number (e.g. +88017XXXXXXX)",
    message="Message text to send"
)
async def send(interaction: discord.Interaction, number: str, message: str):
    await interaction.response.defer(thinking=True)
    success, code, text = send_sms(number, message)
    if success:
        await interaction.followup.send(f"✅ Sent! (HTTP {code})\n```\n{text[:500]}\n```")
    else:
        await interaction.followup.send(f"❌ Failed (HTTP {code})\n```\n{text[:500]}\n```")

bot.run(BOT_TOKEN)
