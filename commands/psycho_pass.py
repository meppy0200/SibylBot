import mysql.connector
from discord.ext import commands
import discord
from discord import app_commands


def get_mysql_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sifre",
        database="psycho_pass"
    )

def get_psycho_pass_level(user_id):
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT score FROM psycho_pass WHERE user_id = %s"
    cursor.execute(query, (str(user_id),))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result["score"]
    return 0

def get_psycho_pass_status(score):
    if score >= 300:
        return discord.Color.red(), "En Tehlikeli"
    elif 200 <= score < 300:
        return discord.Color.orange(), "Tehlikeli"
    elif 100 <= score < 200:
        return discord.Color.gold(), "Dikkat"
    else:
        return discord.Color.green(), "Normal"

class PsychoPass(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pass", help="Psycho-Pass durumunuzu gösterir")
    async def psycho_score(self, ctx):
        score = get_psycho_pass_level(ctx.author.id)
        
        embed_color, danger_level = get_psycho_pass_status(score)

        embed = discord.Embed(
            title="**Psycho-Pass Seviyesi**",
            description=f"{ctx.author.mention}, şu anki Psycho-Pass seviyen:",
            color=embed_color
        )
        
        embed.add_field(name="Psycho-Pass Skoru", value=f"{score}", inline=True)
        embed.add_field(name="Tehlike Durumu", value=danger_level, inline=True)

        embed.set_thumbnail(url=ctx.bot.user.avatar.url)
        embed.set_footer(text="Sibyl System")

        await ctx.send(embed=embed)

    @app_commands.command(name="pass", description="Psycho-Pass durumunuzu gösterir")
    async def slash_psycho_score(self, interaction: discord.Interaction):
        score = get_psycho_pass_level(interaction.user.id)
        
        embed_color, danger_level = get_psycho_pass_status(score)

        embed = discord.Embed(
            title="**Psycho-Pass Seviyesi**",
            description=f"{interaction.user.mention}, şu anki Psycho-Pass seviyen:",
            color=embed_color
        )
        
        embed.add_field(name="Psycho-Pass Skoru", value=f"{score}", inline=True)
        embed.add_field(name="Tehlike Durumu", value=danger_level, inline=True)

        embed.set_thumbnail(url=interaction.client.user.avatar.url)
        embed.set_footer(text="Sibyl System")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PsychoPass(bot))
    
    bot.tree.clear_commands(guild=None)
    try:
        bot.tree.add_command(PsychoPass.slash_psycho_score)
    except discord.app_commands.errors.CommandAlreadyRegistered:
        print("Slash command 'psychopass_slash' already registered")
