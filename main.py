import os
import random
import asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
GD_KEY = os.getenv("GODADDY_KEY")
GD_SECRET = os.getenv("GODADDY_SECRET")

WORDS = [
    "alpha","nova","zen","byte","cloud","prime",
    "spark","orbit","pixel","logic","swift","core"
]

HEADERS = {
    "Authorization": f"sso-key {GD_KEY}:{GD_SECRET}",
    "Accept": "application/json"
}

def generate_domain():
    name = random.choice(WORDS) + random.choice(WORDS)
    return name[:6].lower() + ".com"

def check_godaddy(domain):
    url = "https://api.godaddy.com/v1/domains/available"
    params = {"domain": domain}
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    return r.json().get("available", False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Domain Hunter جاهز\n"
        "اكتب /check لبدء فحص 100 دومين"
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    msg = await context.bot.send_message(
        chat_id,
        "🔍 بدء الفحص...\n"
        "⏳ برجاء الانتظار"
    )

    log = []
    for i in range(1, 101):
        domain = generate_domain()
        try:
            available = check_godaddy(domain)
            status = "✅ AVAILABLE" if available else "❌ TAKEN"
        except Exception as e:
            status = "⚠️ ERROR"

        line = f"{i:03d}. {domain} → {status}"
        print(line)
        log.append(line)

        # تحديث نفس الرسالة (أهم جزء)
        await msg.edit_text(
            "🔍 فحص دومينات من GoDaddy\n\n" +
            "\n".join(log[-10:]) +
            f"\n\n⏱️ {i}/100"
        )

        await asyncio.sleep(1)  # ثانية بين كل فحص

    await context.bot.send_message(chat_id, "✅ انتهى الفحص بالكامل")

def main():
    print("🤖 BOT STARTING...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))
    app.run_polling()

if __name__ == "__main__":
    main()
