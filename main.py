import os
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780  # معرف المدير الخاص بك

AUTHORIZED_USERS = {ADMIN_ID}
VALID_KEYS = {}

def generate_key():
    return "DH-" + ''.join(random.choices(string.ascii_upper + string.digits, k=10))

def get_domain_status(domain):
    """فحص حالة الدومين وتاريخ انتهائه بشكل مستقر"""
    try:
        res = requests.get(f"https://rdap.verisign.com/com/v1/domain/{domain}", timeout=5)
        if res.status_code == 404:
            return "متاح ✅", "N/A"
        data = res.json()
        # استخراج تاريخ الانتهاء
        expiry = "غير معروف"
        for event in data.get("events", []):
            if event.get("eventAction") == "expiration":
                expiry = event.get("eventDate").split("T")[0]
        return "محجوز 🔒", expiry
    except:
        return "خطأ في الفحص", ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in AUTHORIZED_USERS:
        keyboard = [
            ['4 حروف', '5 حروف'],
            ['بحث عن متاح', 'قربت تنتهي ⏰'],
            ['توليد مفتاح جديد 🔑']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("✅ أهلاً بك يا مدير! اختر من القائمة:", reply_markup=markup)
    else:
        await update.message.reply_text("🚫 الوصول مرفوض. أرسل مفتاح التفعيل.")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # 1. حل مشكلة المفتاح (البحث عن كلمة 'توليد' لضمان العمل)
    if 'توليد' in text and user_id == ADMIN_ID:
        key = generate_key()
        VALID_KEYS[key] = "unused"
        await update.message.reply_text(f"🔑 مفتاح جديد:\n`{key}`", parse_mode='Markdown')
        return

    # تفعيل المفاتيح للأجهزة الأخرى
    if text.startswith("DH-"):
        if text in VALID_KEYS and VALID_KEYS[text] == "unused":
            AUTHORIZED_USERS.add(user_id)
            VALID_KEYS[text] = "used"
            await update.message.reply_text("🎉 تم التفعيل بنجاح!")
        else:
            await update.message.reply_text("❌ مفتاح غير صحيح.")
        return

    if user_id not in AUTHORIZED_USERS: return

    # 2. حل مشكلة "قربت تنتهي" (البحث عن عينات عشوائية وفحص تواريخها)
    msg = await update.message.reply_text("⏳ جاري المعالجة...")
    
    if 'تنتهي' in text:
        results = []
        for _ in range(3): # عدد قليل لضمان عدم حدوث Crash
            d = ''.join(random.choices(string.ascii_lowercase, k=4)) + ".com"
            status, expiry = get_domain_status(d)
            if status == "محجوز 🔒":
                results.append(f"⏰ {d}\n📅 ينتهي في: {expiry}")
        
        response = "🔔 دومينات محجوزة وتاريخ انتهائها:\n\n" + ("\n\n".join(results) if results else "لم يتم العثور على دومينات محجوزة حالياً، جرب مرة أخرى.")
        await msg.edit_text(response)

    elif '4' in text or '5' in text:
        length = 4 if '4' in text else 5
        domains = [''.join(random.choices(string.ascii_lowercase, k=length)) + ".com" for _ in range(5)]
        await msg.edit_text(f"🔎 مقترحات {length} حروف:\n\n" + "\n".join(domains))
    
    elif 'متاح' in text:
        d = ''.join(random.choices(string.ascii_lowercase, k=5)) + ".com"
        status, _ = get_domain_status(d)
        await msg.edit_text(f"🌐 فحص عشوائي:\nالدومين: {d}\nالحالة: {status}")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    app.run_polling(drop_pending_updates=True)
