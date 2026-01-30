import os
import telebot
import time

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ BOT_TOKEN not found")
    exit()

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=["start"])
def start(msg):
    bot.reply_to(msg, "🤖 البوت شغال تمام!")

print("✅ Bot is running...")

bot.infinity_polling()
