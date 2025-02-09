import json, os, time
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch, numpy as np, discord
from dotenv import load_dotenv
from discord.ext import commands
import mysql.connector 

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "Sifre"
MYSQL_DB = "psycho_pass"

db_conn = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DB
)
cursor = db_conn.cursor()

model_name = "TURKCELL/bert-offensive-lang-detection-tr"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name).to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))

dangerous_keywords = ["ölüm", "öldürmek", "intihar", "bıçaklama"]
message_history, spam_warning_history, score_history, psycho_pass_warning_history = {}, {}, {}, {}

def load_json(file):
    return json.load(open(file, "r")) if os.path.exists(file) else {}

def get_mysql_connection():
    return mysql.connector.connect(
        host="localhost",  
        user="root",       
        password="Sifre",  
        database="psycho_pass"  
    )

def get_psycho_pass_level(user_id):
    conn = get_mysql_connection()
    cursor = conn.cursor()

    query = "SELECT score, history, last_warning FROM psycho_pass WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()

    if result:
        score, history, last_warning = result
        history = json.loads(history) if history else []
        return {
            "score": score,
            "history": history,
            "last_warning": last_warning
        }
    else:
        return {
            "score": 0,
            "history": [],
            "last_warning": 0
        }

def is_offensive(sentence):
    inputs = tokenizer(sentence, return_tensors="pt", padding=True, truncation=True, max_length=256).to(model.device)
    logits = model(**inputs).logits
    prediction = np.argmax(logits.cpu().detach().numpy(), axis=1)[0]
    if any(keyword in sentence.lower() for keyword in dangerous_keywords):
        return 'offensive', 1
    return 'non-offensive', prediction

def update_psycho_pass(user_id, is_offensive):
    conn = get_mysql_connection()
    cursor = conn.cursor()

    user_data = get_psycho_pass_level(user_id)
    current_time = time.time()
    user_data["history"] = [entry for entry in user_data["history"] if current_time - entry < 600]

    if is_offensive:
        user_data["score"] += 2
        user_data["history"].append(current_time)
    else:
        user_data["score"] -= 0.2
        user_data["score"] = max(user_data["score"], 0)

    history_str = json.dumps(user_data["history"]) if user_data["history"] is not None else '[]'
    last_warning = user_data["last_warning"] if user_data["last_warning"] is not None else 0

    cursor.execute(f"UPDATE psycho_pass SET score = {user_data['score']}, history = '{history_str}', last_warning = {last_warning} WHERE user_id = '{user_id}'")
    conn.commit()
    conn.close()

    update_score_history(user_id, user_data["score"])

    return check_psycho_pass_increase(user_id), user_data["score"]

def update_score_history(user_id, score):
    current_time = time.time()
    score_history.setdefault(user_id, []).append((current_time, score))
    
    score_history[user_id] = [(t, s) for t, s in score_history[user_id] if current_time - t < 600]

def check_psycho_pass_increase(user_id):
    user_score_history = score_history.get(user_id, [])
    
    if len(user_score_history) < 2: 
        return False
    
    first_score = user_score_history[0][1]
    last_score = user_score_history[-1][1]
    
    return last_score - first_score >= 20

async def send_warning_embed(channel, user, message, warning_type):
    embed = discord.Embed(title=f"**{'Spam' if warning_type == 'spam' else 'Psycho-Pass'} Uyarısı!**", description=f"{user.mention}, {message}", color=discord.Color.orange() if warning_type == "spam" else discord.Color.red())
    embed.set_footer(text="Daha dikkatli olmalısın.")
    await channel.send(embed=embed)

def is_spam(user_id, timestamp):
    message_history.setdefault(user_id, []).append(timestamp)
    message_history[user_id] = [msg_time for msg_time in message_history[user_id] if timestamp - msg_time < 10]
    return len(message_history[user_id]) > 5

def should_send_warning(user_id, warning_history, current_time):
    if current_time - warning_history.get(user_id, 0) >= 600:
        warning_history[user_id] = current_time
        return True
    return False

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

load_dotenv()
bot = commands.Bot(command_prefix="pp ", intents=discord.Intents.default().all(), help_command=None)

@bot.event
async def on_ready():
    await bot.load_extension("commands.psycho_pass")
    await bot.load_extension("commands.criminals")
    await bot.load_extension("commands.help")
    await bot.load_extension("commands.kurulum")
    await bot.load_extension("commands.addscore")
    await bot.load_extension("commands.sunucubilgi")
    print(f'{bot.user} olarak giriş yaptım ve komutlar yüklendi.')

@bot.event
async def on_message(message):
    if message.author.bot:
        return  

    user_id = message.author.id
    current_time = time.time()
    guild_id = message.guild.id

    allowed_commands = ["pp pass", "pp top10", "pp help", "pp sunucubilgi", "pp sb", "pp setup", "pp setscore"]
    if any(message.content.startswith(cmd) for cmd in allowed_commands):
        await bot.process_commands(message)
        return  

    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT ignored_channels FROM server_settings WHERE guild_id = '{guild_id}'")
    result = cursor.fetchone()

    ignored_channels = []
    if result and result[0]:
        ignored_channels = json.loads(result[0])  

    if str(message.channel.id) in ignored_channels:
        print(f"Mesaj {message.channel.name} kanalında atıldığı için yok sayıldı.")
        return  


    user_data = get_psycho_pass_level(user_id)


    if is_spam(user_id, current_time):
        if should_send_warning(user_id, spam_warning_history, current_time):
            print(f"Spam tespit edildi! Kullanıcı: {message.author} - Kullanıcı ID: {user_id}")
            update_psycho_pass(user_id, True)
            

            cursor.execute(f"SELECT score FROM psycho_pass WHERE user_id = '{user_id}'")
            result = cursor.fetchone()
            if result:
                current_score = result[0]
                new_score = current_score + 20
                cursor.execute(f"UPDATE psycho_pass SET score = {new_score} WHERE user_id = '{user_id}'")
                conn.commit()

            await send_warning_embed(message.channel, message.author, "Spam nedeniyle Psycho-Pass skoruna 20 puan eklendi.", "spam")

    result, pred = is_offensive(message.content)
    warning, score = update_psycho_pass(user_id, pred == 1)

    if warning and should_send_warning(user_id, psycho_pass_warning_history, current_time):
        await send_warning_embed(message.channel, message.author, f"Psycho-Pass seviyen 10 dakika içinde çok fazla arttı.\nMevcut Psycho-Pass Seviyesi: {score}", "psycho-pass")

    conn.close()

@bot.event
async def on_member_join(member):
    conn = get_mysql_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT notify_role_id, notify_channel_id, kick_threshold, action_type FROM server_settings WHERE guild_id = %s", (member.guild.id,))
    server_settings = cursor.fetchone()

    if not server_settings:
        return 

    notify_role_id, notify_channel_id, kick_threshold, action_type = server_settings

    user_data = get_psycho_pass_level(member.id)
    score = user_data["score"]

    if score >= 100:
        notify_channel = member.guild.get_channel(int(notify_channel_id))
        notify_role = member.guild.get_role(int(notify_role_id))

        if notify_channel and notify_role:
            created_at = member.created_at.strftime('%d %B %Y')

            embed = discord.Embed(
                title="**Psycho-Pass Uyarısı!**",
                description=f"{member.mention} Psycho-Pass skoru {score} ile sunucuya katıldı!",
                color=discord.Color.red()
            )
            
            embed.add_field(name="Psycho-Pass Skoru", value=f"{score}", inline=False)
            embed.add_field(name="Kullanıcı ID", value=f"{member.id}", inline=False)
            embed.add_field(name="Discord'a Giriş Tarihi", value=created_at, inline=False)
            embed.set_thumbnail(url=member.avatar.url)
            embed.set_footer(text=f"Sibyl System tarafından oluşturuldu.")
            
            await notify_channel.send(content=f"{notify_role.mention}", embed=embed)

        if action_type == 'kick' and score >= kick_threshold:
            try:
                await member.send(f"Psycho-Pass skorun {score} ve bu sunucu için belirlenen sınır {kick_threshold} olduğu için sunucudan atıldın.")
                await member.kick(reason="Psycho-Pass skoru çok yüksek")
            except discord.errors.Forbidden:
                print(f"Kullanıcı {member} sunucudan atılamadı. Yetki eksikliği olabilir.")

        elif action_type == 'ban' and score >= kick_threshold:
            try:
                await member.send(f"Psycho-Pass skorun {score} ve bu sunucu için belirlenen sınır {kick_threshold} olduğu için sunucudan banlandın.")
                await member.ban(reason="Psycho-Pass skoru çok yüksek")
            except discord.errors.Forbidden:
                print(f"Kullanıcı {member} sunucudan banlanamadı. Yetki eksikliği olabilir.")

        elif action_type == 'warn' and score >= kick_threshold:
            try:
                # DM üzerinden kullanıcıya uyarı gönderme
                await member.send(f", Psycho-Pass skorun {score}. Yetkililer seni izliyor.")
            except discord.errors.Forbidden:
                print(f"Kullanıcı {member} uyarı mesajı gönderilemedi.")

    conn.close()


bot.run(os.getenv('TOKEN'))
