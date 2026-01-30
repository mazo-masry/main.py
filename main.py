import os
import asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
GD_KEY = os.getenv("GODADDY_KEY")
GD_SECRET = os.getenv("GODADDY_SECRET")

# كلمات حقيقية قصيرة (5–6 حروف)
DOMAINS = [
    "prime","logic","orbit","pixel","spark","swift",
    "alpha","nova","corex","zenix","clixo","bytex",
    "netly","webly","hosta","crypt","chain","block"
]

HEADERS = {
    "Authorization": f"sso-key {GD_KEY}:{GD_SECRET}",
    "Accept": "application/json"
}

def check_godaddy(domain):
    url = "https://api.godaddy.com/v1/domains/available"
    r = requests.get(
        url,
        headers=HEADERS,
        params={"domain": domain},
        timeout=15
    )
    return r.json().get("available", False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Domain Hunter شغال\n"
        "اكتب /check لبدء الفحص"
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    progress_msg = await context.bot.send_message(
        chat_id,
        "🔍 بدء فحص الدومينات من GoDaddy"
    )

    checked = 0
    log = []

    for name in DOMAINS[:100]:
        domain = name + ".com"
        checked += 1

        try:
            available = check_godaddy(domain)
            status = "✅ AVAILABLE" if available else "❌ TAKEN"
        except Exception:
            status = "⚠️ ERROR"

        line = f"{checked}. {domain} → {status}"
        print(line)
        log.append(line)

        # 👑 لو متاح → رسالة فورية لوحدها
        if status.startswith("✅"):
            await context.bot.send_message(
                chat_id,
                f"🔥 DOMAIN AVAILABLE 🔥\n\n{domain}"
            )

        # تحديث رسالة المتابعة
        await progress_msg.edit_text(
            "🔍 فحص جاري...\n\n" +
            "\n".join(log[-10:]) +
            f"\n\n⏱️ {checked}/100"
        )

        await asyncio.sleep(1)

    await context.bot.send_message(chat_id, "✅ انتهى الفحص")

def main():
    print("🤖 BOT STARTED")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))
    app.run_polling()

if __name__ == "__main__":
    main()
