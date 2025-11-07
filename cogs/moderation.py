from discord.ext import commands
import discord
import datetime
from . import log

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- /kick ---
    @commands.slash_command(name="kick", description="Kicke ein Mitglied vom Server")
    async def kick(self, ctx, member: discord.Member, reason: str = None):
        await ctx.defer()

        # Berechtigungen prüfen
        if not ctx.author.guild_permissions.kick_members:
            return await ctx.respond("❌ Du hast keine Berechtigung, Mitglieder zu kicken!", ephemeral=True)
        if member == ctx.author:
            return await ctx.respond("❌ Du kannst dich nicht selbst kicken!", ephemeral=True)
        if member == ctx.guild.owner:
            return await ctx.respond("❌ Du kannst den Serverowner nicht kicken!", ephemeral=True)

        # DM an das Ziel
        try:
            embed_dm = discord.Embed(
                title="🚪 Du wurdest gekickt!",
                description=f"Du wurdest aus **{ctx.guild.name}** entfernt.",
                color=discord.Color.orange()
            )
            embed_dm.add_field(name="Grund:", value=reason or "Kein Grund angegeben.", inline=False)
            embed_dm.add_field(name="Moderator:", value=ctx.author.display_name, inline=False)
            await member.send(embed=embed_dm)
        except Exception:
            pass

        # Kick ausführen
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="✅ Mitglied gekickt",
                description=f"{member.mention} wurde erfolgreich gekickt.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Grund:", value=reason or "Kein Grund angegeben.", inline=False)
            embed.add_field(name="Moderator:", value=ctx.author.display_name, inline=False)
            await ctx.respond(embed=embed)
        except discord.Forbidden:
            await ctx.respond("❌ Ich habe nicht genug Rechte, um dieses Mitglied zu kicken!", ephemeral=True)
        except discord.HTTPException:
            await ctx.respond("⚠️ Fehler beim Kicken – versuch es später nochmal.", ephemeral=True)

    # --- /ban ---
    @commands.slash_command(name="ban", description="Bannt ein Mitglied vom Server")
    async def ban(self, ctx, member: discord.Member, reason: str = None):
        await ctx.defer()

        if not ctx.author.guild_permissions.ban_members:
            return await ctx.respond("❌ Du hast keine Berechtigung, Mitglieder zu bannen!", ephemeral=True)
        if member == ctx.author:
            return await ctx.respond("❌ Du kannst dich nicht selbst bannen!", ephemeral=True)
        if member == ctx.guild.owner:
            return await ctx.respond("❌ Du kannst den Serverowner nicht bannen!", ephemeral=True)

        try:
            embed_dm = discord.Embed(
                title="🔨 Du wurdest gebannt!",
                description=f"Du wurdest aus **{ctx.guild.name}** gebannt.",
                color=discord.Color.red()
            )
            embed_dm.add_field(name="Grund:", value=reason or "Kein Grund angegeben.", inline=False)
            embed_dm.add_field(name="Moderator:", value=ctx.author.display_name, inline=False)
            await member.send(embed=embed_dm)
        except Exception:
            pass

        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="✅ Mitglied gebannt",
                description=f"{member.mention} wurde erfolgreich gebannt.",
                color=discord.Color.red()
            )
            embed.add_field(name="Grund:", value=reason or "Kein Grund angegeben.", inline=False)
            embed.add_field(name="Moderator:", value=ctx.author.display_name, inline=False)
            await ctx.respond(embed=embed)
        except discord.Forbidden:
            await ctx.respond("❌ Ich habe nicht genug Rechte, um dieses Mitglied zu bannen!", ephemeral=True)
        except discord.HTTPException:
            await ctx.respond("⚠️ Fehler beim Bannen – versuch es später nochmal.", ephemeral=True)

    # --- /unban ---
    @commands.slash_command(name="unban", description="Entbannt einen Nutzer anhand seines Namens#Tags")
    async def unban(self, ctx, user: str):
        await ctx.defer()

        if not ctx.author.guild_permissions.ban_members:
            return await ctx.respond("❌ Du darfst keine Nutzer entbannen!", ephemeral=True)

        banned_users = await ctx.guild.bans()
        name, _, discriminator = user.partition("#")
        for ban_entry in banned_users:
            user_obj = ban_entry.user
            if (user_obj.name, user_obj.discriminator) == (name, discriminator):
                await ctx.guild.unban(user_obj)
                embed = discord.Embed(
                    title="✅ Nutzer entbannt",
                    description=f"{user_obj} wurde erfolgreich entbannt.",
                    color=discord.Color.green()
                )
                embed.add_field(name="Moderator:", value=ctx.author.display_name, inline=False)
                return await ctx.respond(embed=embed)

        await ctx.respond("❌ Kein gebannter Nutzer mit diesem Namen gefunden.", ephemeral=True)

    # --- /mute ---
    @commands.slash_command(name="mute", description="Stummschalten eines Mitglieds (Timeout)")
    async def mute(self, ctx, member: discord.Member, minutes: int = 5, reason: str = None):
        await ctx.defer()

        if not ctx.author.guild_permissions.moderate_members:
            return await ctx.respond("❌ Du darfst keine Mitglieder stummschalten!", ephemeral=True)

        try:
            duration = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
            await member.timeout(duration, reason=reason)
            embed = discord.Embed(
                title="🔇 Mitglied gemutet",
                description=f"{member.mention} wurde für **{minutes} Minuten** stummgeschaltet.",
                color=discord.Color.blurple()
            )
            embed.add_field(name="Grund:", value=reason or "Kein Grund angegeben.", inline=False)
            embed.add_field(name="Moderator:", value=ctx.author.display_name, inline=False)
            await ctx.respond(embed=embed)
        except discord.Forbidden:
            await ctx.respond("❌ Ich habe nicht genug Rechte, um dieses Mitglied zu muten!", ephemeral=True)
        except discord.HTTPException:
            await ctx.respond("⚠️ Fehler beim Muten – versuch es später nochmal.", ephemeral=True)

    # --- /unmute ---
    @commands.slash_command(name="unmute", description="Hebt das Timeout eines Mitglieds auf")
    async def unmute(self, ctx, member: discord.Member):
        await ctx.defer()

        if not ctx.author.guild_permissions.moderate_members:
            return await ctx.respond("❌ Du darfst keine Mitglieder entmuten!", ephemeral=True)

        try:
            await member.timeout(None)
            embed = discord.Embed(
                title="🔈 Mitglied entmutet",
                description=f"{member.mention} kann wieder sprechen.",
                color=discord.Color.green()
            )
            embed.add_field(name="Moderator:", value=ctx.author.display_name, inline=False)
            await ctx.respond(embed=embed)
        except discord.Forbidden:
            await ctx.respond("❌ Ich habe nicht genug Rechte, um dieses Mitglied zu entmuten!", ephemeral=True)
        except discord.HTTPException:
            await ctx.respond("⚠️ Fehler beim Entmuten – versuch es später nochmal.", ephemeral=True)


def setup(bot):
    bot.add_cog(Moderation(bot))
