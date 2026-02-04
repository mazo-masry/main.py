import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ========= ENV =========
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# ========= START =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌍 Global", callback_data="global")],
        [InlineKeyboardButton("📊 Status", callback_data="status")],
        [InlineKeyboardButton("ℹ️ Info", callback_data="info")],
        [
            InlineKeyboardButton("➕ Add User", callback_data="add_user"),
            InlineKeyboardButton("➖ Remove User", callback_data="remove_user")
        ]
    ]

    await update.message.reply_text(
        "👋 البوت شغال\nاختار زرار:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========= BUTTONS =========
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # ===== GLOBAL =====
    if query.data == "global":
        await query.edit_message_text(
            "🌍 Global Results\n\n"
            "✅ Bot: ONLINE\n"
            "✅ Server: KOYEB\n"
            "✅ Status: RUNNING\n\n"
            "🚀 كل حاجة شغالة تمام"
        )

    # ===== STATUS =====
    elif query.data == "status":
        await query.edit_message_text(
            "📊 Status\n\n"
            "🤖 Bot Active\n"
            "⚙️ No Errors\n"
            "📡 Connected"
        )

    # ===== INFO =====
    elif query.data == "info":
        await query.edit_message_text(
            f"ℹ️ Info\n\n"
            f"👤 Your ID: {user_id}\n"
            f"👑 Admin ID: {ADMIN_ID}"
        )

    # ===== ADD USER (ADMIN ONLY) =====
    elif query.data == "add_user":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ الزرار ده للأدمن فقط")
            return

        await query.edit_message_text(
            f"✅ Add User\n\n"
            f"ID: {user_id}"
        )

    # ===== REMOVE USER (ADMIN ONLY) =====
    elif query.data == "remove_user":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ الزرار ده للأدمن فقط")
            return

        await query.edit_message_text(
            f"🗑️ Remove User\n\n"
            f"ID: {user_id}"
        )

# ========= MAIN =========
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    app.run_polling()

if __name__ == "__main__":
    main()
