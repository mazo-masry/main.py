import os
import logging
import random
import whois  # تأكد من إضافة python-whois في ملف requirements.txt
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة Railway ومنع الـ Crash
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

# دالة الفحص عبر نظام Whois العالمي (بدون API Key)
def check_availability(domain):
    try:
        w = whois.whois(domain)
        if not w.domain_name:
            return "✅ متاح"
        return "🔒 محجوز"
    except Exception:
        return "✅ متاح"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['🔍 فحص شامل (جميع الامتدادات)'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "🚀 **بوت قناص الدومينات يعمل الآن!**\n\n"
            "تم تفعيل نظام الفحص الحر لتجنب أخطاء جودادي (Access Denied).\n"
            "استخدم الأزرار بالأسفل للتحكم.",
            reply_markup=markup, parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID:
        return

    # --- 1. زر الفحص الشامل (بدون API جودادي) ---
    if text == '🔍 فحص شامل (جميع الامتدادات)':
        await update.message.reply_text("✏️ أرسل الاسم الذي تريد فحصه (مثلاً: `apple` أو `smartwork`):")
        context.user_data['state'] = 'WAIT_NAME'
        return

    if state == 'WAIT_NAME':
        base_name = text.strip().lower()
        context.user_data['state'] = None
        msg = await update.message.reply_text(f"🔎 جاري فحص `{base_name}` في قواعد البيانات العالمية...")
        
        tlds = [".com", ".net", ".org", ".info", ".xyz", ".tech"]
        report = f"🎯 **نتائج الفحص لاسم `{base_name}`:**\n\n"
        
        for tld in tlds:
            full_domain = base_name + tld
            status = check_availability(full_domain)
            report += f"{status} | `{full_domain}`\n"
        
        await msg.edit_text(report, parse_mode='Markdown')
        return

    # --- 2. زر إضافة مستخدم (للأدمن فقط) ---
    if text == '➕ إضافة مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل معرف (ID) المستخدم هكذا: `اضف 123456`", parse_mode='Markdown')
        return

    if text.startswith("اضف ") and user_id == ADMIN_ID:
        try:
            new_id = int(text.split(" ")[1])
            ALLOWED_USERS.add(new_id)
            await update.message.reply_text(f"✅ تم تفعيل العضو بنجاح: `{new_id}`")
        except:
            await update.message.reply_text("❌ خطأ! اكتب الرقم بشكل صحيح.")
        return

    # --- 3. زر حذف مستخدم (للأدمن فقط) ---
    if text == '➖ حذف مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل معرف (ID) المستخدم هكذا: `احذف 123456`", parse_mode='Markdown')
        return

    if text.startswith("احذف ") and user_id == ADMIN_ID:
        try:
            del_id = int(text.split(" ")[1])
            if del_id in ALLOWED_USERS:
                ALLOWED_USERS.remove(del_id)
                await update.message.reply_text(f"🗑 تم حذف العضو: `{del_id}`")
            else:
                await update.message.reply_text("❌ هذا العضو غير موجود بالقائمة.")
        except:
            await update.message.reply_text("❌ خطأ في الإدخال.")
        return

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        logger.info("Bot is running...")
        app.run_polling(drop_pending_updates=True)
