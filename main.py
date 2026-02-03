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
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== Config =====
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780
ALLOWED_USERS = {ADMIN_ID}
GLOBAL_ACTIVE = False
checked_cache = set()

BRAND_DATA = {
    "مصانع": ["Mfg", "Fab", "Ind", "Works", "Tech", "Line", "Forge", "Mill"],
    "مطاعم": ["Tasty", "Bite", "Chef", "Dish", "Eats", "Grill", "Foody", "Kitchen"],
    "ملابس": ["Wear", "Style", "Fit", "Vogue", "Thread", "Apparel", "Fabric"],
    "تعبئة": ["Pack", "Wrap", "Box", "Fill", "Seal", "Flow", "Case"],
    "شحن": ["Ship", "Logix", "Cargo", "Move", "Fast", "Route", "Post"],
    "توصيل": ["Dash", "Drop", "Swift", "Zoom", "Go", "Fetch", "Way"],
    "مستشفيات": ["Med", "Care", "Health", "Cure", "Clinic", "Life", "Heal"],
    "AI": ["AI", "Bot", "Neural", "Mind", "Logic", "Data", "Smart", "IQ"],
    "استهداف الخليج": ["Dubai", "DXB", "AD", "Riyadh", "KSA", "UAE", "Gulf", "Najd"]
}

EXTENSIONS = [".com", ".net", ".ai", ".io", ".live", ".store", ".tech", ".app", ".ae", ".sa"]

# ===== WHOIS CHECK =====
async def is_available_whois(domain):
    try:
        loop = asyncio.get_running_loop()
        w = await loop.run_in_executor(None, whois.whois, domain)
        return not w.domain_name
    except:
        return True

# ===== GLOBAL HUNTER =====
async def global_hunter_task(context: ContextTypes.DEFAULT_TYPE):
    global GLOBAL_ACTIVE, checked_cache

    SOURCES = [
        "https://raw.githubusercontent.com/notracking/hosts-blocklists/master/domains.txt",
        "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
        "https://mirror.cedia.org.ec/malwaredomains/justdomains"
    ]

    loop = asyncio.get_running_loop()

    while GLOBAL_ACTIVE:
        for url in SOURCES:
            if not GLOBAL_ACTIVE:
                break
            try:
                fetch_url = f"{url}?t={time.time()}"
                r = await loop.run_in_executor(
                    None,
                    lambda: requests.get(fetch_url, timeout=20)
                )

                found = re.findall(
                    r'\b[a-z0-9.-]+\.(?:com|net|org|io|biz|info)\b',
                    r.text.lower()
                )

                for domain in set(found):
                    if domain in checked_cache:
                        continue

                    checked_cache.add(domain)

                    try:
                        await loop.run_in_executor(
                            None,
                            lambda: requests.get(f"http://{domain}", timeout=1.5)
                        )
                    except:
                        if await is_available_whois(domain):
                            await context.bot.send_message(
                                chat_id=ADMIN_ID,
                                text=f"🌍 صيد عالمي جديد:\n`{domain}`",
                                parse_mode="Markdown"
                            )

                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(e)

        await asyncio.sleep(10)

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        return

    kb = [
        ["🚀 Global", "🤖 AI", "🇦🇪 استهداف الخليج 🇸🇦"],
        ["🏢 مصانع", "🍴 مطاعم", "👕 ملابس"],
        ["📦 تعبئة", "🚚 شحن", "🛵 توصيل"],
        ["🏥 مستشفيات", "➕ إضافة", "➖ حذف"]
    ]

    await update.message.reply_text(
        "🚀 بوت القنص العالمي المطور 2026",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

# ===== HANDLER =====
async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GLOBAL_ACTIVE

    if update.effective_user.id not in ALLOWED_USERS:
        return

    text = update.message.text

    if text == "🚀 Global":
        GLOBAL_ACTIVE = not GLOBAL_ACTIVE
        if GLOBAL_ACTIVE:
            asyncio.create_task(global_hunter_task(context))
            await update.message.reply_text("📡 الرادار العالمي اشتغل")
        else:
            await update.message.reply_text("🛑 الرادار وقف")
        return

# ===== MAIN =====
if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    print("🚀 BOT IS LIVE")
    app.run_polling()
