import os
import asyncio
import random
import time
import logging
import requests
import re
import whois
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ================== إعدادات ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

ALLOWED_USERS = {ADMIN_ID}
GLOBAL_ACTIVE = False
checked_cache = set()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================== كيبورد ==================
ADMIN_KB = ReplyKeyboardMarkup(
    [
        ["🚀 Global"],
        ["➕ إضافة مستخدم", "➖ حذف مستخدم"]
    ],
    resize_keyboard=True
)

# ================== فحص WHOIS ==================
async def is_available(domain):
    try:
        loop = asyncio.get_event_loop()
        w = await loop.run_in_executor(None, whois.whois, domain)
        if not w.domain_name:
            return True
        return False
    except:
        return True

# ================== Global Hunter ==================
async def global_hunter(context: ContextTypes.DEFAULT_TYPE):
    global GLOBAL_ACTIVE

    SOURCES = [
        "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
        "https://mirror.cedia.org.ec/malwaredomains/justdomains"
    ]

    while GLOBAL_ACTIVE:
        for src in SOURCES:
            if not GLOBAL_ACTIVE:
                break

            try:
                r = requests.get(src, timeout=20)
                domains = re.findall(
                    r'\b(?:[a-z0-9-]+\.)+(?:com|net|org|io|co)\b',
                    r.text.lower()
                )

                random.shuffle(domains)

                for domain in domains[:30]:
                    if not GLOBAL_ACTIVE:
                        break

                    if domain in checked_cache:
                        continue

                    checked_cache.add(domain)

                    try:
                        requests.get(f"http://{domain}", timeout=1.5)
                    except:
                        if await is_available(domain):
                            await context.bot.send_message(
                                chat_id=ADMIN_ID,
                                text=f"🌍 GLOBAL HIT\n\n✅ {domain}"
                            )

                    await asyncio.sleep(0.2)

            except Exception as e:
                logger.error(e)

        await asyncio.sleep(10)

# ================== أوامر ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "🚀 Bot Online\n\nالأوامر المتاحة للأدمن فقط",
        reply_markup=ADMIN_KB
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GLOBAL_ACTIVE
    user_id = update.effective_user.id
    text = update.message.text

    if user_id != ADMIN_ID:
        return

    # -------- Global --------
    if text == "🚀 Global":
        if not GLOBAL_ACTIVE:
            GLOBAL_ACTIVE = True
            checked_cache.clear()
            asyncio.create_task(global_hunter(context))
            await update.message.reply_text("📡 Global STARTED")
        else:
            GLOBAL_ACTIVE = False
            await update.message.reply_text("🛑 Global STOPPED")
        return

    # -------- إضافة مستخدم --------
    if text == "➕ إضافة مستخدم":
        context.user_data["mode"] = "ADD"
        await update.message.reply_text("📩 ابعت ID المستخدم")
        return

    # -------- حذف مستخدم --------
    if text == "➖ حذف مستخدم":
        context.user_data["mode"] = "DEL"
        await update.message.reply_text("📩 ابعت ID المستخدم")
        return

    # -------- تنفيذ الإضافة / الحذف --------
    mode = context.user_data.get("mode")
    if mode in ["ADD", "DEL"]:
        try:
            target = int(text)
            if mode == "ADD":
                ALLOWED_USERS.add(target)
                await update.message.reply_text(f"✅ تم إضافة {target}")
            else:
                ALLOWED_USERS.discard(target)
                await update.message.reply_text(f"❌ تم حذف {target}")
        except:
            await update.message.reply_text("⚠️ ID غير صحيح")

        context.user_data["mode"] = None

# ================== تشغيل ==================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()

if __name__ == "__main__":
    main()
