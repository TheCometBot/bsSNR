import discord
from discord.ext import commands
import json

class TournamentOptionView(discord.ui.View):
    TEAMSIZE = discord.ui.Select(
        placeholder="Wähle eine Option...",
        options=[
            discord.SelectOption(label=str(i), description=f"{i} Person(en) pro Team", value=str(i)) for i in range(1, 6)
        ],
        custom_id="t_op:team_size"
    )

    FORMAT = discord.ui.Select(
        placeholder="Wähle eine Option...",
        options=[
            discord.SelectOption(label="K.O.", description="Wer verliert ist raus!", value="KO"),
            discord.SelectOption(label="Double Elimination", description="Jeder hat zwei Leben!", value="DE"),
            discord.SelectOption(label="Round Robin", description="Jeder gegen jeden", value="RR"),
            discord.SelectOption(label="Group + K.O.", description="Erst Gruppenphase, dann K.O.!", value="GKO"),
        ],
        custom_id="t_op:format"
    )

    ROUND_FORMAT = discord.ui.Select(
        placeholder="Wähle eine Option...",
        options=[
            discord.SelectOption(label="One-Match", description="Eine Begegnung pro Runde", value="1"),
            discord.SelectOption(label="Best-of-3", description="Wer zuerst 2 Matches gewinnt", value="3"),
            discord.SelectOption(label="Best-of-5", description="Wer zuerst 3 Matches gewinnt", value="5"),
            discord.SelectOption(label="Best-of-7", description="Wer zuerst 4 Matches gewinnt", value="7"),
        ],
        custom_id="t_op:round_format"
    )

    OPTIONS = [
        TEAMSIZE,
        FORMAT,
        ROUND_FORMAT
    ]

    def __init__(self, option, tournament, guild: discord.Guild):
        super().__init__(timeout=None)  # persistent
        option.callback = self.o_callback
        self.add_item(option)
        self.tournament = tournament
        self.guild = guild

    async def get_data(self):
        channel = self.guild.get_channel(self.tournament["data_channel"])
        data_msg = await channel.fetch_message(self.tournament["data_msg"])
        data = json.loads(data_msg.content)
        return data, data_msg

    async def update_data(self, data_msg, data: dict):
        await data_msg.edit(content=json.dumps(data, indent=2))

    async def o_callback(self, interaction: discord.Interaction):
        data, data_msg = await self.get_data()
        updated_field = None

        cid = interaction.data["custom_id"]
        value = interaction.data['values'][0]

        if cid == "t_op:team_size":
            data["team_size"] = int(value)
            updated_field = "Teamgröße"
        elif cid == "t_op:format":
            data["format"] = value
            updated_field = "Turnierformat"
        elif cid == "t_op:round_format":
            data["round_format"] = value
            updated_field = "Rundenformat"

        await self.update_data(data_msg, data)

        embed = discord.Embed(
            title="Gespeichert ✅",
            description=f"{updated_field} wurde erfolgreich gespeichert.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class TournamentModal(discord.ui.Modal):
    def __init__(self, tournament):
        super().__init__(title="Neues Turnier")
        self.tournament = tournament

        self.add_item(discord.ui.InputText(
            label="Turniername",
            placeholder="Hier eingeben",
            required=True,
            max_length=50
        ))

        self.add_item(discord.ui.InputText(
            label="Spiel",
            required=True,
            max_length=20
        ))

    async def create_data_channel(self, guild: discord.Guild, category: discord.CategoryChannel):
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }
        data_channel = await category.create_text_channel("tournament-data", overwrites=overwrites)
        data_msg = await data_channel.send(json.dumps(self.tournament, indent=2))
        return data_channel, data_msg

    async def create_tournament(self, guild: discord.Guild, msg: discord.Message):
        # Role & Kategorie
        role = await guild.create_role(name=self.tournament["name"], color=discord.Color.blurple(), reason="Turnier")
        category = await guild.create_category(self.tournament["name"])

        # Kanäle
        register_channel = await category.create_text_channel("anmelden")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            role: discord.PermissionOverwrite(view_channel=True)
        }
        lobby_channel = await category.create_text_channel("lobby", overwrites=overwrites)

        # Admin-Kanal
        for ro in [r for r in guild.roles if r.permissions.administrator]:
            overwrites[ro] = discord.PermissionOverwrite(view_channel=True)
        overwrites.pop(role)
        admin_channel = await category.create_text_channel("admin", overwrites=overwrites)

        # Data-Channel unter Kategorie
        data_channel, data_msg = await self.create_data_channel(guild, category)

        # IDs & Defaults speichern
        t = self.tournament
        t.update({
            "role": role.id,
            "category": category.id,
            "register_channel": register_channel.id,
            "lobby_channel": lobby_channel.id,
            "admin_channel": admin_channel.id,
            "data_channel": data_channel.id,
            "data_msg": data_msg.id,
            "team_size": "1",
            "format": "1",
            "round_format": "1"
        })
        self.tournament = t

        # Embed aktualisieren
        embed = msg.embeds[0]
        embed.set_field_at(0, name="Kanäle", value="Fertig")
        await msg.edit(embed=embed)

        # Options-Views persistent
        options = [
            ("Team-Größe", TournamentOptionView.TEAMSIZE),
            ("Turnier-Format", TournamentOptionView.FORMAT),
            ("Runden-Format", TournamentOptionView.ROUND_FORMAT)
        ]
        for title, opt in options:
            embed = discord.Embed(title=title, description=f"Stelle hier {title} ein!")
            view = TournamentOptionView(opt, self.tournament, guild)
            await admin_channel.send(embed=embed, view=view)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        name = self.children[0].value
        game = self.children[1].value
        self.tournament["name"] = name
        self.tournament["game"] = game

        embed = discord.Embed(title="Turnier erstellen", description="Erstelle Kanäle...")
        embed.add_field(name="Kanäle", value="Ausstehend")
        embed.add_field(name="Anpassungs-Optionen", value="Ausstehend")
        embed.add_field(name="Fertigstellung", value="Ausstehend")
        msg = await interaction.followup.send(embed=embed, ephemeral=True)
        await self.create_tournament(guild=interaction.guild, msg=msg)


class Tournament(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #@commands.Cog.listener()
    #async def on_ready(self):
        #for option in TournamentOptionView.OPTIONS:
            #self.bot.add_view(TournamentOptionView(option, None, None))
        #print("✅ Persistent Views registriert.")

    #@commands.slash_command(name="tournament")
    #async def tournament(self, ctx: discord.ApplicationContext):
        #tournament = {}
        #await ctx.interaction.response.send_modal(TournamentModal(tournament=tournament))


def setup(bot):
    bot.add_cog(Tournament(bot))
