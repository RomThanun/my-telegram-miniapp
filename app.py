import asyncio
import base64
import hashlib
import hmac
import json
import os
import random
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qsl

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

# =========================================================================
# 1. CONFIGURATION
# =========================================================================
BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "db.json"

PORT = int(os.getenv("PORT", "3000"))
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip().rstrip("/")
ADMIN_PIN = os.getenv("ADMIN_PIN", "1234").strip()
SESSION_SECRET = os.getenv("SESSION_SECRET", "nexus-kh-dev-secret").strip()
ALLOW_DEV_MODE = os.getenv("ALLOW_DEV_MODE", "true").lower() == "true"
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"
EXCHANGE_RATE = 4100

DEFAULT_PRODUCTS = [
    {
        "id": "gemini-adv",
        "name": "Gemini Advanced (Google AI)",
        "category": "ai",
        "badge": "HOT AI",
        "inStock": True,
        "badgeClass": "bg-cyan-500/15 text-cyan-300 border-cyan-500/30",
        "accent": "from-blue-500 to-cyan-400",
        "descKm": "ប្រើប្រាស់ Gemini Ultra, 2TB Google Drive និងភ្ជាប់ក្នុង Gmail/Docs ផ្ទាល់។",
        "descEn": "Unlock Gemini Ultra, 2TB Google One storage & Workspace AI.",
        "iconSvg": '<svg class="w-7 h-7 text-white" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C12.4 7.2 16.8 11.6 22 12C16.8 12.4 12.4 16.8 12 22C11.6 16.8 7.2 12.4 2 12C7.2 11.6 11.6 7.2 12 2Z"/></svg>',
        "plans": [
            {"id": "1m", "labelKm": "1 ខែ (Upgrade លើ Email ផ្ទាល់)", "labelEn": "1 Month (Your Own Email)", "price": 4.50},
            {"id": "3m", "labelKm": "3 ខែ (Upgrade លើ Email ផ្ទាល់)", "labelEn": "3 Months (Your Own Email)", "price": 12.00},
            {"id": "1y", "labelKm": "1 ឆ្នាំ (2TB + Gemini Ultra)", "labelEn": "1 Year (2TB + Gemini Ultra)", "price": 35.00},
        ],
    },
    {
        "id": "chatgpt-plus",
        "name": "ChatGPT Plus (GPT-4o / o1)",
        "category": "ai",
        "badge": "BEST SELLER",
        "inStock": True,
        "badgeClass": "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
        "accent": "from-emerald-500 to-teal-500",
        "descKm": "ប្រើ GPT-4o, o1, បង្កើតរូបភាព DALL·E 3 និងវិភាគឯកសារគ្មានដែនកំណត់។",
        "descEn": "Full access to GPT-4o, o1 reasoning, DALL·E 3 & Custom GPTs.",
        "iconSvg": '<svg class="w-7 h-7 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3a5 5 0 0 1 4.5 2.8A5 5 0 0 1 21 10.5a5 5 0 0 1-2.5 4.3A5 5 0 0 1 14 21a5 5 0 0 1-4.5-2.8A5 5 0 0 1 3 13.5a5 5 0 0 1 2.5-4.3A5 5 0 0 1 10 3h2z"/></svg>',
        "plans": [
            {"id": "1m-sh", "labelKm": "1 ខែ (Shared ធានាពេញខែ)", "labelEn": "1 Month (Shared Warranty)", "price": 5.00},
            {"id": "1m-pr", "labelKm": "1 ខែ (គណនីផ្ទាល់ខ្លួន Private)", "labelEn": "1 Month (Private Account)", "price": 16.50},
        ],
    },
    {
        "id": "claude-pro",
        "name": "Claude 3.5 Sonnet Pro",
        "category": "ai",
        "badge": "CODING PRO",
        "inStock": True,
        "badgeClass": "bg-amber-500/15 text-amber-300 border-amber-500/30",
        "accent": "from-orange-500 to-amber-500",
        "descKm": "AI ឆ្លាតវៃបំផុតសម្រាប់សរសេរកូដ អត្ថបទ និង Artifacts ជាមួយ Context ធំ។",
        "descEn": "Top AI for coding, writing & Artifacts with 5x higher limits.",
        "iconSvg": '<svg class="w-7 h-7 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3"><path stroke-linecap="round" d="M12 3v18M4.2 7.5l15.6 9M19.8 7.5L4.2 16.5"/></svg>',
        "plans": [
            {"id": "1m-sh", "labelKm": "1 ខែ (Shared 4 នាក់)", "labelEn": "1 Month (Shared 4 Users)", "price": 5.50},
            {"id": "1m-pr", "labelKm": "1 ខែ (គណនីផ្ទាល់ខ្លួន)", "labelEn": "1 Month (Private Account)", "price": 18.00},
        ],
    },
    {
        "id": "capcut-pro",
        "name": "CapCut Pro (PC & Mobile)",
        "category": "creative",
        "badge": "POPULAR",
        "inStock": True,
        "badgeClass": "bg-violet-500/15 text-violet-300 border-violet-500/30",
        "accent": "from-violet-600 to-indigo-600",
        "descKm": "ដោះសោ Effect Pro ទាំងអស់ Auto Captions, AI Remove BG គ្មាន Watermark។",
        "descEn": "Unlock all Pro effects, Auto Captions & AI Tools on PC/Mobile.",
        "iconSvg": '<svg class="w-7 h-7 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 7l16 10M20 7L4 17M4 7v10M20 7v10"/></svg>',
        "plans": [
            {"id": "1m", "labelKm": "1 ខែ (ប្រើបាន 2 ឧបករណ៍)", "labelEn": "1 Month (2 Devices)", "price": 2.50},
            {"id": "6m", "labelKm": "6 ខែ (គណនីផ្ទាល់ខ្លួន)", "labelEn": "6 Months (Private)", "price": 11.00},
            {"id": "1y", "labelKm": "1 ឆ្នាំ (ធានា 12 ខែពេញ)", "labelEn": "1 Year (Full Warranty)", "price": 19.00},
        ],
    },
    {
        "id": "canva-pro",
        "name": "Canva Pro (Brand & AI)",
        "category": "creative",
        "badge": "BEST VALUE",
        "inStock": True,
        "badgeClass": "bg-sky-500/15 text-sky-300 border-sky-500/30",
        "accent": "from-sky-500 to-blue-600",
        "descKm": "ឌីហ្សាញរូបភាព ឡូហ្គោ វីដេអូ ប្រើ Template Pro ជាង 100 លាន និង Magic AI។",
        "descEn": "100M+ Pro templates, Brand Kit, BG Remover & Magic Studio.",
        "iconSvg": '<svg class="w-7 h-7 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path stroke-linecap="round" d="M16.5 7.5a6 6 0 1 0 0 9"/></svg>',
        "plans": [
            {"id": "1y", "labelKm": "1 ឆ្នាំ (Invite ចូល Email ផ្ទាល់)", "labelEn": "1 Year (Direct Email Invite)", "price": 3.00},
            {"id": "life", "labelKm": "ប្រើប្រាស់យូរអង្វែង (Pro)", "labelEn": "Lifetime Pro Access", "price": 6.50},
        ],
    },
    {
        "id": "netflix-4k",
        "name": "Netflix Premium 4K UHD",
        "category": "entertainment",
        "badge": "4K HDR",
        "inStock": True,
        "badgeClass": "bg-rose-500/15 text-rose-300 border-rose-500/30",
        "accent": "from-rose-600 to-red-700",
        "descKm": "ទស្សនាភាពយន្តកម្រិត 4K Ultra HD មាន Profile ផ្ទាល់ខ្លួន និងដាក់លេខកូដ PIN បាន។",
        "descEn": "Ultra HD 4K streaming with dedicated Private Profile & PIN lock.",
        "iconSvg": '<svg class="w-7 h-7 text-white" viewBox="0 0 24 24" fill="currentColor"><path d="M6 3h3.5l5 11.5V3H18v18h-3.5l-5-11.5V21H6V3z"/></svg>',
        "plans": [
            {"id": "1m", "labelKm": "1 ខែ (1 Profile + PIN ផ្ទាល់ខ្លួន)", "labelEn": "1 Month (Private Profile + PIN)", "price": 3.50},
            {"id": "3m", "labelKm": "3 ខែ (1 Profile + PIN ផ្ទាល់ខ្លួន)", "labelEn": "3 Months (Private Profile + PIN)", "price": 9.50},
        ],
    },
    {
        "id": "spotify-prem",
        "name": "Spotify Premium Individual",
        "category": "entertainment",
        "badge": "NO ADS",
        "inStock": True,
        "badgeClass": "bg-green-500/15 text-green-300 border-green-500/30",
        "accent": "from-green-500 to-emerald-600",
        "descKm": "ស្តាប់តន្ត្រីគ្មានពាណិជ្ជកម្ម ទាញយកស្តាប់ Offline គុណភាពសំឡេងច្បាស់បំផុត។",
        "descEn": "Ad-free music listening, offline downloads & lossless audio.",
        "iconSvg": '<svg class="w-7 h-7 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path stroke-linecap="round" d="M5 9c4.5-1.5 10-1.2 14 1M6.5 13c3.5-1 8-.8 11 .8M8 16.8c2.8-.7 6-.5 8.5.7"/></svg>',
        "plans": [
            {"id": "3m", "labelKm": "3 ខែ (គណនីផ្ទាល់ខ្លួន)", "labelEn": "3 Months (Individual)", "price": 5.50},
            {"id": "1y", "labelKm": "1 ឆ្នាំ (គណនីផ្ទាល់ខ្លួន)", "labelEn": "1 Year (Individual)", "price": 15.00},
        ],
    },
]

WHEEL_SEGMENTS = [
    {"label": "10% OFF", "color": "#2563EB", "type": "coupon", "code": "SPIN10", "discountType": "percent", "value": 10, "desc": "កូដបញ្ចុះតម្លៃ 10% (Code: SPIN10)"},
    {"label": "+50 PTS", "color": "#0D9488", "type": "points", "value": 50, "desc": "ទទួលបាន 50 ពិន្ទុបន្ថែមក្នុងកាបូប!"},
    {"label": "$1.00 OFF", "color": "#D97706", "type": "coupon", "code": "LUCKY1$", "discountType": "fixed", "value": 1.00, "desc": "ប័ណ្ណទឹកប្រាក់ $1.00 (Code: LUCKY1$)"},
    {"label": "+25 PTS", "color": "#4F46E5", "type": "points", "value": 25, "desc": "ទទួលបាន 25 ពិន្ទុបន្ថែមក្នុងកាបូប!"},
    {"label": "20% VIP", "color": "#7C3AED", "type": "coupon", "code": "VIP20", "discountType": "percent", "value": 20, "desc": "កូដបញ្ចុះតម្លៃពិសេស 20% (Code: VIP20)"},
    {"label": "+100 PTS", "color": "#059669", "type": "points", "value": 100, "desc": "អស្ចារ្យ! ទទួលបាន 100 ពិន្ទុ!"},
    {"label": "CAPCUT 7D", "color": "#DB2777", "type": "coupon", "code": "CAPFREE", "discountType": "fixed", "value": 1.50, "desc": "ប័ណ្ណ $1.50 សម្រាប់ CapCut Pro (Code: CAPFREE)"},
    {"label": "+15 PTS", "color": "#334155", "type": "points", "value": 15, "desc": "ទទួលបាន 15 ពិន្ទុលើកទឹកចិត្ត!"},
]

# =========================================================================
# 2. JSON DATA STORE
# =========================================================================
def hash_pin(pin: str) -> str:
    return hashlib.sha256(f"nexus:{pin.strip()}".encode()).hexdigest()


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def now_time_str() -> str:
    return datetime.now().strftime("%H:%M:%S")


_db: Optional[Dict[str, Any]] = None


def load_db() -> Dict[str, Any]:
    global _db
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        _db = {
            "products": json.loads(json.dumps(DEFAULT_PRODUCTS)),
            "orders": [],
            "users": {},
            "settings": {
                "adminPinHash": hash_pin(ADMIN_PIN),
                "adminChatId": ADMIN_CHAT_ID,
            },
            "auditLogs": [
                {
                    "time": now_time_str(),
                    "action": "SYSTEM_INIT",
                    "detail": "Python FastAPI backend initialized with HMAC & PIN protection",
                }
            ],
        }
        save_db()
        return _db
    try:
        _db = json.loads(DB_PATH.read_text(encoding="utf-8"))
        _db.setdefault("products", json.loads(json.dumps(DEFAULT_PRODUCTS)))
        _db.setdefault("orders", [])
        _db.setdefault("users", {})
        _db.setdefault("settings", {"adminPinHash": hash_pin(ADMIN_PIN), "adminChatId": ADMIN_CHAT_ID})
        _db.setdefault("auditLogs", [])
    except Exception:
        _db = None
        DB_PATH.unlink(missing_ok=True)
        return load_db()
    return _db


def save_db() -> None:
    if _db is None:
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DB_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(_db, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(DB_PATH)


def get_db() -> Dict[str, Any]:
    return _db if _db is not None else load_db()


def add_audit_log(action: str, detail: str) -> None:
    store = get_db()
    store["auditLogs"].insert(0, {"time": now_time_str(), "action": action, "detail": detail})
    store["auditLogs"] = store["auditLogs"][:60]
    save_db()


def get_or_create_user(tg_user: Dict[str, Any]) -> Dict[str, Any]:
    store = get_db()
    key = str(tg_user["id"])
    today = today_str()
    if key not in store["users"]:
        store["users"][key] = {
            "id": tg_user["id"],
            "username": tg_user.get("username", ""),
            "firstName": tg_user.get("first_name", "Guest"),
            "lastName": tg_user.get("last_name", ""),
            "points": 120,
            "freeSpins": 1,
            "lastFreeSpinDate": today,
            "streakDays": 0,
            "lastCheckInDate": None,
            "coupons": [
                {"code": "WELCOME10", "label": "10% OFF First Order", "type": "percent", "value": 10}
            ],
            "lastOrderAt": 0,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        save_db()
    else:
        u = store["users"][key]
        if u.get("lastFreeSpinDate") != today:
            u["freeSpins"] = max(u.get("freeSpins", 0), 1)
            u["lastFreeSpinDate"] = today
            save_db()
        if tg_user.get("username") and u.get("username") != tg_user["username"]:
            u["username"] = tg_user["username"]
            save_db()
    return store["users"][key]


# =========================================================================
# 3. TELEGRAM AUTH & ADMIN TOKEN HELPERS
# =========================================================================
def verify_telegram_init_data(init_data: str) -> Optional[Dict[str, Any]]:
    if not init_data or not BOT_TOKEN:
        return None
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", "")
    if not received_hash:
        return None
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc_hash, received_hash):
        return None
    auth_date = int(pairs.get("auth_date", "0") or 0)
    if auth_date > 0 and time.time() - auth_date > 86400:
        return None
    user_raw = pairs.get("user")
    if not user_raw:
        return None
    try:
        return json.loads(user_raw)
    except Exception:
        return None


def resolve_user(init_data: Optional[str]) -> tuple[Dict[str, Any], bool]:
    if init_data and BOT_TOKEN:
        verified = verify_telegram_init_data(init_data)
        if verified:
            return verified, True
        raise HTTPException(status_code=401, detail="Invalid Telegram initData signature")
    if ALLOW_DEV_MODE:
        return {"id": "dev-user", "first_name": "Demo", "last_name": "User", "username": "demo_user"}, False
    raise HTTPException(status_code=401, detail="Telegram WebApp authentication required")


def create_admin_token() -> str:
    payload_bytes = json.dumps({"role": "admin", "exp": int(time.time() * 1000) + 12 * 3600 * 1000}).encode()
    payload = base64.urlsafe_b64encode(payload_bytes).decode().rstrip("=")
    sig = base64.urlsafe_b64encode(
        hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).digest()
    ).decode().rstrip("=")
    return f"{payload}.{sig}"


def verify_admin_token(token: Optional[str]) -> bool:
    if not token or "." not in token:
        return False
    payload, sig = token.split(".", 1)
    expected = base64.urlsafe_b64encode(
        hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).digest()
    ).decode().rstrip("=")
    if not hmac.compare_digest(sig, expected):
        return False
    try:
        padded = payload + "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded).decode())
        return data.get("role") == "admin" and data.get("exp", 0) > int(time.time() * 1000)
    except Exception:
        return False


def require_admin(token: Optional[str]) -> None:
    if not verify_admin_token(token):
        raise HTTPException(status_code=403, detail="Admin authentication required")


def generate_order_hash(order_id: str, contact: str, total_usd: str) -> str:
    raw = f"{order_id}|{contact}|{total_usd}|{SESSION_SECRET}"
    return "SEC-" + hashlib.sha256(raw.encode()).hexdigest()[:8].upper()


# =========================================================================
# 4. TELEGRAM BOT API CLIENT (WEBHOOK + LONG-POLLING)
# =========================================================================
bot_state: Dict[str, Any] = {
    "connected": False,
    "username": None,
    "error": None,
    "mode": "none",
}
_polling_task: Optional[asyncio.Task] = None


def escape_html(text: Any) -> str:
    return str(text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


async def tg_api(method: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not BOT_TOKEN:
        return {"ok": False, "description": "BOT_TOKEN not configured"}
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, json=payload or {})
        return resp.json()


def format_order_html(order: Dict[str, Any]) -> str:
    return (
        f"🛒 <b>ការបញ្ជាទិញថ្មី (NEW ORDER)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 Order ID: <code>{escape_html(order['orderId'])}</code>\n"
        f"👤 អតិថិជន: {escape_html(order['customerContact'])}\n"
        f"💳 ទូទាត់: {escape_html(order['paymentMethod'])}\n"
        f"🔐 Hash: <code>{escape_html(order['securityHash'])}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 មុខទំនិញ៖\n{escape_html(order['itemsSummary'])}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 សរុប: <b>${escape_html(order['totalUsd'])}</b> ({escape_html(order['totalKhr'])} ៛)"
    )


async def handle_telegram_update(update: Dict[str, Any]) -> None:
    msg = update.get("message")
    if not msg:
        return
    chat_id = msg["chat"]["id"]
    user = msg.get("from") or {}
    text = (msg.get("text") or "").strip()

    if "web_app_data" in msg:
        try:
            data = json.loads(msg["web_app_data"]["data"])
            oid = escape_html(data.get("orderId", ""))
            await tg_api("sendMessage", {
                "chat_id": chat_id,
                "text": f"✅ បានទទួលទិន្នន័យបញ្ជាទិញ <code>{oid}</code>!",
                "parse_mode": "HTML",
            })
        except Exception:
            await tg_api("sendMessage", {"chat_id": chat_id, "text": "✅ Received WebApp data."})
        return

    if text.startswith("/start"):
        if user.get("id"):
            get_or_create_user(user)
        name = escape_html(user.get("first_name", "មិត្តភក្តិ"))
        welcome = (
            f"សួស្តី <b>{name}</b>! 👋\n\n"
            f"ស្វាគមន៍មកកាន់ <b>MiniStore KH — Digital Store 24/7</b>\n"
            f"• Gemini Advanced, ChatGPT Plus, Claude Pro\n"
            f"• CapCut Pro, Canva Pro, Netflix 4K, Spotify\n"
            f"• បង្វិលកងសំណាង & សន្សំពិន្ទុប្រចាំថ្ងៃ!\n\n"
            f"<i>Tap the button below to open the Mini App Store.</i>"
        )
        payload: Dict[str, Any] = {"chat_id": chat_id, "text": welcome, "parse_mode": "HTML"}
        if WEBAPP_URL.startswith("https://"):
            payload["reply_markup"] = {
                "inline_keyboard": [
                    [{"text": "🛒 បើកហាង MiniStore KH (Open Store)", "web_app": {"url": WEBAPP_URL}}]
                ]
            }
        await tg_api("sendMessage", payload)
    elif text.startswith("/orders"):
        store = get_db()
        uid = str(user.get("id", ""))
        orders = [o for o in store["orders"] if str(o.get("telegramUserId")) == uid][:5]
        if not orders:
            await tg_api("sendMessage", {"chat_id": chat_id, "text": "📦 អ្នកមិនទាន់មានការបញ្ជាទិញនៅឡើយទេ។"})
        else:
            lines = [
                f"• <b>{escape_html(o['orderId'])}</b> — ${escape_html(o['totalUsd'])} "
                f"[{'✅ DELIVERED' if o['status'] == 'DELIVERED' else '⏳ PENDING'}]"
                for o in orders
            ]
            await tg_api("sendMessage", {
                "chat_id": chat_id,
                "text": "📦 <b>ការបញ្ជាទិញចុងក្រោយរបស់អ្នក៖</b>\n\n" + "\n".join(lines),
                "parse_mode": "HTML",
            })
    elif text.startswith("/help"):
        await tg_api("sendMessage", {
            "chat_id": chat_id,
            "text": (
                f"ℹ️ <b>MiniStore KH Help</b>\n\n"
                f"/start — បើកហាង Mini App (Open Store)\n"
                f"/orders — មើលប្រវត្តិការទិញ (My Orders)\n"
                f"/help — ជំនួយ (Help)\n\n"
                f"🆔 Your Telegram Chat ID: <code>{chat_id}</code>"
            ),
            "parse_mode": "HTML",
        })


async def polling_loop() -> None:
    offset = 0
    await tg_api("deleteWebhook", {"drop_pending_updates": True})
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            async with httpx.AsyncClient(timeout=35.0) as client:
                resp = await client.post(url, json={"offset": offset, "timeout": 25})
                data = resp.json()
            if data.get("ok"):
                for upd in data.get("result", []):
                    offset = upd["update_id"] + 1
                    await handle_telegram_update(upd)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            print(f"[BOT] Polling error: {exc}")
            await asyncio.sleep(3)


async def init_telegram_bot() -> None:
    global _polling_task
    if not BOT_TOKEN:
        bot_state["connected"] = False
        bot_state["error"] = "BOT_TOKEN not configured in .env (running in web-only mode)"
        print(f"[BOT] {bot_state['error']}")
        return

    try:
        me = await tg_api("getMe")
        if not me.get("ok"):
            bot_state["error"] = me.get("description", "Invalid BOT_TOKEN")
            print(f"[BOT] getMe failed: {bot_state['error']}")
            return

        bot_state["connected"] = True
        bot_state["username"] = me["result"]["username"]
        bot_state["error"] = None
        print(f"[BOT] Connected as @{bot_state['username']}")

        if WEBAPP_URL.startswith("https://"):
            await tg_api("setChatMenuButton", {
                "menu_button": {
                    "type": "web_app",
                    "text": "🛒 Open Store",
                    "web_app": {"url": WEBAPP_URL},
                }
            })

        if USE_WEBHOOK and WEBAPP_URL.startswith("https://"):
            webhook_url = f"{WEBAPP_URL}/telegram/webhook"
            res = await tg_api("setWebhook", {"url": webhook_url, "drop_pending_updates": True})
            bot_state["mode"] = "webhook" if res.get("ok") else "webhook_error"
            print(f"[BOT] Webhook registered -> {webhook_url}")
        else:
            bot_state["mode"] = "polling"
            _polling_task = asyncio.create_task(polling_loop())
            print("[BOT] Started long-polling loop")

        add_audit_log("BOT_CONNECTED", f"Python Bot @{bot_state['username']} ({bot_state['mode']})")
    except Exception as exc:
        bot_state["connected"] = False
        bot_state["error"] = str(exc)
        print(f"[BOT] Startup error: {exc}")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    load_db()
    await init_telegram_bot()
    yield
    if _polling_task:
        _polling_task.cancel()


# =========================================================================
# 5. FASTAPI APP & ROUTES
# =========================================================================
app = FastAPI(title="MiniStore KH — Telegram Mini App (Python)", lifespan=lifespan)


def get_bot_status() -> Dict[str, Any]:
    store = get_db()
    return {
        "connected": bot_state["connected"],
        "username": bot_state["username"],
        "mode": bot_state["mode"],
        "webAppUrlConfigured": WEBAPP_URL.startswith("https://"),
        "adminChatConfigured": bool(store["settings"].get("adminChatId") or ADMIN_CHAT_ID),
        "error": bot_state["error"],
    }


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    await handle_telegram_update(update)
    return {"ok": True}


@app.get("/api/health")
async def api_health():
    return {"ok": True, "runtime": "python", "bot": get_bot_status(), "devMode": ALLOW_DEV_MODE}


@app.get("/api/bootstrap")
async def api_bootstrap(x_telegram_init_data: Optional[str] = Header(default=None)):
    tg_user, is_verified = resolve_user(x_telegram_init_data)
    store = get_db()
    user = get_or_create_user(tg_user)
    today = today_str()
    user_orders = [o for o in store["orders"] if str(o.get("telegramUserId")) == str(tg_user["id"])][:50]

    return {
        "isTelegramVerified": is_verified,
        "bot": get_bot_status(),
        "exchangeRate": EXCHANGE_RATE,
        "products": store["products"],
        "user": {
            "id": user["id"],
            "username": user["username"],
            "firstName": user["firstName"],
            "lastName": user["lastName"],
            "points": user["points"],
            "freeSpins": user["freeSpins"],
            "streakDays": user["streakDays"],
            "checkedInToday": user.get("lastCheckInDate") == today,
            "coupons": user["coupons"],
        },
        "orders": user_orders,
    }


@app.post("/api/rewards/checkin")
async def api_checkin(x_telegram_init_data: Optional[str] = Header(default=None)):
    tg_user, _ = resolve_user(x_telegram_init_data)
    user = get_or_create_user(tg_user)
    today = today_str()
    if user.get("lastCheckInDate") == today:
        raise HTTPException(status_code=400, detail="Already checked in today")

    user["lastCheckInDate"] = today
    user["streakDays"] = 1 if user.get("streakDays", 0) >= 7 else user.get("streakDays", 0) + 1
    bonus = 100 if user["streakDays"] == 7 else 30
    user["points"] += bonus
    save_db()
    add_audit_log("DAILY_CHECKIN", f"User {user['id']} claimed +{bonus} PTS (Day {user['streakDays']})")

    return {"bonus": bonus, "points": user["points"], "streakDays": user["streakDays"], "checkedInToday": True}


@app.post("/api/rewards/buy-spin")
async def api_buy_spin(x_telegram_init_data: Optional[str] = Header(default=None)):
    tg_user, _ = resolve_user(x_telegram_init_data)
    user = get_or_create_user(tg_user)
    if user["points"] < 50:
        raise HTTPException(status_code=400, detail="Not enough points (need 50 PTS)")
    user["points"] -= 50
    user["freeSpins"] += 1
    save_db()
    return {"points": user["points"], "freeSpins": user["freeSpins"]}


@app.post("/api/rewards/spin")
async def api_spin(x_telegram_init_data: Optional[str] = Header(default=None)):
    tg_user, _ = resolve_user(x_telegram_init_data)
    user = get_or_create_user(tg_user)

    if user["freeSpins"] > 0:
        user["freeSpins"] -= 1
    elif user["points"] >= 50:
        user["points"] -= 50
    else:
        raise HTTPException(status_code=400, detail="Not enough points or free spins (need 50 PTS)")

    win_index = random.randint(0, len(WHEEL_SEGMENTS) - 1)
    prize = WHEEL_SEGMENTS[win_index]

    if prize["type"] == "points":
        user["points"] += prize["value"]
    elif prize["type"] == "coupon":
        if not any(c["code"] == prize["code"] for c in user["coupons"]):
            user["coupons"].insert(0, {
                "code": prize["code"],
                "label": prize["desc"],
                "type": prize["discountType"],
                "value": prize["value"],
            })
    save_db()
    add_audit_log("LUCKY_SPIN", f"User {user['id']} won '{prize['label']}'")

    return {
        "winIndex": win_index,
        "prize": prize,
        "points": user["points"],
        "freeSpins": user["freeSpins"],
        "coupons": user["coupons"],
    }


@app.post("/api/orders")
async def api_create_order(request: Request, x_telegram_init_data: Optional[str] = Header(default=None)):
    tg_user, _ = resolve_user(x_telegram_init_data)
    store = get_db()
    user = get_or_create_user(tg_user)
    body = await request.json()

    now_ms = int(time.time() * 1000)
    if now_ms - user.get("lastOrderAt", 0) < 3000:
        raise HTTPException(status_code=429, detail="Please wait 3 seconds before placing another order (Anti-Spam)")

    contact = str(body.get("customerContact") or "").strip()
    items = body.get("items") or []
    payment_method = str(body.get("paymentMethod") or "ABA / Bakong KHQR")
    coupon_code = body.get("couponCode")

    if not contact:
        raise HTTPException(status_code=400, detail="Customer contact (@username or email) is required")
    if not isinstance(items, list) or not items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    subtotal = 0.0
    resolved_items: List[Dict[str, Any]] = []
    for req_item in items:
        prod = next((p for p in store["products"] if p["id"] == req_item.get("productId")), None)
        if not prod or prod.get("inStock") is False:
            raise HTTPException(status_code=400, detail=f"Product unavailable: {req_item.get('productId')}")
        plan = next((pl for pl in prod["plans"] if pl["id"] == req_item.get("planId")), None)
        if not plan:
            raise HTTPException(status_code=400, detail=f"Invalid plan: {req_item.get('planId')}")
        qty = max(1, min(20, int(req_item.get("qty") or 1)))
        subtotal += float(plan["price"]) * qty
        resolved_items.append({
            "productId": prod["id"],
            "productName": prod["name"],
            "planId": plan["id"],
            "planLabelEn": plan["labelEn"],
            "planLabelKm": plan["labelKm"],
            "price": float(plan["price"]),
            "qty": qty,
        })

    discount = 0.0
    applied_code = None
    if coupon_code:
        code_upper = str(coupon_code).strip().upper()
        coupon = next((c for c in user["coupons"] if c["code"] == code_upper), None)
        if coupon:
            applied_code = coupon["code"]
            if coupon["type"] == "percent":
                discount = subtotal * (float(coupon["value"]) / 100.0)
            else:
                discount = min(subtotal, float(coupon["value"]))

    total = max(0.0, subtotal - discount)
    total_usd = f"{total:.2f}"
    total_khr = f"{round(total * EXCHANGE_RATE):,}"
    order_id = f"ORD-{random.randint(100000, 999999)}"
    sec_hash = generate_order_hash(order_id, contact, total_usd)
    items_summary = "\n".join(
        f"{i + 1}. {it['productName']} ({it['planLabelEn']}) x{it['qty']} = ${it['price'] * it['qty']:.2f}"
        for i, it in enumerate(resolved_items)
    )

    order_record = {
        "orderId": order_id,
        "telegramUserId": tg_user["id"],
        "telegramUsername": tg_user.get("username", ""),
        "timestamp": datetime.now().strftime("%d/%m/%Y, %I:%M:%S %p"),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "customerContact": contact,
        "paymentMethod": payment_method,
        "couponCode": applied_code,
        "subtotalUsd": f"{subtotal:.2f}",
        "discountUsd": f"{discount:.2f}",
        "totalUsd": total_usd,
        "totalKhr": total_khr,
        "items": resolved_items,
        "itemsSummary": items_summary,
        "status": "PENDING",
        "credentials": "",
        "securityHash": sec_hash,
    }

    user["lastOrderAt"] = now_ms
    user["points"] += 20
    store["orders"].insert(0, order_record)
    save_db()
    add_audit_log("ORDER_CREATED", f"Order {order_id} (${total_usd}) verified [{sec_hash}]")

    admin_notified = False
    user_notified = False
    admin_chat = store["settings"].get("adminChatId") or ADMIN_CHAT_ID
    if BOT_TOKEN and admin_chat:
        res = await tg_api("sendMessage", {
            "chat_id": admin_chat,
            "text": format_order_html(order_record),
            "parse_mode": "HTML",
        })
        admin_notified = bool(res.get("ok"))

    if BOT_TOKEN and str(tg_user["id"]) != "dev-user":
        res = await tg_api("sendMessage", {
            "chat_id": tg_user["id"],
            "text": (
                f"✅ <b>ការបញ្ជាទិញ {escape_html(order_id)} ត្រូវបានទទួល!</b>\n"
                f"💰 សរុប: <b>${escape_html(total_usd)}</b> ({escape_html(total_khr)} ៛)\n"
                f"⏳ Admin កំពុងពិនិត្យ និងបញ្ជូនគណនីជូនអ្នកឆាប់ៗនេះ។"
            ),
            "parse_mode": "HTML",
        })
        user_notified = bool(res.get("ok"))

    return JSONResponse(
        status_code=201,
        content={
            "order": order_record,
            "points": user["points"],
            "adminNotified": admin_notified,
            "userNotified": user_notified,
        },
    )


# =========================================================================
# 6. ADMIN ENDPOINTS
# =========================================================================
@app.post("/api/admin/login")
async def api_admin_login(request: Request):
    body = await request.json()
    pin = str(body.get("pin") or "").strip()
    store = get_db()
    if store["settings"].get("adminPinHash") != hash_pin(pin):
        add_audit_log("ADMIN_LOGIN_FAILED", "Invalid PIN attempt blocked")
        raise HTTPException(status_code=401, detail="Invalid Admin PIN")
    add_audit_log("ADMIN_LOGIN_SUCCESS", "Admin authenticated via Security PIN")
    return {"token": create_admin_token()}


@app.get("/api/admin/dashboard")
async def api_admin_dashboard(x_admin_token: Optional[str] = Header(default=None)):
    require_admin(x_admin_token)
    store = get_db()
    total_rev = sum(float(o.get("totalUsd", 0)) for o in store["orders"])
    pending = sum(1 for o in store["orders"] if o.get("status") != "DELIVERED")
    return {
        "kpis": {
            "totalRevenue": f"{total_rev:.2f}",
            "totalOrders": len(store["orders"]),
            "pendingOrders": pending,
            "productsCount": len(store["products"]),
        },
        "orders": store["orders"],
        "products": store["products"],
        "auditLogs": store["auditLogs"],
        "bot": get_bot_status(),
        "adminChatId": store["settings"].get("adminChatId", ""),
    }


@app.post("/api/admin/orders/{order_id}/fulfill")
async def api_admin_fulfill(order_id: str, request: Request, x_admin_token: Optional[str] = Header(default=None)):
    require_admin(x_admin_token)
    store = get_db()
    order = next((o for o in store["orders"] if o["orderId"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    body = await request.json()
    creds = str(body.get("credentials") or "").strip()
    if not creds:
        raise HTTPException(status_code=400, detail="Credentials are required")

    order["credentials"] = creds
    order["status"] = "DELIVERED"
    order["deliveredAt"] = datetime.now(timezone.utc).isoformat()
    save_db()
    add_audit_log("ORDER_FULFILLED", f"Admin delivered credentials for {order_id}")

    user_notified = False
    if BOT_TOKEN and str(order.get("telegramUserId")) != "dev-user":
        res = await tg_api("sendMessage", {
            "chat_id": order["telegramUserId"],
            "text": (
                f"🚀 <b>គណនីសម្រាប់ {escape_html(order_id)} រួចរាល់ហើយ!</b>\n\n"
                f"🔐 <b>Credentials / Invite Link:</b>\n<code>{escape_html(creds)}</code>\n\n"
                f"សូមអរគុណដែលបានគាំទ្រ MiniStore KH!"
            ),
            "parse_mode": "HTML",
        })
        user_notified = bool(res.get("ok"))

    return {"order": order, "userNotified": user_notified}


@app.post("/api/admin/products")
async def api_admin_add_product(request: Request, x_admin_token: Optional[str] = Header(default=None)):
    require_admin(x_admin_token)
    store = get_db()
    body = await request.json()
    name = str(body.get("name") or "").strip()
    category = body.get("category") if body.get("category") in ("ai", "creative", "entertainment") else "ai"
    try:
        price = float(body.get("price"))
    except Exception:
        price = 0.0
    if not name or price <= 0:
        raise HTTPException(status_code=400, detail="Valid product name and price are required")

    new_prod = {
        "id": f"prod-{int(time.time() * 1000)}",
        "name": name,
        "category": category,
        "badge": "NEW",
        "inStock": True,
        "badgeClass": "bg-indigo-500/15 text-indigo-300 border-indigo-500/30",
        "accent": "from-indigo-500 to-purple-600",
        "descKm": "គណនី Premium ធានាគុណភាព 100% ប្រើប្រាស់បានភ្លាមៗ។",
        "descEn": "100% Genuine Premium Subscription with instant delivery.",
        "iconSvg": '<svg class="w-7 h-7 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
        "plans": [{"id": "1m", "labelKm": "1 ខែ (Standard)", "labelEn": "1 Month (Standard)", "price": price}],
    }
    store["products"].insert(0, new_prod)
    save_db()
    add_audit_log("PRODUCT_ADDED", f"Added product '{name}' at ${price:.2f}")
    return JSONResponse(status_code=201, content={"product": new_prod, "products": store["products"]})


@app.patch("/api/admin/products/{product_id}/stock")
async def api_admin_toggle_stock(product_id: str, x_admin_token: Optional[str] = Header(default=None)):
    require_admin(x_admin_token)
    store = get_db()
    prod = next((p for p in store["products"] if p["id"] == product_id), None)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    prod["inStock"] = not (prod.get("inStock", True))
    save_db()
    add_audit_log("STOCK_UPDATED", f"Toggled stock for {prod['name']}")
    return {"product": prod, "products": store["products"]}


@app.post("/api/admin/pin")
async def api_admin_pin(request: Request, x_admin_token: Optional[str] = Header(default=None)):
    require_admin(x_admin_token)
    body = await request.json()
    new_pin = str(body.get("newPin") or "").strip()
    if len(new_pin) < 4 or len(new_pin) > 6:
        raise HTTPException(status_code=400, detail="PIN must be 4-6 digits")
    store = get_db()
    store["settings"]["adminPinHash"] = hash_pin(new_pin)
    save_db()
    add_audit_log("PIN_CHANGED", "Admin updated security PIN")
    return {"ok": True}


@app.post("/api/admin/bot-config")
async def api_admin_bot_config(request: Request, x_admin_token: Optional[str] = Header(default=None)):
    require_admin(x_admin_token)
    body = await request.json()
    chat_id = str(body.get("adminChatId") or "").strip()
    store = get_db()
    store["settings"]["adminChatId"] = chat_id
    save_db()
    add_audit_log("BOT_CONFIG_SAVED", f"Admin Chat ID updated to {chat_id or '(cleared)'}")
    return {"ok": True, "adminChatId": chat_id}


@app.post("/api/admin/test-telegram")
async def api_admin_test_telegram(request: Request, x_admin_token: Optional[str] = Header(default=None)):
    require_admin(x_admin_token)
    if not BOT_TOKEN:
        raise HTTPException(status_code=400, detail="BOT_TOKEN not configured in .env")
    body = await request.json()
    store = get_db()
    target = str(body.get("adminChatId") or store["settings"].get("adminChatId") or ADMIN_CHAT_ID).strip()
    if not target:
        raise HTTPException(status_code=400, detail="Admin Chat ID is required")
    res = await tg_api("sendMessage", {
        "chat_id": target,
        "text": "✅ <b>MiniStore KH (Python 24/7) តភ្ជាប់ជោគជ័យ!</b>",
        "parse_mode": "HTML",
    })
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail=res.get("description", "Telegram API error"))
    return {"ok": True}


# Serve Mini App Frontend
@app.get("/")
async def index():
    return FileResponse(PUBLIC_DIR / "index.html")


app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="public")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=False)
