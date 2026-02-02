import os
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات الهامة ---
TOKEN = os.getenv("BOT_TOKEN")
# استبدل الرقم أدناه برقم الـ ID الذي حصلت عليه من @userinfobot
ADMIN_ID = 592837465  

# الذاكرة المؤقتة للمستخدمين المفعلين
AUTHORIZED_USERS = {ADMIN_ID} 
VALID_KEYS = {} 

def generate_key():
    return "DH-" + ''.join(random.choices(string.ascii_upper + string.digits, k=10))

def get_domain_info(domain):
    """فحص التوافر وتاريخ الانتهاء"""
    try:
        res = requests.get(f"https://rdap.verisign.com/com/v1/domain/{domain}", timeout=5)
        if res.status_code == 404:
            return {"status": "متاح ✅", "expiry": "N/A"}
        data = res.json()
        expiry = next((e['eventDate'].split('T')[0] for e in data.get('events', []) if e.get('eventAction') == 'expiration'), "غير محدد")
        return {"status": "محجوز 🔒", "expiry": expiry}
    except: return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in AUTHORIZED_USERS:
        keyboard = [['4 حروف', '5 حروف'], ['بحث عن متاح', 'قربت تنتهي ⏰'], ['كلمات مفهومة']]
        if user_id == ADMIN_ID:
            keyboard.append(['توليد مفتاح جديد 🔑'])
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("✅ أهلاً بك يا مدير! البوت جاهز للعمل.", reply_markup=markup)
    else:
        await update.message.reply_text("🚫 الوصول مرفوض. أرسل مفتاح التفعيل الخاص بك.")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # نظام تفعيل المفاتيح
    if text.startswith("DH-"):
        if text in VALID_KEYS and VALID_KEYS[text] == "unused":
            AUTHORIZED_USERS.add(user_id)
            VALID_KEYS[text] = "used"
            await update.message.reply_text("🎉 تم تفعيل جهازك بنجاح! اضغط /start")
        else:
            await update.message.reply_text("❌ مفتاح غير صحيح.")
        return

    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("⚠️ يرجى التفعيل أولاً.")
        return

    # أوامر الآدمن لتوليد المفاتيح
    if text == 'توليد مفتاح جديد 🔑' and user_id == ADMIN_ID:
        new_key = generate_key()
        VALID_KEYS[new_key] = "unused"
        await update.message.reply_text(f"🔑 مفتاح جديد:\n`{new_key}`", parse_mode='Markdown')
        return

    # منطق البحث (4 حروف، 5 حروف، متاح، تنتهي)
    msg = await update.message.reply_text("⏳ جاري المعالجة...")
    # ... نفس منطق البحث السابق ...
    await msg.edit_text(f"نتائج البحث عن: {text}")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    app.run_polling(drop_pending_updates=True)
