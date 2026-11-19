# Host Your Python Telegram Bot + Mini App Online 24/7 for FREE

This project includes a complete **Python (`FastAPI + Uvicorn + httpx`)** backend in [app.py](app.py) that runs both the **Mini App** and the **Telegram Bot** in a single free cloud service.

## Step 1: Push `d:\MiniApp` to GitHub
```bash
git init
git add .
git commit -m "MiniStore KH Python Telegram Bot & Mini App"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ministore-kh.git
git push -u origin main
```

## Step 2: Deploy Free on Render.com (Python)
1. Go to https://render.com and sign in with GitHub (Free plan, no credit card needed).
2. Click **New +** → **Blueprint** (or **Web Service**) and select your GitHub repo.
3. Render automatically reads `render.yaml` (`pip install -r requirements.txt` and `uvicorn app:app --host 0.0.0.0 --port $PORT`).
4. Set these **Environment Variables**:
   - `BOT_TOKEN` = your token from `@BotFather`
   - `ADMIN_CHAT_ID` = your numeric Telegram ID
   - `WEBAPP_URL` = `https://<your-service-name>.onrender.com` (copy the URL Render gives you after first deploy)
   - `USE_WEBHOOK` = `true`
   - `ADMIN_PIN` = `1234` (or your own 4-6 digit PIN)
   - `ALLOW_DEV_MODE` = `false`
5. Click **Deploy** (redeploy once after setting `WEBAPP_URL` so the bot registers `/telegram/webhook` and sets the Telegram Menu Button automatically).

## Step 3: Keep It Awake 24/7 for FREE (Prevent Sleep)
Render's free web service sleeps after 15 minutes of inactivity. To keep your bot & Mini App awake **24/7 for free**:
1. Create a free account at https://cron-job.org or https://uptimerobot.com.
2. Add a new HTTP Monitor / Cron Job:
   - **URL:** `https://<your-service-name>.onrender.com/api/health`
   - **Interval:** Every **10 minutes** (or **5 minutes**).
3. That's it — your Python server + Telegram Bot + Mini App stays online **24/7 for free**!

## Step 4: Link `?startapp` in `@BotFather`
1. Open `@BotFather` → `/mybots` → select your bot → **Bot Settings** → **Configure Mini App**.
2. Set the Web App URL to `https://<your-service-name>.onrender.com`.
3. Your permanent Mini App link is now: `https://t.me/<YourBotUsername>?startapp`
