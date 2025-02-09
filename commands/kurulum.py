import mysql.connector
import discord
from discord.ext import commands
from discord import app_commands


def get_mysql_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sifre",
        database="psycho_pass"
    )


def save_server_settings(guild_id, notify_role_id, notify_channel_id, kick_threshold):
    conn = get_mysql_connection()
    cursor = conn.cursor()
    
    query = """
    INSERT INTO server_settings (guild_id, notify_role_id, notify_channel_id, kick_threshold)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    notify_role_id = VALUES(notify_role_id),
    notify_channel_id = VALUES(notify_channel_id),
    kick_threshold = VALUES(kick_threshold)
    """
    
    cursor.execute(query, (guild_id, notify_role_id, notify_channel_id, kick_threshold))
    conn.commit()
    conn.close()


def load_server_settings(guild_id):
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT * FROM server_settings WHERE guild_id = %s"
    cursor.execute(query, (guild_id,))
    result = cursor.fetchone()
    conn.close()
    
    return result

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setup")
    @commands.has_permissions(administrator=True, manage_roles=True)
    async def setup(self, ctx):
        guild_id = str(ctx.guild.id)

        def check_author(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await ctx.send("Psycho-Pass bot kurulumu için yetkili rolünün ID'sini girin (Rol etiketlemeden ID'sini girmeniz gerekmektedir).")

        try:
            role_msg = await self.bot.wait_for('message', timeout=60.0, check=check_author)
            notify_role_id = role_msg.content

            await ctx.send("Lütfen Psycho-Pass uyarılarının gönderileceği kanalın ID'sini girin.")
            channel_msg = await self.bot.wait_for('message', timeout=60.0, check=check_author)
            notify_channel_id = channel_msg.content

            notify_channel = self.bot.get_channel(int(notify_channel_id))
            if not notify_channel:
                await ctx.send("Geçersiz kanal ID'si girdiniz. Lütfen doğru bir kanal ID'si girin.")
                return

            try:
                test_message = await notify_channel.send("Kurulum doğrulama mesajı: Bu kanalda mesaj gönderilebiliyor.")
                await test_message.delete()
            except discord.Forbidden:
                await ctx.send("Botun bu kanala mesaj gönderme yetkisi yok. Lütfen yetkileri kontrol edin ve tekrar deneyin.")
                return

            await ctx.send("Opsiyonel olarak, kullanıcıları belirli bir Psycho-Pass skorunun üzerinde atmak isterseniz bir skor girin. Eğer bu özelliği kullanmak istemiyorsanız 'skip' yazabilirsiniz. (Daha sonradan https://sibylbot.com/control-panel üzerinden değiştirebilirsiniz)")
            threshold_msg = await self.bot.wait_for('message', timeout=90.0, check=check_author)

            if threshold_msg.content.lower() == 'skip':
                kick_threshold = None
            else:
                kick_threshold = int(threshold_msg.content)

            save_server_settings(guild_id, notify_role_id, notify_channel_id, kick_threshold)
            await ctx.send(f"Kurulum tamamlandı! Bildirimler {notify_role_id} rolüne {notify_channel_id} kanalında yapılacak.")
        
        except TimeoutError:
            await ctx.send("Kurulum süresi doldu. Lütfen tekrar deneyin.")

    @app_commands.command(name="setup", description="Psycho-Pass bot kurulumu yapar")
    @app_commands.checks.has_permissions(administrator=True, manage_roles=True)
    async def slash_setup(self, interaction: discord.Interaction, 
                          notify_role_id: str, 
                          notify_channel_id: str, 
                          kick_threshold: int = None):
        guild_id = str(interaction.guild.id)

        notify_channel = self.bot.get_channel(int(notify_channel_id))
        if not notify_channel:
            await interaction.response.send_message("Geçersiz kanal ID'si girdiniz. Lütfen doğru bir kanal ID'si girin.", ephemeral=True)
            return

        try:
            test_message = await notify_channel.send("Kurulum doğrulama mesajı: Bu kanalda mesaj gönderilebiliyor.")
            try:
                await test_message.delete()
            except discord.Forbidden:
                await interaction.response.send_message("Botun bu kanalda mesaj silemediği fark edildi, ancak mesaj gönderebiliyor.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Bir hata oluştu. Lütfen pp setup komutunu kullanın", ephemeral=True)
            return

        save_server_settings(guild_id, notify_role_id, notify_channel_id, kick_threshold)
        await interaction.response.send_message(f"Kurulum tamamlandı! Bildirimler {notify_role_id} rolüne {notify_channel_id} kanalında yapılacak.", ephemeral=True)

async def setup(bot):
    cog = Setup(bot)
    await bot.add_cog(cog)

    if not bot.tree.get_command("setup"):
        bot.tree.add_command(cog.slash_setup)
