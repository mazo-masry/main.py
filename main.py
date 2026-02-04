import os
import random
import socket
import logging
import asyncio
import requests
import re
import whois
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===== Logging =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== Settings =====
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780
ALLOWED_USERS = {ADMIN_ID}

GLOBAL_ACTIVE = False
checked_cache = set()

# ===== Brand Data =====
BRAND_DATA = {
    "مصانع": ["mfg", "fab", "ind", "works", "tech", "forge"],
    "مطاعم": ["tasty", "bite", "chef", "grill", "kitchen"],
    "ملابس": ["wear", "style", "fit", "vogue", "apparel"],
    "تعبئة": ["pack", "wrap", "box", "seal"],
    "شحن": ["ship", "cargo", "logix", "move"],
    "توصيل": ["dash", "drop", "swift", "go"],
    "مستشفيات": ["med", "care", "health", "clinic"],
    "AI": ["ai", "bot", "neural", "data", "smart"],
    "استهداف الخليج": ["dubai", "ksa", "uae", "gulf", "emirates"]
}

EXTENSIONS = [".com", ".net", ".io", ".ai", ".ae", ".sa"]

# ===== WHOIS Check =====
async def is_available(domain):
    try:
        loop = asyncio.get_event_loop()
        w = await loop.run_in_executor(None, whois.whois, domain)
        return not w.domain_name
    except:
        return True

# ===== Global Hunter (ADMIN ONLY) =====
async def global_hunter(context):
    global GLOBAL_ACTIVE
    sources = [
        "https://mirror.cedia.org.ec/malwaredomains/justdomains"
    ]

    while GLOBAL_ACTIVE:
        for src in sources:
            if not GLOBAL_ACTIVE:
                break
            try:
                r = requests.get(src, timeout=15)
                domains = re.findall(r"[a-z0-9\-]+\.(com|net|org|io)", r.text.lower())
                random.shuffle(domains)

                for d in domains[:30]:
                    if not GLOBAL_ACTIVE or d in checked_cache:
                        continue

                    checked_cache.add(d)
                    if await is_available(d):
                        await context.bot.send_message(
                            chat_id=ADMIN_ID,
                            text=f"🌍 Global Hit:\n`{d}`",
                            parse_mode="Markdown"
                        )
                    await asyncio.sleep(0.2)
            except Exception as e:
                logger.error(e)

        await asyncio.sleep(10)

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ALLOWED_USERS:
        return

    kb = [
        ["🚀 Global", "🤖 AI", "🇦🇪 استهداف الخليج 🇸🇦"],
        ["🏢 مصانع", "🍴 مطاعم", "👕 ملابس"],
        ["📦 تعبئة", "🚚 شحن", "🛵 توصيل"],
        ["🏥 مستشفيات", "➕ إضافة", "➖ حذف"]
    ]

    await update.message.reply_text(
        "🚀 بوت القنص الذكي جاهز",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

# ===== Main Handler =====
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GLOBAL_ACTIVE
    uid = update.effective_user.id
    text = update.message.text.strip()

    if uid not in ALLOWED_USERS:
        return

    # ===== ADMIN ONLY =====
    if text == "🚀 Global":
        if uid != ADMIN_ID:
            return

        GLOBAL_ACTIVE = not GLOBAL_ACTIVE
        if GLOBAL_ACTIVE:
            asyncio.create_task(global_hunter(context))
            await update.message.reply_text("📡 Global Hunter ON")
        else:
            await update.message.reply_text("🛑 Global Hunter OFF")
        return

    if text == "➕ إضافة" and uid == ADMIN_ID:
        context.user_data["mode"] = "ADD"
        await update.message.reply_text("📥 ابعت ID المستخدم")
        return

    if text == "➖ حذف" and uid == ADMIN_ID:
        context.user_data["mode"] = "DEL"
        await update.message.reply_text("📤 ابعت ID المستخدم")
        return

    if context.user_data.get("mode") in ["ADD", "DEL"]:
        try:
            tid = int(text)
            if context.user_data["mode"] == "ADD":
                ALLOWED_USERS.add(tid)
            else:
                ALLOWED_USERS.discard(tid)
            await update.message.reply_text("✅ تم التنفيذ")
        except:
            await update.message.reply_text("❌ ID غلط")
        context.user_data["mode"] = None
        return

    # ===== Brand Buttons =====
    for key in BRAND_DATA:
        if key in text:
            msg = f"🎯 نتائج {key}:\n\n"
            for _ in range(8):
                name = random.choice(BRAND_DATA[key])
                ext = random.choice(EXTENSIONS)
                domain = f"{name}{random.randint(10,99)}{ext}"

                try:
                    socket.gethostbyname(domain)
                    status = "❌ محجوز"
                except:
                    status = "✅ متاح"

                msg += f"`{domain}` | {status}\n"

            await update.message.reply_text(msg, parse_mode="Markdown")
            return

# ===== Run =====
if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    print("🚀 BOT RUNNING")
    app.run_polling()
