import os
import time
import random
import requests
import asyncio
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
    return name[:10].lower() + ".com"

def check_godaddy(domain):
    url = f"https://api.godaddy.com/v1/domains/available?domain={domain}"
    r = requests.get(url, headers=HEADERS, timeout=10)
    data = r.json()
    return data.get("available", False)

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, "🔍 بدء فحص 100 دومين من GoDaddy")

    results = []

    for i in range(1, 101):
        domain = generate_domain()
        try:
            available = check_godaddy(domain)
            status = "✅ AVAILABLE" if available else "❌ TAKEN"
        except Exception as e:
            status = f"⚠️ ERROR"

        line = f"{i}. {domain} → {status}"
        print(line)
        results.append(line)

        if i % 10 == 0:
            await context.bot.send_message(chat_id, "\n".join(results))
            results.clear()

        await asyncio.sleep(1)  # ثانية بين كل دومين

    await context.bot.send_message(chat_id, "✅ انتهى الفحص")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("check", check))
    print("🤖 BOT IS RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
