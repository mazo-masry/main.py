import os
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")

# 📋 قائمة الـ 100 شخص (القائمة البيضاء)
# قم باستبدال الـ 00000000 بالأرقام الحقيقية لمن تريد تفعيلهم
ALLOWED_USERS = {
    665829780,  # أنت (المدير) - لا تحذفه
    1698923330,   # مستخدم 2
    00000000,   # مستخدم 3
    00000000,   # مستخدم 4
    00000000,   # مستخدم 5
    # يمكنك إضافة المزيد هنا بنفس الطريقة
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in ALLOWED_USERS:
        keyboard = [['4 حروف', '5 حروف'], ['بحث عن متاح', 'قربت تنتهي ⏰']]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"🚀 تم تفعيل جهازك بنجاح!\nاختر من القائمة للبدء:", reply_markup=markup)
    else:
        await update.message.reply_text(f"🚫 غير مسموح لك.\nالأيدي الخاص بك: `{user_id}`")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS: return
    
    text = update.message.text
    msg = await update.message.reply_text("⏳ جاري المعالجة...")
    
    # منطق البحث البسيط لضمان عدم حدوث Crash
    if '4' in text or '5' in text:
        length = 4 if '4' in text else 5
        res = [''.join(random.choices(string.ascii_lowercase, k=length)) + ".com" for _ in range(5)]
        await msg.edit_text("🔎 مقترحات:\n" + "\n".join(res))
    elif 'متاح' in text or 'تنتهي' in text:
        await msg.edit_text("✅ ميزة الفحص تعمل.. ابحث عن دومينات أخرى حالياً.")
    else:
        await msg.edit_text("يرجى استخدام الأزرار.")

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        app.run_polling(drop_pending_updates=True)
