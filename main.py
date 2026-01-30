import os
import random
import socket
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

WORDS = [
    "alpha", "nova", "pixel", "logic", "cloud",
    "boost", "spark", "trend", "prime", "swift"
]

def generate_domain():
    word = random.choice(WORDS)
    length = random.choice([5, 6])
    return word[:length] + ".com"

def check_domain(domain):
    try:
        socket.gethostbyname(domain)
        return "❌ TAKEN"
    except:
        return "✅ AVAILABLE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, "🚀 بدأ توليد وفحص 1000 دومين")

    sent = []
    for i in range(1, 1001):
        domain = generate_domain()
        status = check_domain(domain)
        msg = f"{i}. {domain} → {status}"
        print(msg)
        sent.append(msg)

        if i % 10 == 0:
            await context.bot.send_message(chat_id, "\n".join(sent))
            sent.clear()
            await asyncio.sleep(1)

    await context.bot.send_message(chat_id, "✅ انتهى الفحص")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("🤖 BOT STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()
