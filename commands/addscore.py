import discord
from discord.ext import commands
from discord import app_commands
import mysql.connector

def get_mysql_connection():
    return mysql.connector.connect(
        host="localhost",  
        user="root",       
        password="Sifre",  
        database="psycho_pass"  
    )

AUTHORIZED_USERS = ["351090699334057997", "472311035114815488", "344220078465744896", "454670002004688897"]

def update_user_score(user_id, new_score):
    conn = get_mysql_connection()
    cursor = conn.cursor()

    query = "UPDATE psycho_pass SET score = %s WHERE user_id = %s"
    cursor.execute(query, (new_score, user_id))

    if cursor.rowcount == 0:
      
        query = "INSERT INTO psycho_pass (user_id, score) VALUES (%s, %s)"
        cursor.execute(query, (user_id, new_score))
    
    conn.commit()
    conn.close()

class UpdateScore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setscore", help="Bir kullanıcının Psycho-Pass skorunu değiştirir (Yalnızca bot sahibi).")
    async def update_score(self, ctx, user_id: str, new_score: float):
        if str(ctx.author.id) not in AUTHORIZED_USERS:
            await ctx.send("Bu komutu kullanma yetkiniz yok!")
            return
        
        try:
            update_user_score(user_id, new_score)
            user = await self.bot.fetch_user(int(user_id))
            await ctx.send(f"{user.name} adlı kullanıcının Psycho-Pass skoru başarıyla {new_score} olarak güncellendi.")
        except Exception as e:
            await ctx.send(f"Bir hata oluştu: {str(e)}")

    @app_commands.command(name="setscore", description="Bir kullanıcının Psycho-Pass skorunu günceller (Yalnızca yetkililer).")
    async def slash_update_score(self, interaction: discord.Interaction, user_id: str, new_score: float):
        if str(interaction.user.id) not in AUTHORIZED_USERS:
            await interaction.response.send_message("Bu komutu kullanma yetkiniz yok!", ephemeral=True)
            return

        try:
            update_user_score(user_id, new_score)
            user = await self.bot.fetch_user(int(user_id))
            await interaction.response.send_message(f"{user.name} adlı kullanıcının Psycho-Pass skoru başarıyla {new_score} olarak güncellendi.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Bir hata oluştu: {str(e)}", ephemeral=True)

async def setup(bot):
    cog = UpdateScore(bot)
    await bot.add_cog(cog)

    if not bot.tree.get_command("setscore"):
        bot.tree.add_command(cog.slash_setscore)
