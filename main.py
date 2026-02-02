import os
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780  # رقم الـ ID بتاعك من الصورة

# ذاكرة مؤقتة للمفاتيح
AUTHORIZED_USERS = {ADMIN_ID}
VALID_KEYS = {}

def generate_key():
    return "DH-" + ''.join(random.choices(string.ascii_upper + string.digits, k=10))

def check_domain(domain):
    """فحص سريع ومستقر"""
    try:
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
        res = requests.get(url, timeout=5)
        if res.status_code == 404:
            return "متاح ✅"
        return "محجوز 🔒"
    except:
        return "خطأ في الفحص ⚠️"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in AUTHORIZED_USERS:
        keyboard = [
            ['4 حروف', '5 حروف'],
            ['بحث عن متاح', 'قربت تنتهي ⏰'],
            ['توليد مفتاح جديد 🔑']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"✅ أهلاً يا مدير!\nالبوت شغال الآن، اختر من القائمة:", reply_markup=markup)
    else:
        await update.message.reply_text("🚫 البوت خاص. أرسل كود التفعيل للمتابعة.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # تفعيل الكود للأجهزة التانية
    if text.startswith("DH-"):
        if text in VALID_KEYS and VALID_KEYS[text] == "unused":
            AUTHORIZED_USERS.add(user_id)
            VALID_KEYS[text] = "used"
            await update.message.reply_text("🎉 تم التفعيل! اضغط /start")
        else:
            await update.message.reply_text("❌ كود غلط.")
        return

    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("⚠️ فعل البوت الأول.")
        return

    # تشغيل زر التوليد للآدمن
    if "توليد" in text and user_id == ADMIN_ID:
        key = generate_key()
        VALID_KEYS[key] = "unused"
        await update.message.reply_text(f"🔑 كود جديد:\n`{key}`", parse_mode='Markdown')
        return

    # تنفيذ أوامر البحث
    temp = await update.message.reply_text("⏳ جاري البحث...")
    
    if '4' in text or '5' in text:
        num = 4 if '4' in text else 5
        res = [f"{''.join(random.choice(string.ascii_lowercase) for _ in range(num))}.com" for _ in range(5)]
        await temp.edit_text("🔎 مقترحات:\n" + "\n".join(res))
    elif 'متاح' in text:
        # فحص عينة سريعة
        d = ''.join(random.choice(string.ascii_lowercase) for _ in range(5)) + ".com"
        status = check_domain(d)
        await temp.edit_text(f"🌐 الدومين: {d}\n📊 الحالة: {status}")
    else:
        await temp.edit_text("استخدم الأزرار يا بطل.")

if __name__ == "__main__":
    if not TOKEN:
        print("TOKEN MISSING!")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.run_polling(drop_pending_updates=True)
