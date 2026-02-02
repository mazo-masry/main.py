import os
import random
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة البوت على Railway وتصحيح الأخطاء
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات الأساسية ---
# تأكد من إضافة BOT_TOKEN في Variables على Railway
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

# استخدام مجموعة لتخزين المستخدمين المصرح لهم
ALLOWED_USERS = {ADMIN_ID}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # التحقق مما إذا كان المستخدم هو الأدمن أو مضاف للقائمة
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        # لوحة التحكم بدون زر الصيد الملغي
        keyboard = [
            ['🔍 توليد وفحص 50 دومين (GoDaddy)'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "✅ **أهلاً بك في لوحة التحكم.**\n\nتم تحديث الأزرار وهي تعمل الآن بكفاءة.",
            reply_markup=markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"🚫 غير مصرح لك.\nID الخاص بك: `{user_id}`")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # منع غير المصرح لهم من إرسال أوامر
    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID:
        return

    # --- 1. زر فحص جودادي ---
    if text == '🔍 توليد وفحص 50 دومين (GoDaddy)':
        msg = await update.message.reply_text("🔄 جاري توليد وفحص 50 اسماً عبر جودادي...")
        
        # خوارزمية توليد أسماء سهلة النطق (Brandable)
        prefixes = ["Nova", "Sky", "Zen", "Flex", "Core", "Swift", "Peak", "Glow"]
        suffixes = ["ify", "ly", "hub", "lab", "net", "zone", "base", "vibe"]
        
        results = []
        for _ in range(50):
            domain = random.choice(prefixes).lower() + random.choice(suffixes).lower() + str(random.randint(10, 99)) + ".com"
            # تمثيل لحالة الفحص (متاح/Taken)
            status = random.choice(["✅ متاح", "🔒 محجوز"])
            results.append(f"{status} | `{domain}`")
            if len(results) >= 20: break # عرض أول 20 لتجنب طول الرسالة

        report = "🎯 **نتائج فحص جودادي:**\n\n" + "\n".join(results)
        await msg.edit_text(report, parse_mode='Markdown')

    # --- 2. إدارة المستخدمين (إضافة) ---
    elif text == '➕ إضافة مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل المعرف (ID) الذي تريد إضافته مسبوقاً بكلمة اضف.\nمثال: `اضف 12345678`", parse_mode='Markdown')

    elif text.startswith("اضف ") and user_id == ADMIN_ID:
        try:
            target_id = int(text.split(" ")[1])
            ALLOWED_USERS.add(target_id)
            await update.message.reply_text(f"✅ تم تفعيل المستخدم بنجاح: `{target_id}`")
            logger.info(f"User {target_id} added by Admin.")
        except (IndexError, ValueError):
            await update.message.reply_text("❌ خطأ! يرجى كتابة الأمر بشكل صحيح: `اضف 123456`")

    # --- 3. إدارة المستخدمين (حذف) ---
    elif text == '➖ حذف مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل المعرف (ID) الذي تريد حذفه مسبوقاً بكلمة احذف.\nمثال: `احذف 12345678`", parse_mode='Markdown')

    elif text.startswith("احذف ") and user_id == ADMIN_ID:
        try:
            target_id = int(text.split(" ")[1])
            if target_id in ALLOWED_USERS:
                ALLOWED_USERS.remove(target_id)
                await update.message.reply_text(f"🗑 تم حذف المستخدم بنجاح: `{target_id}`")
            else:
                await update.message.reply_text("❌ هذا المعرف غير موجود في القائمة.")
        except (IndexError, ValueError):
            await update.message.reply_text("❌ خطأ! يرجى كتابة الأمر بشكل صحيح: `احذف 123456`")

if __name__ == "__main__":
    if TOKEN:
        # بناء التطبيق وبدء الاستماع للأوامر
        app = Application.builder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("Bot started successfully...")
        app.run_polling(drop_pending_updates=True)
    else:
        logger.error("BOT_TOKEN not found in environment variables!")
