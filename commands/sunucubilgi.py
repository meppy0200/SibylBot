from discord.ext import commands
from discord import app_commands, Interaction
import discord
import mysql.connector
import time

def get_mysql_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sifre",
        database="psycho_pass"
    )

class SunucuBilgi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_psycho_pass_stats(self):
        conn = get_mysql_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id, score FROM psycho_pass ORDER BY score DESC LIMIT 1")
        highest_user = cursor.fetchone()

        cursor.execute("SELECT AVG(score) FROM psycho_pass WHERE score > 0")
        avg_score = cursor.fetchone()[0]

        conn.close()
        return highest_user, avg_score or 0

    @commands.command(name="sunucubilgi", aliases=["sb"], help="Sunucu bilgilerini gösterir.")
    async def show_server_info(self, ctx):
        guild = ctx.guild

        owner = guild.owner
        created_at = guild.created_at.strftime('%d %B %Y')
        member_count = guild.member_count
        icon_url = guild.icon.url if guild.icon else None

        highest_user, avg_score = self.get_psycho_pass_stats()

        embed = discord.Embed(
            title=f"**{guild.name} Sunucu Bilgileri**",
            description=f"{guild.name} hakkında bilgiler aşağıda verilmiştir.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Sunucu Sahibi", value=owner.mention, inline=False)
        embed.add_field(name="Sunucu Kuruluş Tarihi", value=created_at, inline=False)
        embed.add_field(name="Toplam Üye", value=str(member_count), inline=False)
        embed.add_field(name="Psycho-Pass Ortalaması", value=f"{round(avg_score, 2)}", inline=False)
        if icon_url:
            embed.set_thumbnail(url=icon_url)

        await ctx.send(embed=embed)

    @app_commands.command(name="sunucubilgi", description="Sunucu bilgilerini gösterir.")
    async def slash_show_server_info(self, interaction: Interaction):
        guild = interaction.guild

        owner = guild.owner
        created_at = guild.created_at.strftime('%d %B %Y')
        member_count = guild.member_count
        icon_url = guild.icon.url if guild.icon else None

        highest_user, avg_score = self.get_psycho_pass_stats()

        embed = discord.Embed(
            title=f"**{guild.name} Sunucu Bilgileri**",
            description=f"{guild.name} hakkında bilgiler aşağıda verilmiştir.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Sunucu Sahibi", value=owner.mention, inline=False)
        embed.add_field(name="Sunucu Kuruluş Tarihi", value=created_at, inline=False)
        embed.add_field(name="Toplam Üye", value=str(member_count), inline=False)
        if highest_user:
            embed.add_field(name="En Yüksek Psycho-Pass Skoru", value=f"<@{highest_user[0]}> - {round(highest_user[1], 2)}", inline=False)
        else:
            embed.add_field(name="En Yüksek Psycho-Pass Skoru", value="Veri bulunamadı", inline=False)
        embed.add_field(name="Psycho-Pass Ortalaması", value=f"{round(avg_score, 2)}", inline=False)
        if icon_url:
            embed.set_thumbnail(url=icon_url)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(SunucuBilgi(bot))

    if bot.tree.get_command("sunucubilgi") is None:
        bot.tree.add_command(SunucuBilgi.slash_show_server_info)
