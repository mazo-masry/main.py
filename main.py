import os
import random
import socket
import logging
import asyncio
import requests
import re
import whois
import time
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================== Flask (موقع وهمي لـ Koyeb) ==================
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is running"

# ================== إعداد السجلات ==================
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ================== الإعدادات الأساسية ==================
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
    "استهداف الخليج": ["Dubai", "DXB", "AD", "Riyadh", "KSA", "UAE", "Gulf", "Najd", "Emirates", "Elite", "Capital", "Sky", "Desert", "Pearl"]
}

EXTENSIONS = [".com", ".net", ".ai", ".io", ".live", ".store", ".tech", ".app", ".ae", ".sa"]

# ================== فحص WHOIS ==================
async def is_available_whois(domain):
    try:
        loop = asyncio.get_event_loop()
        w = await loop.run_in_executor(None, whois.whois, domain)
        if not w.domain_name or (not w.expiration_date and not w.creation_date):
            return True
        return False
    except:
        return True

# ================== Global Hunter ==================
async def global_hunter_task(context: ContextTypes.DEFAULT_TYPE):
    global GLOBAL_ACTIVE, checked_cache

    SOURCES = [
        "https://raw.githubusercontent.com/notracking/hosts-blocklists/master/domains.txt",
        "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
        "https://mirror.cedia.org.ec/malwaredomains/justdomains"
    ]

    while GLOBAL_ACTIVE:
        for url in SOURCES:
            if not GLOBAL_ACTIVE:
                break
            try:
                fetch_url = f"{url}?t={time.time()}"
                loop = asyncio.get_event_loop()
                headers = {'User-Agent': f'Mozilla/5.0 {random.randint(1,99)}'}
                r = await loop.run_in_executor(
                    None, lambda: requests.get(fetch_url, headers=headers, timeout=20)
                )

                found = re.findall(
                    r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:com|net|org|info|biz|io|co|me)\b',
                    r.text.lower()
                )

                new_domains = [d for d in set(found) if d not in checked_cache]
                random.shuffle(new_domains)

                for domain in new_domains[:50]:
                    if not GLOBAL_ACTIVE:
                        break

                    checked_cache.add(domain)

                    if any(x in domain for x in ['google', 'facebook', 'apple', 'akamai', 'github', 'microsoft']):
                        continue

                    try:
                        await loop.run_in_executor(None, lambda: requests.get(f"http://{domain}", timeout=1.5))
                    except:
                        if await is_available_whois(domain):
                            await context.bot.send_message(
                                chat_id=ADMIN_ID,
                                text=f"🌍 **صيد عالمي جديد!**\n\n🔗 `{domain}`\n📊 Total: {len(checked_cache)}",
                                parse_mode='Markdown'
                            )

                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Global Source Error: {e}")

        await asyncio.sleep(10)

# ================== أوامر البوت ==================
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
        "🚀 **بوت القنص العالمي المطور 2026**",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GLOBAL_ACTIVE
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in ALLOWED_USERS:
        return

    if text == "🚀 Global":
        if not GLOBAL_ACTIVE:
            GLOBAL_ACTIVE = True
            asyncio.create_task(global_hunter_task(context))
            await update.message.reply_text("📡 تم تشغيل الرادار العالمي")
        else:
            GLOBAL_ACTIVE = False
            await update.message.reply_text(f"🛑 تم الإيقاف | Total: {len(checked_cache)}")
        return

# ================== تشغيل البوت ==================
def run_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    application.run_polling()

# ================== MAIN ==================
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    web.run(host="0.0.0.0", port=8000)
