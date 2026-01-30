import asyncio
import whois
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# =====================
BOT_TOKEN = "8166138523:AAGTRyw29i8lvojIsyrCU3tVGWMRAteblkU"
# =====================

WORDS = [
    "alpha","bravo","delta","novex","orbit","pixel","logic","swift",
    "vortex","nexus","prime","zenix","crypt","cloud","spark","pulse",
    "flare","quant","block","stack","corex","media","arena","brand"
]

CHECK_LIMIT = 100
DELAY = 1  # ثانية بين كل فحص

def generate_domains():
    domains = []
    for w in WORDS:
        if 5 <= len(w) <= 6:
            domains.append(f"{w}.com")
    return domains[:CHECK_LIMIT]

def is_available(domain):
    try:
        data = whois.whois(domain)
        return data.domain_name is None
    except:
        return True  # غالباً متاح لو WHOIS فشل

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Domain Hunter Bot\n"
        "استخدم /hunt لبدء فحص الدومينات"
    )

async def hunt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    domains = generate_domains()

    await context.bot.send_message(
        chat_id,
        f"🔍 بدء فحص {len(domains)} دومين\n⏳ بهدوء لتفادي أي حظر"
    )

    count = 0

    for domain in domains:
        count += 1
        await context.bot.send_message(
            chat_id,
            f"⏳ {count}/{len(domains)}\n🔎 فحص: {domain}"
        )

        try:
            available = is_available(domain)

            if available:
                await context.bot.send_message(
                    chat_id,
                    f"🟢 AVAILABLE DOMAIN 🔥\n{domain}"
                )
            else:
                await context.bot.send_message(
                    chat_id,
                    f"❌ TAKEN: {domain}"
                )

        except Exception as e:
            await context.bot.send_message(
                chat_id,
                f"⚠️ ERROR مع {domain}\n{str(e)}"
            )

        await asyncio.sleep(DELAY)

    await context.bot.send_message(chat_id, "✅ انتهى الفحص بالكامل")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hunt", hunt))
    print("🤖 BOT IS RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
