import os
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات ---
# سيقوم الكود بالبحث عن التوكن في إعدادات Railway أولاً
TOKEN = os.getenv("BOT_TOKEN")

def generate_domain(length):
    """توليد اسم عشوائي خماسي أو رباعي"""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length)) + ".com"

def check_availability(domain):
    """فحص حقيقي وسريع عبر RDAP"""
    try:
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
        res = requests.get(url, timeout=5)
        return res.status_code == 404 # 404 يعني غير مسجل (متاح)
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['4 حروف', '5 حروف'], ['بحث عن متاح', 'كلمات مفهومة']]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("مرحباً بك في بوت صائد الدومينات! 🚀 اختر من القائمة:", reply_markup=markup)

async def handle_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    msg = await update.message.reply_text("⏳ جاري العمل...")
    
    results = []
    if '4' in text or '5' in text:
        length = 4 if '4' in text else 5
        for _ in range(10):
            results.append(generate_domain(length))
        response = f"🔎 مقترحات {length} حروف:\n" + "\n".join(results)
        
    elif 'متاح' in text:
        found = []
        for _ in range(20):
            d = generate_domain(5)
            if check_availability(d):
                found.append(f"✅ {d}")
            if len(found) >= 3: break
        response = "💎 دومينات متاحة غالباً:\n" + "\n".join(found) if found else "❌ حاول مرة أخرى."

    elif 'كلمة' in text:
        words = ["fast", "cool", "smart", "tech", "web", "link", "hub", "pro"]
        for _ in range(5):
            results.append(random.choice(words) + generate_domain(2))
        response = "💡 كلمات مفهومة مقترحة:\n" + "\n".join(results)
    
    else:
        response = "الرجاء استخدام الأزرار بالأسفل."

    await msg.edit_text(response)

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Error: BOT_TOKEN variable is missing!")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_request))
        print("🤖 Bot is running...")
        app.run_polling(drop_pending_updates=True)
