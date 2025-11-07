import os
from discord.ext import commands
from discord import Intents
try:
    import dotenv
    dotenv.load_dotenv("var.env")
finally:
    pass

intents = Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="$", intents=intents, max_messages=10000)

# COGS

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
                print([name.lower() for name in bot.cogs.keys()])
                if cog_name in [name.lower() for name in bot.cogs.keys()]:
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

bot.run(os.getenv("BOT_TOKEN"))