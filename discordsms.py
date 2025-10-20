import os
import asyncio
import requests
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from urllib.parse import quote_plus

# ----------------- CONFIGURATION -----------------
DISCORD_TOKEN = "MTQyOTgzNjgwNDk2NTc5Nzk4OQ.GZGGdm.cCkiYZP6vffKt1qGF74YIEsiOfONolI_KRDFew"
BASE_URL_TEMPLATE = "https://sms-spoofer.itxkaal.workers.dev/?mo={number}&text={message}"
LOG_FILE = "sent.log"
TIMEOUT = 30
DEFAULT_DELAY = 1.0
# -------------------------------------------------

_last_send_at = {}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def build_url(number: str, message: str) -> str:
    return BASE_URL_TEMPLATE.replace("{number}", quote_plus(number.strip(), safe="")) \
                            .replace("{message}", quote_plus(message, safe=""))


def log_entry(number: str, message: str, status_code: int, resp_text: str):
    now = datetime.utcnow().isoformat() + "Z"
    short_resp = (resp_text.replace("\n", " "))[:500]
    line = f"{now}\t{number}\t{status_code}\t{short_resp}\t{message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


def send_once_sync(number: str, message: str):
    url = build_url(number, message)
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        text = (resp.text or "").strip()
        log_entry(number, message, resp.status_code, text)
        success = 200 <= resp.status_code < 300
        return success, resp.status_code, text
    except requests.RequestException as e:
        log_entry(number, message, 0, f"RequestException: {e}")
        return False, 0, str(e)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")


@bot.tree.command(name="start", description="Show bot info")
async def start_command(interaction: discord.Interaction):
    banner = (
        "```text\n"
        "____  ___       _________   _____    _________\n"
        "\\   \\/  /      /   _____/  /     \\  /   _____/\n"
        " \\     /       \\_____  \\  /  \\ /  \\ \\_____  \\\n"
        " /     \\       /        \\/    Y    \\/        \\\n"
        "/___/\\  \\_____/_______  /\\____|__  /_______  /\n"
        "      \\_/_____/       \\/         \\/        \\/\n"
        "```\\n"
        "**Powered by Hackerhacked**\\n\\nUse `/send` to send an SMS."
    )
    await interaction.response.send_message(banner)


@bot.tree.command(name="help", description="Show usage help")
async def help_command(interaction: discord.Interaction):
    msg = (
        "**Usage:**\n"
        "/send number message — send SMS\n"
        "/start — show bot info\n"
        "/help — show this help\n\n"
        "Example:\n"
        "`/send number:+88017XXXXXXX message:Hello there!`"
    )
    await interaction.response.send_message(msg)


@bot.tree.command(name="send", description="Send an SMS to a number")
@app_commands.describe(number="Phone number (e.g. +88017XXXXXXX)", message="Message text")
async def send_command(interaction: discord.Interaction, number: str, message: str):
    user_id = interaction.user.id
    now_ts = asyncio.get_event_loop().time()
    last = _last_send_at.get(user_id, 0)
    elapsed = now_ts - last
    if elapsed < DEFAULT_DELAY:
        wait = DEFAULT_DELAY - elapsed
        await interaction.response.send_message(
            f"You're sending too fast. Please wait {wait:.1f}s.", ephemeral=True
        )
        return

    await interaction.response.send_message(f"📤 Sending to {number}...", ephemeral=True)
    loop = asyncio.get_event_loop()
    success, status_code, resp_text = await loop.run_in_executor(None, send_once_sync, number, message)
    _last_send_at[user_id] = asyncio.get_event_loop().time()

    if success:
        msg = f"✅ Likely successful (HTTP {status_code}).\nResponse: {resp_text[:1000]}"
    else:
        msg = f"❌ Failed (HTTP {status_code}). Error: {resp_text}"

    await interaction.followup.send(msg, ephemeral=True)


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
