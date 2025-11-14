import discord
from discord.ext import commands

class ReportReasonModal(discord.ui.Modal):
    def __init__(self, rcallback):
        super().__init__(title="Meldegrund")
        self.rcallback = rcallback
        self.add_item(discord.ui.InputText(
            label="Grund",
            placeholder="Dies kann helfen, dass das Team deine Meldung besser versteht.",
            required=False
        ))

    async def callback(self, interaction: discord.Interaction):
        reason = self.children[0].value
        await self.rcallback(interaction, reason)


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mod_channel = 1438880120881283247

    # Nachricht melden
    @discord.message_command(name="Nachricht melden")
    async def report_message(self, ctx: discord.ApplicationContext, message: discord.Message):
        async def rcallback(interaction: discord.Interaction, reason):
            embed = discord.Embed(
                title="Gemeldete Nachricht",
                description=f"**Inhalt**: {message.content[:1024]}",
                color=discord.Color.orange()
            )
            embed.add_field(name="Gesendet von", value=f"{message.author.mention} ({message.author.id})", inline=False)
            embed.add_field(name="Gemeldet von", value=f"{interaction.user.mention} ({interaction.user.id})", inline=False)
            embed.add_field(name="Grund", value=reason or "Kein Grund angegeben", inline=False)
            embed.add_field(name="Channel", value=message.channel.mention, inline=False)
            embed.add_field(name="Link", value=f"[Zur Nachricht]({message.jump_url})", inline=False)

            channel = interaction.guild.get_channel(self.mod_channel)
            if channel:
                await channel.send(embed=embed)
            await interaction.response.send_message("Die Nachricht wurde gemeldet!", ephemeral=True)

        await ctx.interaction.response.send_modal(ReportReasonModal(rcallback))

    # User melden
    @discord.user_command(name="User melden")
    async def report_user(self, ctx: discord.ApplicationContext, user: discord.User):
        async def rcallback(interaction: discord.Interaction, reason):
            embed = discord.Embed(
                title="Gemeldeter User",
                description=f"**User**: {user.mention} ({user.id})",
                color=discord.Color.orange()
            )
            embed.add_field(name="Gemeldet von", value=f"{interaction.user.mention} ({interaction.user.id})", inline=False)
            embed.add_field(name="Grund", value=reason or "Kein Grund angegeben", inline=False)

            channel = interaction.guild.get_channel(self.mod_channel)
            if channel:
                await channel.send(embed=embed)
            await interaction.response.send_message("Der User wurde gemeldet!", ephemeral=True)

        await ctx.interaction.response.send_modal(ReportReasonModal(rcallback))


def setup(bot):
    bot.add_cog(AutoMod(bot))
