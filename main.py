import os
import logging
import whois
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة Railway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# الإعدادات
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

# دالة فحص حالة الدومين
def check_availability(domain):
    try:
        w = whois.whois(domain)
        return "🔒 محجوز" if w.domain_name else "✅ متاح"
    except Exception:
        return "✅ متاح"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [['🔍 فحص شامل (بدون API)'], ['➕ إضافة مستخدم', '➖ حذف مستخدم']]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("🚀 **البوت جاهز للعمل!**\nتم تفعيل نظام الفحص الحر لضمان الاستقرار.", reply_markup=markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # زر الفحص
    if text == '🔍 فحص شامل (بدون API)':
        await update.message.reply_text("✏️ أرسل الاسم المراد فحصه:")
        context.user_data['state'] = 'WAIT_NAME'
        return

    if state == 'WAIT_NAME':
        base_name = text.strip().lower()
        context.user_data['state'] = None
        msg = await update.message.reply_text(f"🔎 جاري الفحص لـ `{base_name}`...")
        tlds = [".com", ".net", ".org", ".info", ".xyz"]
        report = f"🎯 **النتائج:**\n\n"
        for tld in tlds:
            report += f"{check_availability(base_name + tld)} | `{base_name + tld}`\n"
        await msg.edit_text(report, parse_mode='Markdown')

    # أزرار الإدارة
    elif text.startswith("اضف ") and user_id == ADMIN_ID:
        try:
            target = int(text.split(" ")[1])
            ALLOWED_USERS.add(target)
            await update.message.reply_text(f"✅ تم تفعيل: `{target}`")
        except: pass
    elif text.startswith("احذف ") and user_id == ADMIN_ID:
        try:
            target = int(text.split(" ")[1])
            if target in ALLOWED_USERS: ALLOWED_USERS.remove(target)
            await update.message.reply_text(f"🗑 تم حذف: `{target}`")
        except: pass

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.run_polling()
