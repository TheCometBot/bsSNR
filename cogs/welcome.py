import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import aiohttp
import random
from datetime import datetime
from .log import logSuccess, logError, logWarning, logInfo


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1438880119841099821
        self.font_path = "./LilitaOne.ttf"
        self.backgrounds = [
            "./welcomes/Crow.png",
            "./welcomes/Mortis.png",
            "./welcomes/Skeleton.png",
            "./welcomes/Steve.png"
        ]
        
        self.avatar_slot = (130, 92, 580, 550)

        self.text_slots = {
            "welcome": {"slot": {"x": 450, "y": 40, "w": 540, "h": 90}, "align": "center"},
            "username": {"slot": {"x": 65, "y": 600, "w": 730, "h": 70}, "align": "center"},
            "member_count": {"slot": {"x": 125, "y": 750, "w": 600, "h": 40}, "align": "left"}
        }

    def draw_text_in_slot(self, draw, text, slot, align="center", max_font_size=64, min_font_size=24):
        # Korrigierte Zuweisung von x, y, w, h
        x, y, w, h = slot["x"], slot["y"], slot["w"], slot["h"]
        font_size = max_font_size
        font = ImageFont.truetype(self.font_path, font_size)

        while True:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            if text_w <= w and text_h <= h:
                break
            font_size -= 2
            if font_size < min_font_size:
                while text and (draw.textbbox((0, 0), text + "…", font=font)[2] > w):
                    text = text[:-1]
                text += "…"
                break
            font = ImageFont.truetype(self.font_path, font_size)

        bbox = draw.textbbox((0, 0), text, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

        if align == "center":
            pos = (x + (w - text_w) // 2, y + (h - text_h) // 2)
        elif align == "right":
            pos = (x + w - text_w, y + (h - text_h) // 2)
        else:
            pos = (x, y + (h - text_h) // 2)

        draw.text(
            pos,
            text,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=3,
            stroke_fill=(0, 0, 0, 255)
        )

    async def load_avatar(self, member):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(member.display_avatar.url)) as resp:
                    if resp.status == 200:
                        avatar_bytes = await resp.read()
                        avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                        return avatar_img
        except Exception as e:
            await  logError(
                guild=member.guild,
                title="Avatar konnte nicht geladen werden",
                description=str(e),
                fields={
                    "Member": f"{member.name}#{member.discriminator}",
                    "Timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                }
            )
        return None

    async def generate_welcome_image(self, member, member_count: int):
        background_path = random.choice(self.backgrounds)
        background = Image.open(background_path).convert("RGBA")

        avatar = await self.load_avatar(member)
        if avatar:
            x, y, w, h = self.avatar_slot
            avatar = avatar.resize((w, h))

            # 1️⃣ Schatten erstellen (größer als Avatar)
            shadow = Image.new("RGBA", (w+20, h+20), (0,0,0,0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.ellipse((10, 10, w+10, h+10), fill=(0,0,0,200))  # halbtransparent schwarz

            # 2️⃣ Schatten weichzeichnen für Glow
            shadow = shadow.filter(ImageFilter.GaussianBlur(8))  # softer Glow

            # 3️⃣ Schatten auf Hintergrund einfügen
            background.paste(shadow, (x-10, y-10), shadow)

            # 4️⃣ Avatar rund ausschneiden
            mask = Image.new("L", (w, h), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, w, h), fill=255)

            # 5️⃣ Avatar auf Hintergrund mit Maske einfügen
            background.paste(avatar, (x, y), mask)



        draw = ImageDraw.Draw(background)
        self.draw_text_in_slot(draw, "Willkommen!", **self.text_slots["welcome"], max_font_size=150, min_font_size=30)
        self.draw_text_in_slot(draw, f"@{member.name}", **self.text_slots["username"], max_font_size=60, min_font_size=24)
        self.draw_text_in_slot(draw, f"{member_count}. Mitglied!", **self.text_slots["member_count"], max_font_size=50, min_font_size=20)

        return background, background_path

    @commands.command(name="welcome")
    async def welcome_command(self, ctx, member: discord.Member, member_count: int):
        channel = ctx.guild.get_channel(self.channel_id)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        if not channel:
            await ctx.send("❌ Der Willkommenschannel wurde nicht gefunden.")
            await logWarning(
                guild=ctx.guild,
                title="Willkommens-Channel nicht gefunden",
                description=f"Channel-ID {self.channel_id} existiert auf Server {ctx.guild.name} nicht.",
                fields={"Guild ID": ctx.guild.id, "Timestamp": timestamp}
            )
            return

        try:
            background, background_path = await self.generate_welcome_image(member, member_count)

            embed = discord.Embed(
                title="Willkommen!",
                description=f"{member.mention} ist dem Server beigetreten.",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="User ID", value=str(member.id), inline=True)
            embed.add_field(name="Beitritt", value=f"<t:{int(datetime.utcnow().timestamp())}:R>", inline=True)
            embed.add_field(name="Erstellt von", value=ctx.author.mention, inline=True)

            with io.BytesIO() as image_binary:
                background.save(image_binary, 'PNG')
                image_binary.seek(0)
                await channel.send(embed=embed, file=discord.File(fp=image_binary, filename='welcome.png'))

            await ctx.send(f"✅ Willkommensnachricht für {member.mention} wurde im Channel {channel.mention} gesendet!")

            await  logSuccess(
                guild=ctx.guild,
                title="Manuelles Willkommensbild gesendet",
                description=f"Von {ctx.author.name}#{ctx.author.discriminator} für {member.name}#{member.discriminator}",
                fields={
                    "Guild": ctx.guild.name,
                    "Member": f"{member.name}#{member.discriminator}",
                    "Member Count": member_count,
                    "Timestamp": timestamp
                },
                image=background_path
            )

        except Exception as e:
            await ctx.send("❌ Fehler beim Erstellen des Willkommensbilds.")
            await logError(
                guild=ctx.guild,
                title="Fehler beim manuellen Willkommensbild",
                description=str(e),
                fields={
                    "Member": f"{member.name}#{member.discriminator}",
                    "Guild": ctx.guild.name,
                    "Timestamp": timestamp
                }
            )

    @commands.Cog.listener()
    async def on_member_join(self, member:discord.Member):
        guild = member.guild
        channel = guild.get_channel(self.channel_id)
        if not channel:
            return
        
        member_count = guild.member_count
        background, background_path = await self.generate_welcome_image(member, member_count)

        embed = discord.Embed(
            title="Willkommen!",
            description=f"{member.mention} ist dem Server beigetreten!",
            color=discord.Color.green()
        )

        with io.BytesIO() as image_binary:
            background.save(image_binary, "PNG")
            image_binary.seek(0)
            await channel.send(embed=embed, file=discord.File(fp=image_binary, filename="welcome.png"))


def setup(bot):
    bot.add_cog(Welcome(bot))
