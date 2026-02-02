import os
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات الهامة ---
TOKEN = os.getenv("BOT_TOKEN")
# ضع رقم ID حسابك هنا (يمكنك الحصول عليه من بوت @userinfobot)
ADMIN_ID = 592837465  # <--- استبدل هذا الرقم برقم ID حسابك الحقيقي

AUTHORIZED_USERS = {ADMIN_ID} # الآدمن مفعّل تلقائياً
VALID_KEYS = {} # تخزين المفاتيح المولدة {key: status}

def generate_key():
    return "DH-" + ''.join(random.choices(string.ascii_upper + string.digits, k=10))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in AUTHORIZED_USERS:
        keyboard = [['4 حروف', '5 حروف'], ['بحث عن متاح', 'كلمات مفهومة'], ['قربت تنتهي ⏰']]
        if user_id == ADMIN_ID:
            keyboard.append(['توليد مفتاح جديد 🔑']) # زر خاص بالآدمن فقط
            
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("✅ أهلاً بك يا مدير! البوت جاهز للعمل.", reply_markup=markup)
    else:
        await update.message.reply_text("🚫 الوصول مرفوض. أرسل مفتاح التفعيل الخاص بجهازك للمتابعة.")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # 1. تفعيل مفتاح جديد
    if text.startswith("DH-"):
        if text in VALID_KEYS and VALID_KEYS[text] == "unused":
            AUTHORIZED_USERS.add(user_id)
            VALID_KEYS[text] = "used"
            await update.message.reply_text("🎉 تم تفعيل جهازك بنجاح! اضغط /start")
        else:
            await update.message.reply_text("❌ مفتاح غير صحيح أو تم استخدامه مسبقاً.")
        return

    # 2. حماية البوت (منع غير المصلح لهم)
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("⚠️ يرجى تفعيل البوت أولاً.")
        return

    # 3. أمر توليد المفاتيح (للآدمن فقط)
    if text == 'توليد مفتاح جديد 🔑' and user_id == ADMIN_ID:
        new_key = generate_key()
        VALID_KEYS[new_key] = "unused"
        await update.message.reply_text(f"🔑 مفتاح جديد جاهز:\n`{new_key}`\n\nأرسله للجهاز الآخر لتفعيله.", parse_mode='Markdown')
        return

    # 4. باقي وظائف البحث (الـ 4 و 5 حروف وغيرها)
    await update.message.reply_text(f"⏳ جاري تنفيذ طلبك لـ: {text}")
    # (هنا تضع منطق البحث الذي كان في الكود السابق)

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    app.run_polling(drop_pending_updates=True)
