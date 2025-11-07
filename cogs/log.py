import discord
from discord.ext import commands
from datetime import datetime

logInfo = None
logWarning = None
logError = None
logSuccess = None

class Log(commands.Cog):
    def __init__(self, bot):
        global logInfo, logWarning, logError, logSuccess
        self.bot = bot
        self.log_channels = {}  # guild_id -> channel
        logError = self.logError
        logInfo = self.logInfo
        logWarning = self.logWarning
        logSuccess = self.logSuccess

    def cog_unload(self):
        global logInfo, logSuccess, logWarning, logError
        logInfo = logSuccess = logWarning = logError = None

    # ------------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------------
    def get_log_channel(self, guild: discord.Guild):
        if guild.id in self.log_channels:
            return self.log_channels[guild.id]
        for channel in guild.text_channels:
            if "logs" in channel.name.lower():
                self.log_channels[guild.id] = channel
                return channel
        return None
    
    async def logError(self, guild, title, description, **kwargs):
        fields = kwargs.get("fields", {})
        embed = self.make_embed(title, description, color=discord.Color.red(), **fields)
        await self.send_log(guild, embed)

    async def logInfo(self, guild, title, description, **kwargs):
        fields = kwargs.get("fields", {})
        embed = self.make_embed(title, description, **fields)
        await self.send_log(guild, embed)

    async def logWarning(self, guild, title, description, **kwargs):
        fields = kwargs.get("fields", {})
        embed = self.make_embed(title, description, color=discord.Color.orange(), **fields)
        await self.send_log(guild, embed)

    async def logSuccess(self, guild, title, description, **kwargs):
        fields = kwargs.get("fields", {})
        embed = self.make_embed(title, description, color=discord.Color.green(), **fields)
        await self.send_log(guild, embed)

    def make_embed(self, title, description, color=discord.Color.blurple(), **fields):
        embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.utcnow())
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=False)
        embed.set_footer(text="Log-System")
        return embed

    async def send_log(self, guild, embed):
        channel = self.get_log_channel(guild)
        if channel:
            await channel.send(embed=embed)

    # ------------------------------------------------------------
    # MEMBER JOIN / LEAVE
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        embed = self.make_embed(
            "👋 Mitglied beigetreten",
            f"{member.mention} ({member}) ist beigetreten.",
            discord.Color.green(),
            **{"Account erstellt": member.created_at.strftime("%d.%m.%Y %H:%M:%S")}
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.send_log(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        embed = self.make_embed(
            "🚪 Mitglied hat den Server verlassen",
            f"{member} ({member.id}) hat den Server verlassen.",
            discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.send_log(member.guild, embed)

    # ------------------------------------------------------------
    # KICK / BAN / UNBAN / MUTE / ROLE UPDATES
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        guild = after.guild
        changes = []

        # Rollenänderungen
        added = [r.mention for r in after.roles if r not in before.roles and r.name != "@everyone"]
        removed = [r.mention for r in before.roles if r not in after.roles and r.name != "@everyone"]

        if added:
            changes.append(f"➕ **Rolle(n) hinzugefügt:** {', '.join(added)}")
        if removed:
            changes.append(f"➖ **Rolle(n) entfernt:** {', '.join(removed)}")

        # Nickname Änderung
        if before.nick != after.nick:
            changes.append(f"🧩 **Nickname:** `{before.nick}` → `{after.nick}`")

        # Keine Änderungen → nichts loggen
        if not changes:
            return

        # Ersteller (Admin) aus Audit Log holen
        try:
            entry = await guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update).get(target=after)
            executor = entry.user.mention if entry else "Unbekannt"
        except:
            executor = "Unbekannt"

        embed = self.make_embed(
            "🧑‍💼 Mitglied geändert",
            f"{after.mention} ({after.id})",
            discord.Color.blurple(),
            **{
                "Änderungen": "\n".join(changes),
                "Ausgeführt von": executor
            }
        )
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        entry = await guild.audit_logs(limit=1, action=discord.AuditLogAction.ban).get(target=user)
        executor = entry.user.mention if entry else "Unbekannt"
        embed = self.make_embed(
            "🔨 Benutzer gebannt",
            f"{user} wurde gebannt.",
            discord.Color.red(),
            **{"Von": executor}
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        entry = await guild.audit_logs(limit=1, action=discord.AuditLogAction.unban).get(target=user)
        executor = entry.user.mention if entry else "Unbekannt"
        embed = self.make_embed(
            "🕊 Benutzer entbannt",
            f"{user} wurde entbannt.",
            discord.Color.green(),
            **{"Von": executor}
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_member_kick(self, guild, user):
        entry = await guild.audit_logs(limit=1, action=discord.AuditLogAction.kick).get(target=user)
        executor = entry.user.mention if entry else "Unbekannt"
        embed = self.make_embed(
            "👢 Benutzer gekickt",
            f"{user} wurde gekickt.",
            discord.Color.orange(),
            **{"Von": executor}
        )
        await self.send_log(guild, embed)

    # ------------------------------------------------------------
    # MESSAGE LOGS
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        embed = self.make_embed(
            "🗑 Nachricht gelöscht",
            f"**Autor:** {message.author.mention}\n**Kanal:** {message.channel.mention}",
            discord.Color.red(),
            **{"Inhalt": message.content or '*leer*'}
        )
        await self.send_log(message.guild, embed)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        for message in messages:
            await self.on_message_delete(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        embed = self.make_embed(
            "✏️ Nachricht bearbeitet",
            f"**Autor:** {before.author.mention}\n**Kanal:** {before.channel.mention}",
            discord.Color.orange(),
            **{
                "Vorher": before.content or "*leer*",
                "Nachher": after.content or "*leer*"
            }
        )
        await self.send_log(before.guild, embed)

    # ------------------------------------------------------------
    # VOICE LOGS
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild = member.guild
        if before.channel == after.channel:
            return

        if not before.channel and after.channel:
            desc = f"{member.mention} ist **{after.channel.name}** beigetreten."
            color = discord.Color.green()
        elif before.channel and not after.channel:
            desc = f"{member.mention} hat **{before.channel.name}** verlassen."
            color = discord.Color.red()
        else:
            desc = f"{member.mention} ist von **{before.channel.name}** → **{after.channel.name}** gewechselt."
            color = discord.Color.blurple()

        embed = self.make_embed("🎧 Voice-Aktion", desc, color)
        await self.send_log(guild, embed)

    # ------------------------------------------------------------
    # CHANNEL / ROLE UPDATES
    # ------------------------------------------------------------
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        guild = after.guild
        entry = await guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update).get(target=after)
        executor = entry.user.mention if entry else "Unbekannt"

        changes = []
        if before.name != after.name:
            changes.append(f"**Name:** `{before.name}` → `{after.name}`")

        if not changes:
            return

        embed = self.make_embed(
            "⚙️ Kanal geändert",
            f"{after.mention}",
            discord.Color.teal(),
            **{
                "Änderungen": "\n".join(changes),
                "Von": executor
            }
        )
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        guild = after.guild
        entry = await guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update).get(target=after)
        executor = entry.user.mention if entry else "Unbekannt"

        changes = []
        if before.name != after.name:
            changes.append(f"**Name:** `{before.name}` → `{after.name}`")
        if before.permissions != after.permissions:
            changes.append("**Berechtigungen geändert.**")

        embed = self.make_embed(
            "🧱 Rolle geändert",
            f"**{after.name}** ({after.id})",
            discord.Color.teal(),
            **{
                "Änderungen": "\n".join(changes),
                "Von": executor
            }
        )
        await self.send_log(guild, embed)

def setup(bot):
    bot.add_cog(Log(bot))