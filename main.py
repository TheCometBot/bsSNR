import os
import threading
from discord.ext import commands
from discord import Intents
from flask import Flask, redirect, url_for
try:
    import dotenv
    dotenv.load_dotenv("var.env")
finally:
    pass

# -------- Discord Setup --------
intents = Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="$", intents=intents, max_messages=10000)

# Load Cogs
for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        try:
            bot.load_extension(f"cogs.{filename[:-3]}")
            print("Loaded", filename)
        except Exception as e:
            print(f"Failed to load {filename}: {e}")

@bot.event
async def on_ready():
    print(f"Bot ready - logged in as {bot.user} (ID: {bot.user.id})")

@bot.slash_command(name="reload", description="Lädt alle Cogs neu (Admin)")
@commands.has_permissions(administrator=True)
async def reload(ctx):
    await ctx.defer(ephemeral=True)
    
    reloaded = []
    failed = []

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            cog_name = filename[:-3]
            try:
                if cog_name.lower() in [name.lower() for name in bot.cogs.keys()]:
                    bot.reload_extension(f"cogs.{cog_name}")
                else:
                    bot.load_extension(f"cogs.{cog_name}")
                reloaded.append(cog_name)
            except Exception as e:
                failed.append(f"{cog_name} ({e})")
    
    msg = f"✅ Neu geladen: {', '.join(reloaded)}"
    if failed:
        msg += f"\n❌ Fehler: {', '.join(failed)}"
    await ctx.respond(msg, ephemeral=True)

# -------- Flask Setup --------
app = Flask(__name__)

@app.route("/")
def index():
    return redirect(url_for("health"))

@app.route("/health")
def health():
    return "OK", 200

# -------- Helper to run bot in a thread --------
def run_bot():
    bot.run(os.getenv("BOT_TOKEN"))

# -------- Main --------

threading.Thread(target=run_bot, daemon=True).start()
# Starte Flask im Main Thread
app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
