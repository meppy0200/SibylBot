const express = require('express');
const session = require('express-session');
const passport = require('passport');
const DiscordStrategy = require('passport-discord').Strategy;
const path = require('path');
const mysql = require('mysql2/promise'); // MySQL için gerekli modül
const fs = require('fs');
require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');

// MySQL bağlantısı
const db = mysql.createPool({
    host: '127.0.0.1', 
    user: 'root',
    password: 'Sifre',
    database: 'psycho_pass'
});

const bot = new Client({
    intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMembers]
});

const BOT_TOKEN = process.env.TOKEN;
bot.login(BOT_TOKEN);

const app = express();
const port = 3000;
const API_KEY = process.env.API_KEY || 'Anim3ciX'; 

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

passport.use(new DiscordStrategy({
    clientID: process.env.DISCORD_CLIENT_ID,
    clientSecret: process.env.DISCORD_CLIENT_SECRET,
    callbackURL: process.env.DISCORD_CALLBACK_URL,
    scope: ['identify', 'guilds']
}, function (accessToken, refreshToken, profile, done) {
    return done(null, profile);
}));

passport.serializeUser((user, done) => done(null, user));
passport.deserializeUser((obj, done) => done(null, obj));

app.use(session({
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: false
}));
app.use(passport.initialize());
app.use(passport.session());

app.set('view engine', 'ejs');
app.use(express.static('public'));

function getAvatarURL(user) {
    if (!user.avatar) {
        return 'https://cdn.discordapp.com/embed/avatars/0.png';
    }
    return `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png?size=512`;
}

function getGuildIconURL(guild) {
    if (!guild.icon) {
        return 'https://cdn.discordapp.com/embed/avatars/0.png';
    }
    return `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png?size=512`;
}

async function getBotGuildsFromDB() {
    try {
        const [rows] = await db.query("SELECT guild_id, guild_name FROM bot_guilds");
        return rows;
    } catch (err) {
        console.error("MySQL'den bot sunucu bilgileri alınamadı:", err);
        return [];
    }
}

async function loadServerSettings(guildID) {
    const [rows] = await db.execute('SELECT * FROM server_settings WHERE guild_id = ?', [guildID]);

    if (rows.length > 0) {
        const settings = rows[0];
        settings.ignored_channels = settings.ignored_channels ? JSON.parse(settings.ignored_channels) : [];
        return settings;
    }

    return null;
}


async function saveServerSettings(guildID, notifyRoleID, notifyChannelID, kickThreshold, joinActionType, existingMemberActionType, ignoredChannels) {
    const [rows] = await db.execute('SELECT guild_id FROM server_settings WHERE guild_id = ?', [guildID]);

    notifyRoleID = notifyRoleID || null;
    notifyChannelID = notifyChannelID || null;
    kickThreshold = kickThreshold || null;
    joinActionType = joinActionType || null;
    existingMemberActionType = existingMemberActionType || null;
    ignoredChannels = ignoredChannels ? JSON.stringify(ignoredChannels) : null;  

    if (rows.length === 0) {
        // Yeni kayıt oluştur
        await db.execute('INSERT INTO server_settings (guild_id, notify_role_id, notify_channel_id, kick_threshold, join_action_type, existing_member_action_type, ignored_channels) VALUES (?, ?, ?, ?, ?, ?, ?)', 
            [guildID, notifyRoleID, notifyChannelID, kickThreshold, joinActionType, existingMemberActionType, ignoredChannels]);
    } else {
        // Mevcut kaydı güncelle
        await db.execute('UPDATE server_settings SET notify_role_id = ?, notify_channel_id = ?, kick_threshold = ?, join_action_type = ?, existing_member_action_type = ?, ignored_channels = ? WHERE guild_id = ?', 
            [notifyRoleID, notifyChannelID, kickThreshold, joinActionType, existingMemberActionType, ignoredChannels, guildID]);
    }
}


async function updatePsychoPassData(userID, score) {
    const [rows] = await db.execute('SELECT user_id FROM psycho_pass WHERE user_id = ?', [userID]);

    if (rows.length === 0) {
        // Eğer kullanıcı yoksa yeni kayıt ekle
        await db.execute('INSERT INTO psycho_pass (user_id, score, history, last_warning) VALUES (?, ?, ?, ?)', 
            [userID, score, '[]', 0]);
    } else {
        // Eğer kullanıcı varsa skoru güncelle
        await db.execute('UPDATE psycho_pass SET score = ? WHERE user_id = ?', [score, userID]);
    }
}

async function loadPsychoPassData(userID) {
    try {
        const [rows] = await db.query("SELECT score, history, last_warning FROM psycho_pass WHERE user_id = ?", [userID]);
        if (rows.length > 0) {
            const user = rows[0];
            return {
                score: user.score,
                history: JSON.parse(user.history || '[]'),
                last_warning: user.last_warning
            };
        } else {
            return { score: 0, history: [], last_warning: 0 };
        }
    } catch (err) {
        console.error("MySQL'den Psycho-Pass verisi alınamadı:", err);
        return { score: 0, history: [], last_warning: 0 }; 
    }
}

app.get('/auth/discord', passport.authenticate('discord'));

app.get('/auth/discord/redirect',
    passport.authenticate('discord', { failureRedirect: '/' }),
    (req, res) => {
        res.redirect('/control-panel');
    }
);
app.post('/control-server/:guildID', async (req, res) => {
    const { notify_role_id, notify_channel_id, kick_threshold, action_type, ignored_channels } = req.body;
    const guildID = req.params.guildID;

    // ignored_channels verisini diziye çevir
    const ignoredChannelsArray = ignored_channels ? ignored_channels.split(',') : [];

    const ignoredChannelsJSON = JSON.stringify(ignoredChannelsArray);

    // Veritabanına kaydetme işlemi
    const query = `
        INSERT INTO server_settings (guild_id, notify_role_id, notify_channel_id, kick_threshold, action_type, ignored_channels)
        VALUES (?, ?, ?, ?, ?, ?)
        ON DUPLICATE KEY UPDATE notify_role_id = ?, notify_channel_id = ?, kick_threshold = ?, action_type = ?, ignored_channels = ?;
    `;

    await db.query(query, [
        guildID, notify_role_id, notify_channel_id, kick_threshold, action_type, ignoredChannelsJSON,
        notify_role_id, notify_channel_id, kick_threshold, action_type, ignoredChannelsJSON
    ]);

    res.redirect(`/control-server/${guildID}`);
});

app.get('/control-server/:guildID', async (req, res) => {
    if (!req.isAuthenticated() || !req.user || !req.user.guilds) {
        return res.redirect('/login'); 
    }

    const guildID = req.params.guildID;
    const userGuild = req.user.guilds.find(guild => guild.id === guildID && (guild.permissions & 0x8) === 0x8);

    if (!userGuild) {
        return res.status(403).send('Bu sunucu için yetkiniz yok.');
    }

    let serverSettings = await loadServerSettings(guildID);

    if (!serverSettings) {
        await saveServerSettings(guildID, "", "", 250, "kick");
        serverSettings = await loadServerSettings(guildID); 
    }

    const guild = bot.guilds.cache.get(guildID);
    
    if (!guild) {
        return res.status(404).send('Bot bu sunucuda bulunmuyor.');
    }
    const channels = guild.channels.cache
        .filter(channel => channel.type === 0)
        .map(channel => ({
            id: channel.id,
            name: channel.name
        }));

    const roles = guild.roles.cache.map(role => ({
        id: role.id,
        name: role.name
    }));

    res.render('control-server', {
        guildID,
        guildName: userGuild.name,
        settings: serverSettings,
        channels,  
        roles      
    });
});


app.get('/control-panel', async (req, res) => {
    if (!req.isAuthenticated()) {
        return res.redirect('/login');
    }

    const userID = req.user.id;
    
    const psychoPassData = await loadPsychoPassData(userID);

    req.user.avatarURL = getAvatarURL(req.user);

    const botGuilds = await getBotGuildsFromDB();
    const botGuildIDs = botGuilds.map(guild => guild.guild_id.toString());

    console.log("Veritabanından alınan bot sunucuları:", botGuildIDs);  

    const adminGuilds = req.user.guilds
        .filter(guild => (guild.permissions & 0x8) === 0x8) 
        .map(guild => {
            const hasBot = botGuildIDs.includes(guild.id.toString()); 
            guild.hasBot = hasBot;
            guild.iconURL = getGuildIconURL(guild);
            return guild;
        });

    const totalMembers = adminGuilds.reduce((acc, guild) => acc + (guild.memberCount || 0), 0);

    res.render('control-panel', { 
        user: req.user, 
        adminGuilds, 
        psychoPassData, 
        totalMembers
    });
});
bot.on('guildCreate', async guild => {
    try {
        const [existingGuild] = await db.query("SELECT guild_id FROM bot_guilds WHERE guild_id = ?", [guild.id]);
        
        if (existingGuild.length === 0) {
            await db.query("INSERT INTO bot_guilds (guild_id, guild_name) VALUES (?, ?)", [guild.id, guild.name]);
            console.log(`Bot ${guild.name} sunucusuna eklendi.`);
        }
    } catch (err) {
        console.error("Sunucu eklenirken bir hata oluştu:", err);
    }
});

bot.on('guildDelete', async guild => {
    try {
        await db.query("DELETE FROM bot_guilds WHERE guild_id = ?", [guild.id]);
        console.log(`Bot ${guild.name} sunucusundan çıkarıldı.`);
    } catch (err) {
        console.error("Sunucu silinirken bir hata oluştu:", err);
    }
});

app.get('/login', (req, res) => {
    res.render('login');
});

app.get('/tos', (req, res) => {
    res.render('tos');
});

app.get('/legal', (req, res) => {
    res.render('legal');
});

app.get('/donate', (req, res) => {
    res.render('donate');
});

app.get('/', (req, res) => {
    const serverCount = bot.guilds.cache.size;
    const userCount = bot.guilds.cache.reduce((acc, guild) => acc + guild.memberCount, 0);
    res.render('index', { serverCount, userCount });
});

app.get('/features', (req, res) => {
    const serverCount = bot.guilds.cache.size;
    const userCount = bot.guilds.cache.reduce((acc, guild) => acc + guild.memberCount, 0);
    res.render('features', { serverCount, userCount });
});

app.listen(port, () => {
    console.log(`Sunucu şu adreste çalışıyor: http://localhost:${port}`);
});

app.get('/api/psycho-pass', async (req, res) => {
    const apiKey = req.headers['api-key'];
    if (apiKey !== API_KEY) {
        return res.status(403).json({ error: "Unauthorized access" });
    }

    const userId = req.query.user_id;
    if (!userId) {
        return res.status(400).json({ error: "user_id is required" });
    }

    const psychoPassData = await loadPsychoPassData(userId);
    if (!psychoPassData) {
        return res.status(404).json({ error: "User not found" });
    }

    return res.json({
        user_id: userId,
        score: psychoPassData.score
    });
});

app.post('/api/update-psycho-pass', async (req, res) => {
    const apiKey = req.headers['api-key'];
    if (apiKey !== API_KEY) {
        return res.status(403).json({ error: "Unauthorized access" });
    }

    const { user_id, score } = req.body;
    if (!user_id || typeof score !== 'number') {
        return res.status(400).json({ error: "user_id and score are required and score must be a number" });
    }

    try {
        await updatePsychoPassData(user_id, score);
        return res.json({ success: true, message: "Psycho-Pass score updated", user_id, score });
    } catch (error) {
        console.error("Psycho-Pass güncellenirken bir hata oluştu:", error);
        return res.status(500).json({ error: "Internal server error" });
    }
});

bot.on('ready', () => {
    console.log(`${bot.user.tag} olarak giriş yaptım!`);
    bot.guilds.cache.forEach(guild => {
        console.log(`Botun olduğu sunucu: ${guild.name} (${guild.id})`);
    });
});
