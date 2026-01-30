import os
import random
import socket
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

WORDS = [
    "alpha", "nova", "pixel", "logic", "cloud",
    "boost", "spark", "trend", "prime", "swift"
]

def gen_domain():
    w = random.choice(WORDS)
    return f"{w[:6]}.com"

def check(domain):
    try:
        socket.gethostbyname(domain)
        return "TAKEN"
    except:
        return "AVAILABLE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, "🚀 بدأ فحص 1000 دومين")

    batch = []
    for i in range(1, 1001):
        d = gen_domain()
        s = check(d)
        line = f"{i}. {d} → {s}"
        print(line)
        batch.append(line)

        if i % 10 == 0:
            await context.bot.send_message(chat_id, "\n".join(batch))
            batch.clear()
            await asyncio.sleep(1)  # ✅ الحل هنا

    await context.bot.send_message(chat_id, "✅ انتهى الفحص")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
