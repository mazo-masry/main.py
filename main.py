import os
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات الأساسية ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780  # معرفك الثابت لضمان الصلاحية

AUTHORIZED_USERS = {ADMIN_ID}
VALID_KEYS = {}

def generate_key():
    return "DH-" + ''.join(random.choices(string.ascii_upper + string.digits, k=10))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in AUTHORIZED_USERS:
        keyboard = [
            ['4 حروف', '5 حروف'],
            ['بحث عن متاح', 'قربت تنتهي ⏰'],
            ['توليد مفتاح جديد 🔑']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"✅ أهلاً بك يا مدير!\nاستخدم الأزرار أو أرسل /generate للحصول على مفتاح.", reply_markup=markup)
    else:
        await update.message.reply_text("🚫 البوت مغلق. أرسل مفتاح التفعيل للمتابعة.")

async def gen_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر مباشر لتوليد المفتاح لضمان العمل في حال فشل الزر"""
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        key = generate_key()
        VALID_KEYS[key] = "unused"
        await update.message.reply_text(f"🔑 مفتاح جديد:\n`{key}`", parse_mode='Markdown')

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # تفعيل المفاتيح
    if text.startswith("DH-"):
        if text in VALID_KEYS and VALID_KEYS[text] == "unused":
            AUTHORIZED_USERS.add(user_id)
            VALID_KEYS[text] = "used"
            await update.message.reply_text("🎉 تم التفعيل بنجاح! اضغط /start")
        else:
            await update.message.reply_text("❌ مفتاح غير صحيح.")
        return

    if user_id not in AUTHORIZED_USERS: return

    # الحل النهائي للمفتاح: البحث عن الكلمة داخل النص
    if "توليد" in text and user_id == ADMIN_ID:
        key = generate_key()
        VALID_KEYS[key] = "unused"
        await update.message.reply_text(f"🔑 مفتاح جديد:\n`{key}`", parse_mode='Markdown')
        return

    # أوامر البحث البسيطة لمنع الـ Crash
    if '4' in text or '5' in text:
        length = 4 if '4' in text else 5
        res = [''.join(random.choices(string.ascii_lowercase, k=length)) + ".com" for _ in range(5)]
        await update.message.reply_text(f"🔎 مقترحات {length} حروف:\n" + "\n".join(res))
    elif 'تنتهي' in text or 'متاح' in text:
        await update.message.reply_text("⏳ ميزة الفحص المتقدم قيد الصيانة لضمان استقرار السيرفر.")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", gen_cmd)) # أمر إضافي كاحتياط
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.run_polling(drop_pending_updates=True)
        response = "🔔 دومينات قربت تنتهي:\n\n" + "\n\n".join(expiring)

    elif 'كلمة' in text:
        words = ["nova", "fast", "web", "smart", "go"]
        res = [random.choice(words) + ''.join(random.choices(string.ascii_lowercase, k=2)) + ".com" for _ in range(5)]
        response = "💡 دومينات بكلمات مفهومة:\n\n" + "\n".join(res)
    
    else:
        response = "يرجى اختيار أمر من القائمة بالأسفل."

    await msg.edit_text(response)

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
    print("🤖 البوت يعمل الآن بنجاح...")
    app.run_polling(drop_pending_updates=True)
