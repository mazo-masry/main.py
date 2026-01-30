import os
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# =====================
# VARIABLES
# =====================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# =====================
# GPT FUNCTION
# =====================
async def ask_gpt(text):
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "انت مساعد ذكي بترد باختصار وذكاء"},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

# =====================
# TELEGRAM HANDLER
# =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text("⏳ بفكر...")

    try:
        reply = await ask_gpt(user_text)
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("❌ حصل خطأ")

# =====================
# MAIN
# =====================
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
