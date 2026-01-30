import os
import asyncio
import whois
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

DOMAINS = [
    "novex.com", "zenly.com", "crypta.com",
    "bytex.com", "corex.com", "nexor.com",
    "fluxy.com", "datix.com", "webly.com"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Domain Hunter شغال\n"
        "اكتب /hunt لبدء الفحص"
    )

async def hunt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 بدء الفحص...")

    count = 0
    for domain in DOMAINS:
        count += 1
        await update.message.reply_text(f"⏳ {count}/{len(DOMAINS)}\n{domain}")

        try:
            w = whois.whois(domain)
            if not w.domain_name:
                await update.message.reply_text(
                    f"🟢 AVAILABLE 🔥\n{domain}"
                )
        except Exception:
            await update.message.reply_text(
                f"🟢 AVAILABLE 🔥\n{domain}"
            )

        await asyncio.sleep(1)

    await update.message.reply_text("✅ انتهى الفحص")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hunt", hunt))

    print("🤖 BOT IS RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
