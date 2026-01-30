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
    return (random.choice(WORDS) + random.choice(WORDS))[:10].lower() + ".com"

def check_godaddy(domain):
    url = "https://api.godaddy.com/v1/domains/available"
    params = {"domain": domain}
    r = requests.get(url, headers=HEADERS, params=params, timeout=10)
    return r.status_code, r.text

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, "🚀 بدء الفحص (100 دومين)\n⏱ ثانية بين كل دومين")

    for i in range(1, 101):
        domain = generate_domain()

        try:
            status_code, response = await asyncio.to_thread(check_godaddy, domain)

            if status_code == 200:
                data = eval(response)
                available = data.get("available", False)
                msg = "✅ AVAILABLE" if available else "❌ TAKEN"
            else:
                msg = f"⚠️ API ERROR ({status_code})"

        except Exception as e:
            msg = f"🔥 EXCEPTION: {str(e)}"

        text = f"""
🔎 فحص #{i}
🌐 {domain}
📡 النتيجة: {msg}
        """

        print(text)
        await context.bot.send_message(chat_id, text)

        await asyncio.sleep(1)

    await context.bot.send_message(chat_id, "✅ انتهى الفحص بالكامل")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("check", check))
    print("🤖 BOT IS RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
