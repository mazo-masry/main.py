import os
import random
import time
import socket
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

WORDS = [
    "cloud", "pixel", "nova", "logic", "alpha", "omega",
    "boost", "smart", "spark", "trend", "prime", "swift"
]

def generate_domain():
    word = random.choice(WORDS)
    if len(word) < 5:
        word += random.choice(["ly", "it", "io"])
    return f"{word[:6]}.com"

def is_domain_available(domain):
    try:
        socket.gethostbyname(domain)
        return False  # TAKEN
    except socket.gaierror:
        return True   # AVAILABLE

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, "🚀 بدء توليد وفحص 1000 دومين...\n")

    for i in range(1, 1001):
        domain = generate_domain()
        available = is_domain_available(domain)

        status = "✅ AVAILABLE" if available else "❌ TAKEN"
        await context.bot.send_message(
            chat_id,
            f"[{i}/1000] 🔍 {domain} → {status}"
        )

        time.sleep(0.7)  # سرعة متوسطة (لا سريع ولا بطيء)

    await context.bot.send_message(chat_id, "🏁 انتهى الفحص.")

def main():
    if not BOT_TOKEN:
        raise Exception("BOT_TOKEN مش متضاف في Variables")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
