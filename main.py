import os
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 123456789  # استبدل هذا برقم الـ ID الخاص بك لتصلك طلبات المفاتيح

# قواعد بيانات وهمية (يفضل استخدام SQL في المستقبل)
AUTHORIZED_USERS = set()
PENDING_KEYS = {} # {key: user_id}

def generate_key():
    """توليد مفتاح عشوائي من 8 أرقام وحروف"""
    return ''.join(random.choices(string.ascii_upper + string.digits, k=8))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in AUTHORIZED_USERS:
        keyboard = [['4 حروف', '5 حروف'], ['بحث عن متاح', 'كلمات مفهومة'], ['قربت تنتهي ⏰']]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("✅ أهلاً بك مجدداً في صائد الدومينات!", reply_markup=markup)
    else:
        # إذا كان المستخدم جديد، اطلب منه المفتاح
        await update.message.reply_text(
            "🚫 البوت مغلق. يرجى إدخال مفتاح التفعيل للمتابعة.\n"
            "للحصول على مفتاح، تواصل مع المطور."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # 1. نظام التحقق من المفتاح
    if user_id not in AUTHORIZED_USERS:
        # هنا يمكنك إضافة منطق حيث ترسل أنت المفتاح للمستخدم يدوياً
        # كمثال: لو كتب المستخدم كلمة "تفعيل" وأنت أعطيته كود
        if text.startswith("KEY-"):
            # في نسخة حقيقية ستقارن النص بقاعدة بياناتك
            AUTHORIZED_USERS.add(user_id)
            keyboard = [['4 حروف', '5 حروف'], ['بحث عن متاح', 'كلمات مفهومة'], ['قربت تنتهي ⏰']]
            markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("🎉 تم تفعيل البوت بنجاح!", reply_markup=markup)
        else:
            await update.message.reply_text("⚠️ المفتاح غير صحيح. يرجى إرسال مفتاح يبدأ بـ KEY-")
        return

    # 2. منطق البوت الأساسي (الذي قمنا ببنائه سابقاً)
    temp_msg = await update.message.reply_text("⏳ جاري المعالجة...")
    # ... (نفس منطق الفحص السابق) ...
    await temp_msg.edit_text(f"نتائج البحث عن: {text}")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)
