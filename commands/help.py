from discord.ext import commands
from discord import app_commands, Interaction
import discord

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", help="Yardım menüsünü açar")
    async def show_help(self, ctx):
        embed = discord.Embed(
            title="**SIBYL Yardım Menüsü**",
            description="Aşağıda botta kullanabileceğiniz komutlar listelenmiştir.",
            color=discord.Color.blue()
        )

        for command in self.bot.commands:
            embed.add_field(name=f"pp {command.name}", value=command.help or "Açıklama bulunmuyor.", inline=False)

        embed.set_footer(text="Sibyl System tarafından desteklenmektedir.")
        await ctx.send(embed=embed)

    @app_commands.command(name="slash_help", description="Yardım menüsünü açar (Slash komutu)")
    async def slash_help(self, interaction: Interaction):
        embed = discord.Embed(
            title="**SIBYL Yardım Menüsü**",
            description="Aşağıda botta kullanabileceğiniz komutlar listelenmiştir.",
            color=discord.Color.blue()
        )

        for command in self.bot.commands:
            embed.add_field(name=f"pp {command.name}", value=command.help or "Açıklama bulunmuyor.", inline=False)

        embed.set_footer(text="Sibyl System tarafından desteklenmektedir.")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))

    if bot.tree.get_command("slash_help") is None:
        bot.tree.add_command(HelpCommand.slash_help)
