# Discord Bot

Bu projeyi tamamen öğrenme amaçlı, ChatGPT ile birlikte geliştirdim o yüzden proje %100 bana ait değildir. Psycho-Pass adındaki anime serisinden esinlenerek "Discord" platformundaki kullanıcılara bir sicil çıkartmak üzere geliştirmekteydim. Discord, Türkiye'de yasaklandığı zaman geliştirmeyi bıraktım. 

## Özellikler

- Türkcell'in açık kaynak yapay zekasını kullanarak kullanıcının mesajlarını tarar ve ofansif olup olmadığını belirler.
- Belirlenene göre kullanıcının siciline puan ekler veya sicilinden puan eksiltir.
- Otomatik moderasyon
- API entegrasyonları
- Sunucu yönetimi (kick, ban vb.)
- Discord kimlik doğrulaması
- MySQL veritabanı entegrasyonu

## Gereksinimler

Bu botu çalıştırmadan önce aşağıdaki bağımlılıkların yüklü olduğundan emin olun:

- Python 3.8 veya daha yeni bir sürüm
- `discord.py` kütüphanesi
- `requests` (API çağrıları için)
- Node.js 16 veya daha yeni bir sürüm
- `discord.js`, `express`, `passport-discord`, `mysql2`, `dotenv`, `express-session`

Bağımlılıkları yüklemek için:

```bash
npm install
```

## Kurulum

1. **Discord Geliştirici Portalı'ndan bir bot oluşturun** ve token'ınızı alın.
2. Bu repoyu klonlayın:

   ```bash
   git clone https://github.com/meppy0200/SibylBot
   cd SibylBot
   ```

3. Çevre değişkenlerinizi ayarlayın veya `.env` dosyanızı oluşturun:

   ```env
   DISCORD_CLIENT_ID=your_client_id_here
   DISCORD_CLIENT_SECRET=your_client_secret_here
   DISCORD_CALLBACK_URL=http://localhost:3000/auth/discord/redirect
   TOKEN=your_bot_token_here
   SESSION_SECRET=your_session_secret_here
   API_KEY=your_api_key_here
   ```

4. Botu ve Dashboard'ı başlatın.:

   ```bash
   node server.js
   python sibyl.py
   ```

## Kullanım

Botu çalıştırdıktan sonra, Discord sunucunuzda belirlenen komutları kullanabilirsiniz. Örneğin:

- `pp yardım` ile komutları görebilirsiniz.

Ayrıca web paneli üzerinden sunucu ayarlarını yönetebilirsiniz.

## API

- **Psycho-Pass Bilgisi Al**: `GET /api/psycho-pass?user_id=DISCORD_USER_ID`
- **Psycho-Pass Güncelle**: `POST /api/update-psycho-pass`
  ```json
  {
    "user_id": "DISCORD_USER_ID",
    "score": 75
  }
  ```

## Lisans

Bu proje MIT Lisansı ile lisanslanmıştır. Daha fazla bilgi için aşağıdaki lisans metnine göz atabilirsiniz.

```
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

Herhangi bir sorunuz varsa, lütfen GitHub üzerinden issue açın veya bana ulaşın!

