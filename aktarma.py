import json
import mysql.connector

db_config = {
    'user': 'root',
    'password': 'Sifre',
    'host': '127.0.0.1',
    'database': 'psycho_pass'
}

json_file_path = 'bot_guilds.json'

with open(json_file_path, 'r', encoding='utf-8') as json_file:
    guild_data = json.load(json_file)

db_conn = mysql.connector.connect(**db_config)
cursor = db_conn.cursor()


for guild_id, guild_info in guild_data.items():
    guild_name = guild_info['name']

    try:
        cursor.execute("""
            INSERT INTO bot_guilds (guild_id, guild_name)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE guild_name = VALUES(guild_name)
        """, (guild_id, guild_name))
    except mysql.connector.Error as err:
        print(f"Veritabanına eklenirken bir hata oluştu: {err}")
        continue


db_conn.commit()
cursor.close()
db_conn.close()

print("JSON verileri MySQL'e aktarıldı.")
