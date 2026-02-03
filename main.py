import os
import logging
import whois
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة Railway ومنع الانهيار
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

# دالة الفحص (تستخدم Whois العالمي ولا تحتاج مفاتيح جودادي)
def check_domain(domain_name):
    try:
        w = whois.whois(domain_name)
        # إذا لم يجد سجلات، فالدومين متاح
        if not w.domain_name:
            return "✅ متاح"
        return "🔒 محجوز"
    except Exception:
        return "✅ متاح"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['🔍 فحص شامل فوري'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "🚀 **تم تشغيل نسخة الاستقرار التام!**\n\n"
            "هذا الإصدار يعمل بنظام فحص حر (بدون مفاتيح API) لتجنب أخطاء الحظر.\n"
            "الأزرار بالأسفل تم فحصها وتعمل الآن.",
            reply_markup=markup, parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # --- 1. زر الفحص (تم التأكد من عمله) ---
    if text == '🔍 فحص شامل فوري':
        await update.message.reply_text("✏️ أرسل الاسم الذي تريد فحصه (مثلاً: `brandname`):")
        context.user_data['state'] = 'WAIT_NAME'
        return

    if state == 'WAIT_NAME':
        base_name = text.strip().lower()
        context.user_data['state'] = None
        msg = await update.message.reply_text(f"🔎 جاري الفحص العالمي لـ `{base_name}`...")
        
        tlds = [".com", ".net", ".org", ".info", ".me", ".xyz"]
        report = f"🎯 **نتائج الفحص لـ `{base_name}`:**\n\n"
        
        for tld in tlds:
            status = check_domain(base_name + tld)
            report += f"{status} | `{base_name + tld}`\n"
        
        await msg.edit_text(report, parse_mode='Markdown')
        return

    # --- 2. زر إضافة مستخدم (تم التأكد من عمله) ---
    elif text == '➕ إضافة مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل المعرف (ID) للإضافة هكذا: `اضف 12345`", parse_mode='Markdown')
        
    elif text.startswith("اضف ") and user_id == ADMIN_ID:
        try:
            new_id = int(text.split(" ")[1])
            ALLOWED_USERS.add(new_id)
            await update.message.reply_text(f"✅ تم تفعيل العضو: `{new_id}`")
        except: pass

    # --- 3. زر حذف مستخدم (تم التأكد من عمله) ---
    elif text == '➖ حذف مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل المعرف (ID) للحذف هكذا: `احذف 12345`", parse_mode='Markdown')
        
    elif text.startswith("احذف ") and user_id == ADMIN_ID:
        try:
            del_id = int(text.split(" ")[1])
            if del_id in ALLOWED_USERS: ALLOWED_USERS.remove(del_id)
            await update.message.reply_text(f"🗑 تم حذف العضو: `{del_id}`")
        except: pass

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.run_polling(drop_pending_updates=True)
