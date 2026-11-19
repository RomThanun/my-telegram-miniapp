# NEXUS KH — Telegram Digital Store Mini App & Bot

A complete **Telegram Mini App** + **Telegram Bot** (`grammy` + `Express`) project built from your NEXUS KH digital store template.

## Features
- **Bilingual Storefront (KM / EN)**: AI Tools, Creative & Video, Entertainment subscriptions with USD & KHR (`4,100 ៛`) pricing.
- **Telegram Bot Integration (`grammy`)**:
  - `/start` sends a welcome message with an inline **Open Store** Mini App button and configures the Telegram Chat Menu Button when `WEBAPP_URL` is HTTPS.
  - `/orders` lets customers check their recent order statuses directly in Telegram.
  - `/help` shows commands and the user's Telegram Chat ID.
  - Automatic Telegram notifications to **Admin** on new orders and to the **Customer** on order creation & credential delivery.
- **Server-Side Security**:
  - Official Telegram `initData` HMAC-SHA256 verification (`src/telegramAuth.js`).
  - Server-side price, coupon, and Lucky Wheel reward calculation (never trusts client totals).
  - Admin Dashboard protected by PIN + HMAC-signed session token (`X-Admin-Token`), plus security audit logs.
- **Persistent JSON Storage**: Stores products, orders, user points/streaks/coupons, and audit logs in `data/db.json` (zero native dependencies).

## Quick Start

### 1. Install dependencies
```bash
npm install
```

### 2. Configure `.env`
Copy `.env.example` to `.env` (already created for you) and fill in:
```env
PORT=3000
BOT_TOKEN=123456789:ABCdef...   # From @BotFather
ADMIN_CHAT_ID=123456789         # Your numeric Telegram ID (send /help to your bot or use @userinfobot)
WEBAPP_URL=https://your-https-url.example.com
ADMIN_PIN=1234
SESSION_SECRET=change-this-to-a-random-string
ALLOW_DEV_MODE=true             # Set false in production
```

### 3. Run the server + bot
```bash
npm start
```
The Mini App runs at `http://localhost:3000`.

### 4. Link with Telegram (HTTPS required by Telegram)
Telegram Mini Apps require an **HTTPS** URL. For local testing, start an HTTPS tunnel such as Cloudflare Tunnel or ngrok:
```bash
cloudflared tunnel --url http://localhost:3000
```
Copy the generated `https://....trycloudflare.com` URL into `WEBAPP_URL=` in `.env`, then restart `npm start`.

Optionally, in `@BotFather`:
1. Send `/newapp` or `/mybots` → select your bot → **Bot Settings** → **Menu Button** → **Configure menu button** and paste your `WEBAPP_URL`.
2. Send `/start` to your bot in Telegram and tap **🛒 Open Store**!
