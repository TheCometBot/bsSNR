import os
import threading
import discord
from discord.ext import commands
from discord import Intents
from flask import Flask, redirect, url_for, request
import requests
import xml.etree.ElementTree as ET
import asyncio

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

async def send_new_yt_video(title, author, link, thumbnail_url):
    channel = bot.get_channel(1436649248610582528)
    if channel:
        embed = discord.Embed(
            title=f"{author}: Neues Video!",
            url=link,
            description=f"{title}\n@everyone",
            color=discord.Color.red(),
        )
        embed.set_thumbnail(url=thumbnail_url)
        await channel.send(embed=embed)


# -------- Flask Setup --------
app = Flask(__name__)

@app.route("/")
def index():
    return redirect(url_for("health"))

@app.route("/health")
def health():
    return "OK", 200

@app.route("/tos")
def tos():
    with open("TERMS.html", 'r', encoding='utf-8') as f:
        return f.read()
    
@app.route("/privacy")
def privacy():
    with open("PRIVACY.html", 'r', encoding='utf-8') as f:
        return f.read()
    
@app.route("/websub/callback", methods=["GET", "POST"])
def websub_callback():
    if request.method == "GET":
        challenge = request.args.get("hub.challenge")
        if challenge:
            return challenge, 200
        return "Missing challenge", 400
    print("Youtube-Update")
    data = request.data.decode("utf-8")

    root = ET.fromstring(data)

    entry = root.find("{http://www.w3.org/2005/Atom}entry")
    if entry is not None:
        ns = {
            "yt": "http://www.youtube.com/xml/schemas/2015",
            "atom": "http://www.w3.org/2005/Atom"
        }

        video_id = entry.find("yt:videoId", ns).text
        channel_id = entry.find("yt:channelId", ns).text
        title = entry.find("atom:title", ns).text
        author = entry.find("atom:author/atom:name", ns).text
        link = entry.find("atom:link", ns).attrib.get("href")
        thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        asyncio.create_task(send_new_yt_video(title, author, link, thumbnail))


def subscribe():
    callback_url = "https://creeper-7rup.onrender.com/websub/callback/"
    print("Callback:", callback_url)
    hub_url = "https://pubsubhubbub.appspot.com/subscribe"
    channel_ids = ["UCxzx7sdLPG9XzxC-supGbiw", "UCg7aqczRrjRMTvyQD9FF0Yg"]
    topics = []
    for cid in channel_ids:
        topics.append(f"https://www.youtube.com/channel/{cid}")
    for topic in topics:
        data = {
            "hub.mode": "subscribe",
            "hub.topic": topic,
            "hub.callback": callback_url,
            "hub.verify": "async"
        }
        response = requests.post(hub_url, data=data)
        print("Subscription sended:", response.status_code, response.text)
    print("All Subscriptions done.")
    

# -------- Helper to run bot in a thread --------
def run_bot():
    subscribe()
    bot.run(os.getenv("BOT_TOKEN"))

# -------- Main --------

threading.Thread(target=run_bot, daemon=True).start()
# Starte Flask im Main Thread
app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
