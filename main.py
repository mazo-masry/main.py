import asyncio
import random
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

BOT_TOKEN = os.getenv("8166138523:AAGTRyw29i8lvojIsyrCU3tVGWMRAteblkU")
GD_KEY = os.getenv("e4hKswXmobhm_RBV2EMdJJabknhTzWgc9w7")
GD_SECRET = os.getenv("QZeRQUp2RVL2RmSHL2iodi")

HEADERS = {
    "Authorization": f"sso-key {GD_KEY}:{GD_SECRET}",
    "Accept": "application/json"
}

WORDS = [
    "brand","trust","money","power","prime","smart","logic",
    "alpha","pixel","boost","value","spark","solid","quick",
    "sharp","light","scope","vivid","frame","cloud"
]

TLD = "com"
USED = set()

# ---------------------------
def generate_domain():
    while True:
        word = random.choice(WORDS)
        if 5 <= len(word) <= 6:
            domain = f"{word}.{TLD}"
            if domain not in USED:
                USED.add(domain)
                return domain

# ---------------------------
def check_godaddy(domain):
    url = f"https://api.godaddy.com/v1/domains/available?domain={domain}"
    r = requests.get(url, headers=HEADERS, timeout=8)
    if r.status_code == 200:
        return r.json().get("available", False)
    return False

# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🐉 Domain Hunter BOT\n\n"
        "🚀 بدء توليد + فحص 1000 دومين\n"
        "🔍 المصدر: GoDaddy\n"
    )

    found = 0

    for i in range(1000):
        domain = generate_domain()

        await update.message.reply_text(
            f"🔍 [{i+1}/1000] Checking: {domain}"
        )

        if check_godaddy(domain):
            found += 1
            await update.message.reply_text(
                f"✅ AVAILABLE: {domain}"
            )

        await asyncio.sleep(0.5)  # سرعة متوازنة

    await update.message.reply_text(
        f"🎯 انتهى الفحص\n"
        f"✅ المتاح: {found}\n"
        f"🔢 المفحوص: 1000"
    )

# ---------------------------
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))

print("🤖 Bot is running...")
app.run_polling()
