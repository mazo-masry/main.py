import os
import random
import asyncio
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ========= CONFIG =========
BOT_TOKEN = os.getenv("8166138523:AAGTRyw29i8lvojIsyrCU3tVGWMRAteblkU")

NC_API_USER = os.getenv("NC_API_USER")
NC_API_KEY = os.getenv("NC_API_KEY")
NC_USERNAME = os.getenv("NC_USERNAME")
NC_CLIENT_IP = os.getenv("NC_CLIENT_IP")

DOMAINS_PER_RUN = 1000
DELAY = 0.4
TLDS = ["com"]

BASE_WORDS = [
    "brand","smart","cloud","quick","media","prime","trust","pixel","fresh",
    "logic","spark","boost","trend","scope","alpha","delta","nexus","vivid",
    "eagle","tiger","urban","solid","clean","sharp","magic","happy","super"
]

# ========= DOMAIN CHECK =========
def check_namecheap(domain):
    url = "https://api.namecheap.com/xml.response"
    params = {
        "ApiUser": NC_API_USER,
        "ApiKey": NC_API_KEY,
        "UserName": NC_USERNAME,
        "ClientIp": NC_CLIENT_IP,
        "Command": "namecheap.domains.check",
        "DomainList": domain
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        return 'Available="true"' in r.text
    except:
        return False

# ========= BOT =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 بدء الفحص...")

    words = list(set(w for w in BASE_WORDS if 5 <= len(w) <= 6))
    random.shuffle(words)

    checked = 0
    available = []

    for word in words:
        domain = f"{word}.com"
        checked += 1

        is_free = check_namecheap(domain)

        await update.message.reply_text(
            f"🔎 [{checked}/{DOMAINS_PER_RUN}] {domain} → {'✅ AVAILABLE' if is_free else '❌ TAKEN'}"
        )

        if is_free:
            available.append(domain)

        await asyncio.sleep(DELAY)

        if checked >= DOMAINS_PER_RUN:
            break

    if available:
        await update.message.reply_text(
            "🎯 المتاح:\n\n" + "\n".join(available)
        )
    else:
        await update.message.reply_text("😕 مفيش دومينات متاحة")

# ========= RUN =========
if __name__ == "__main__":
    print("BOT STARTING...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling() os
import time
import random
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ========= CONFIG =========
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8166138523:AAGTRyw29i8lvojIsyrCU3tVGWMRAteblkU"

# Namecheap API
NC_API_USER = os.getenv("NC_API_USER") or "YOUR_NAMECHEAP_USER"
NC_API_KEY  = os.getenv("NC_API_KEY") or "YOUR_NAMECHEAP_API_KEY"
NC_USERNAME = os.getenv("NC_USERNAME") or "YOUR_NAMECHEAP_USERNAME"
NC_CLIENT_IP = os.getenv("NC_CLIENT_IP") or "YOUR_SERVER_IP"  # مهم جدًا

DOMAINS_PER_RUN = 1000
DELAY_BETWEEN_CHECKS = 0.35  # لا سريع ولا بطيء
TLDS = ["com"]  # نقدر نزود بعدين

# ========= WORD SOURCE (مفهومة) =========
BASE_WORDS = [
    "brand","smart","cloud","quick","media","prime","trust","pixel","fresh",
    "logic","spark","boost","trend","scope","alpha","delta","nexus","vivid",
    "eagle","tiger","urban","solid","clean","sharp","magic","happy","super"
]

def generate_words():
    words = set()
    while len(words) < DOMAINS_PER_RUN:
        w = random.choice(BASE_WORDS)
        if 5 <= len(w) <= 6:
            words.add(w)
    return list(words)

# ========= NAMECHEAP CHECK =========
def check_namecheap(domain):
    url = "https://api.namecheap.com/xml.response"
    params = {
        "ApiUser": NC_API_USER,
        "ApiKey": NC_API_KEY,
        "UserName": NC_USERNAME,
        "ClientIp": NC_CLIENT_IP,
        "Command": "namecheap.domains.check",
        "DomainList": domain
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        return 'Available="true"' in r.text
    except Exception:
        return False

# ========= TELEGRAM =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("🚀 بدء توليد وفحص الدومينات...\n⏳ شوية صبر")

    words = generate_words()
    checked = 0
    available = []

    for word in words:
        for tld in TLDS:
            domain = f"{word}.{tld}"
            checked += 1

            is_free = check_namecheap(domain)

            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🔎 [{checked}/{DOMAINS_PER_RUN}] {domain} → {'✅ AVAILABLE' if is_free else '❌ TAKEN'}"
            )

            if is_free:
                available.append(domain)

            time.sleep(DELAY_BETWEEN_CHECKS)

            if checked >= DOMAINS_PER_RUN:
                break
        if checked >= DOMAINS_PER_RUN:
            break

    if available:
        msg = "🎯 الدومينات المتاحة:\n\n" + "\n".join(available)
    else:
        msg = "😕 مفيش دومينات متاحة في الجولة دي"

    await context.bot.send_message(chat_id=chat_id, text=msg)

# ========= RUN =========
if __name__ == "__main__":
    print("BOT STARTING...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
