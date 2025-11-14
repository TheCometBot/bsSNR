import discord
from discord.ext import commands
from discord.utils import get

vc_extra_properties = {}

# ------------------------------
# PERSISTENT VIEWS
# ------------------------------
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ticket öffnen", style=discord.ButtonStyle.primary, custom_id="create_ticket")
    async def create_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        guild = interaction.guild
        cog = interaction.client.get_cog("Default")
        existing = get(guild.text_channels, name=f"ticket-{interaction.user.name}".lower())
        if existing:
            return await interaction.response.send_message("Du hast bereits ein offenes Ticket!", ephemeral=True)

        category = guild.get_channel(cog.support_category_id)
        support_role = get(guild.roles, id=cog.support_role_id)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        await channel.send(
            content=f"{interaction.user.mention}",
            embed=discord.Embed(
                title="🎫 Dein Ticket",
                description="Beschreibe hier dein Problem, ein Supporter wird sich melden.",
                color=discord.Color.green()
            ),
            view=CloseTicketView(channel)
        )
        await channel.send(f"{support_role.mention if support_role else ''}")
        await channel.send("Du kannst das Ticket auch mit dem Befehl ``$close`` schließen!")

        await interaction.response.send_message(f"Dein Ticket wurde erstellt: {channel.mention}", ephemeral=True)

# ------------------------------
# Close Ticket View
# ------------------------------
class CloseTicketView(discord.ui.View):
    def __init__(self, channel):
        super().__init__(timeout=None)
        self.channel = channel

    @discord.ui.button(label="🔒 Ticket schließen", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.channel != self.channel:
            return await interaction.response.send_message("Dieser Button gehört nicht zu diesem Ticket.", ephemeral=True)
        await interaction.response.send_message("Ticket wird geschlossen...", ephemeral=True)
        await self.channel.delete()

# ------------------------------
# Password Modal
# ------------------------------
class PasswordModal(discord.ui.Modal):
    def __init__(self, vc, user):
        super().__init__(title="Passwort eingeben")
        self.vc = vc
        self.user = user
        self.add_item(discord.ui.InputText(label="Passwort", placeholder="Hier eingeben", required=True))

    async def callback(self, interaction: discord.Interaction):
        global vc_extra_properties
        pw = self.children[0].value
        real_pw = vc_extra_properties.get(str(self.vc.id), {}).get("password")
        if pw == real_pw:
            allowed_users = vc_extra_properties.get(str(self.vc.id), {}).get("allowed_users", [])
            allowed_users.append(interaction.user.id)
            vc_extra_properties[str(self.vc.id)]["allowed_users"] = allowed_users
            await interaction.response.send_message("Richtiges Passwort! Du kannst nun dem VC beitreten!", ephemeral=True)
        else:
            await interaction.response.send_message("Falsches Passwort!", ephemeral=True)

class PasswordSetModal(discord.ui.Modal):
    def __init__(self, vc):
        super().__init__(title="Passwort setzen")
        self.vc = vc
        self.add_item(discord.ui.InputText(
            label="Passwort",
            placeholder="Hier eingeben",
            required=False,
            max_length=50
        ))

    async def callback(self, interaction: discord.Interaction):
        global vc_extra_properties
        vc_id = str(self.vc.id)
        pw = self.children[0].value

        # Stelle sicher, dass das VC-Objekt im Dict existiert
        if vc_id not in vc_extra_properties:
            vc_extra_properties[vc_id] = {}

        vc_extra_properties[vc_id]["password"] = pw
        vc_extra_properties[vc_id]["allowed_users"] = [m.id for m in self.vc.members]

        await interaction.response.send_message(
            f"🔑 Passwort {'gesetzt auf **'+pw+'**' if pw else 'deaktiviert'}!", ephemeral=True
        )

        # --- Embed nur bearbeiten, wenn es existiert ---
        msg = vc_extra_properties[vc_id].get("embed_msg")
        if msg:
            try:
                embed = msg.embeds[0]
                # Falls das Embed zu wenig Felder hat (Sichtbarkeit, Passwort)
                if len(embed.fields) < 2:
                    embed.add_field(name="Passwort", value=pw if pw else "Deaktiviert")
                else:
                    embed.set_field_at(1, name="Passwort", value=pw if pw else "Deaktiviert")
                await msg.edit(embed=embed)
            except Exception as e:
                print(f"[WARN] Embed konnte nicht aktualisiert werden: {e}")


class VCJoinPasswordView(discord.ui.View):
    def __init__(self, modal):
        super().__init__(timeout=None)
        self.modal = modal

    @discord.ui.button(label="Passwort eingeben", style=discord.ButtonStyle.success, custom_id="vc:join_password")
    async def join(self, button, interaction):
        await interaction.response.send_modal(self.modal)

# ------------------------------
# Temp VC Buttons View
# ------------------------------
class TempVCView(discord.ui.View):
    def __init__(self, vc):
        super().__init__(timeout=None)
        self.vc = vc

    @discord.ui.button(label="🔒 Privat", style=discord.ButtonStyle.danger, custom_id="vc_private")
    async def private(self, button: discord.ui.Button, interaction: discord.Interaction):
        overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(connect=False)}
        for member in self.vc.members:
            overwrites[member] = discord.PermissionOverwrite(connect=True)
        await self.vc.edit(overwrites=overwrites)
        await interaction.response.send_message("Der VC ist jetzt privat!", ephemeral=True)
        global vc_extra_properties
        print(vc_extra_properties[str(self.vc.id)])
        msg = vc_extra_properties[str(self.vc.id)]["embed_msg"]
        embed = msg.embeds[0]
        embed.set_field_at(0, name="Sichtbarkeit", value="Privat")
        await msg.edit(embed=embed)

    @discord.ui.button(label="🌐 Öffentlich", style=discord.ButtonStyle.success, custom_id="vc_public")
    async def public(self, button: discord.ui.Button, interaction: discord.Interaction):
        overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(connect=True)}
        await self.vc.edit(overwrites=overwrites)
        await interaction.response.send_message("Der VC ist jetzt öffentlich!", ephemeral=True)
        global vc_extra_properties
        msg = vc_extra_properties[str(self.vc.id)]["embed_msg"]
        embed = msg.embeds[0]
        embed.set_field_at(0, name="Sichtbarkeit", value="Öffentlich")
        await msg.edit(embed=embed)

    @discord.ui.button(label="🔑 Passwort", style=discord.ButtonStyle.primary, custom_id="vc_password")
    async def password(self, button, interaction: discord.Interaction):
        await interaction.response.send_modal(
            PasswordSetModal(self.vc)
        )

# ------------------------------
# MAIN COG
# ------------------------------
class Default(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.temp_voice_category_id = 1438880120700932142
        self.rules_role_name = "Regel Akzeptiert"
        self.support_category_id = 1438880120700932144
        self.support_role_id = 1438880119493103687

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketView())
        print("✅ Persistent Views registriert.")

    # Ticket Nachricht
    @commands.slash_command(name="ticket_message", description="Sendet die Ticket-Eröffnungs Nachricht")
    @commands.has_permissions(administrator=True)
    async def ticket_message(self, ctx):
        await ctx.defer()
        embed = discord.Embed(
            title="🎫 Support Ticket",
            description="Klicke auf den Button, um ein Ticket zu öffnen!",
            color=discord.Color.blue()
        )
        await ctx.channel.send(embed=embed, view=TicketView())
        await ctx.respond("Ticketsystem erstellt!", ephemeral=True)

    # Close Ticket mit Command
    @commands.command(name="close")
    async def close_ticket_command(self, ctx):
        if not ctx.channel.name.startswith("ticket-"):
            return await ctx.send("Dieser Befehl kann nur in einem Ticket genutzt werden.")
        await ctx.send("Ticket wird geschlossen...")
        await ctx.channel.delete()

    # 3️⃣ Temporary Voice Channel
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        global vc_extra_properties
        guild = member.guild
        category = guild.get_channel(self.temp_voice_category_id)

        # User erstellt Temp VC
        if after.channel and "CREATE VC" in after.channel.name:
            existing = [c for c in category.voice_channels if c.name.startswith(f"{member.name}'s VC")]
            if existing:
                await member.move_to(existing[0])
                return
            vc = await category.create_voice_channel(
                name=f"{member.name}'s VC",
                user_limit=5
            )
            await member.move_to(vc)

            textchannel = vc.guild.get_thread(vc.id)
            if not textchannel: textchannel = vc.guild.get_channel(vc.id)
            if textchannel:
                embed = discord.Embed(
                    title=f"{vc.name} Einstellungen",
                    description="Klicke auf die Buttons, um den VC einzustellen.",
                    color=discord.Color.blurple()
                )
                await textchannel.send(embed=embed, view=TempVCView(vc))
                embed = discord.Embed(
                    title="VC Übersicht",
                    description="Alle Einstellungen:"
                )
                embed.add_field(name="Sichtbarkeit", value="Öffentlich")
                embed.add_field(name="Passwort", value="Deaktiviert")
                vc_extra_properties[str(vc.id)] = {}
                vc_extra_properties[str(vc.id)]["embed_msg"] = await textchannel.send(embed=embed)
                print("...")
                

        # Password check beim Join
        if after.channel and "'s VC" in after.channel.name:
            vc = after.channel
            props = vc_extra_properties.get(str(vc.id), {})
            if props.get("password", "") != "":
                if member.id in vc_extra_properties.get(str(vc.id), {}).get("allowed_users", []):
                    return
                await member.move_to(None)
                modal = PasswordModal(vc, member)
                embed = discord.Embed(
                    title="Passwortgeschützer Srachkanal",
                    description=f"Klicke auf den Button, um dem VC zu joinen!",
                    color=discord.Color.green()
                )
                textchannel = vc.guild.get_thread(vc.id)
                if not textchannel: textchannel = vc.guild.get_channel(vc.id)
                if textchannel:
                    await textchannel.send(embed=discord.Embed(
                        title="Passwortgeschützter Sprachkanal",
                        description=f"{member.mention} hat versucht, dem Sprachkanal beizutreten.\nIch habe ihm eine Passwort-Request gesendet."
                    ))
                try:
                    await member.send(embed=embed, view=VCJoinPasswordView(modal))
                except discord.Forbidden:
                    if textchannel:
                        await textchannel.send(embed=discord.Embed(
                            title="Fehler",
                            description=f"Die Passwort-Request konnte nicht gesemdet werden, da {member.mention} dies in den Einstellungen deaktiviert hat.\nUm {member.mention} trotzdem den Beitritt zu erlauben, deaktiviert die Passwort-Sicherung.",
                            color=discord.Color.red()
                        ))

        # Cleanup leere Temp VCs
        if before.channel and before.channel.category_id == self.temp_voice_category_id:
            if before.channel.members == [] and "s VC" in before.channel.name:
                del vc_extra_properties[str(before.channel.id)]
                await before.channel.delete()


def setup(bot):
    bot.add_cog(Default(bot))

