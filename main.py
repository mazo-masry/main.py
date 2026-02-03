import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ====== TOKEN ======
TOKEN = os.getenv("BOT_TOKEN")

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📥 تحميل فيديو", callback_data="download"),
            InlineKeyboardButton("🌐 فحص دومين", callback_data="whois"),
        ],
        [
            InlineKeyboardButton("ℹ️ عن البوت", callback_data="about"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 أهلاً بيك!\nاختار من الزراير 👇",
        reply_markup=reply_markup
    )

# ====== BUTTON HANDLER ======
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "download":
        await query.edit_message_text(
            "📥 ابعت رابط الفيديو (يوتيوب مثلاً)"
        )

    elif query.data == "whois":
        await query.edit_message_text(
            "🌐 ابعت اسم الدومين (example.com)"
        )

    elif query.data == "about":
        await query.edit_message_text(
            "🤖 بوت تجريبي شغال على Koyeb\n"
            "✅ Python Telegram Bot\n"
            "🚀 Polling Mode"
        )

# ====== MAIN ======
def main():
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN مش موجود في Environment Variables")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
