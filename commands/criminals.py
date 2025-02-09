import mysql.connector
from discord.ext import commands
import discord

def get_mysql_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sifre",
        database="psycho_pass"
    )

def get_top_criminals():
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT user_id, score FROM psycho_pass ORDER BY score DESC LIMIT 10"
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    return results

class Criminals(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="top10", help="En yüksek suç oranına sahip kullanıcılar")
    async def top_criminals(self, ctx):
        top_users = get_top_criminals()
        
        embed = discord.Embed(
            title="**Top 10 Psycho-Pass Seviyesine Sahip Kullanıcı**",
            description="En yüksek Psycho-Pass seviyesine sahip kullanıcılar:",
            color=discord.Color.purple()
        )
        
        for i, user_data in enumerate(top_users, start=1):
            user_id = user_data['user_id']
            score = user_data['score']
            
            try:
                user = await self.bot.fetch_user(int(user_id))
                embed.add_field(name=f"{i}. {user.name}", value=f"Psycho-Pass: {score}", inline=False)
            except discord.errors.NotFound:
                embed.add_field(name=f"{i}. [Bilinmeyen Kullanıcı]", value=f"Psycho-Pass: {score}", inline=False)
            except Exception as e:
                print(f"An error occurred when fetching user {user_id}: {e}")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Criminals(bot))
