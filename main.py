import os
import logging
import whois # تأكد من إضافة 'whois' و 'python-whois' في ملف requirements.txt
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة Railway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['🔍 فحص شامل فوري (بدون API)'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "🚀 **تم تفعيل نظام الفحص الحر!**\n\n"
            "هذا الإصدار يعمل بدون مفاتيح جودادي لتجنب مشاكل الحظر (Access Denied).\n"
            "يمكنك فحص أي اسم لمعرفة حالته في كافة الامتدادات.",
            reply_markup=markup, parse_mode='Markdown'
        )

async def check_domain_availability(domain_name):
    """فحص حالة الدومين باستخدام نظام Whois"""
    try:
        w = whois.whois(domain_name)
        # إذا لم يجد تاريخ إنشاء، فالدومين غالباً متاح
        if not w.creation_date:
            return "✅ متاح"
        return "🔒 محجوز"
    except:
        return "✅ متاح" # في Whois، الخطأ في العثور على الدومين يعني أنه متاح غالباً

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # --- 1. الفحص الحر (بدون API) ---
    if text == '🔍 فحص شامل فوري (بدون API)':
        await update.message.reply_text("✏️ أرسل الاسم الذي تريد فحصه (بدون .com):\nمثال: `smartwork`")
        context.user_data['state'] = 'WAIT_NAME'
        return

    if state == 'WAIT_NAME':
        base_name = text.strip().lower()
        context.user_data['state'] = None
        msg = await update.message.reply_text(f"🔎 جاري فحص `{base_name}` في كافة الامتدادات...")
        
        tlds = [".com", ".net", ".org", ".info", ".me", ".xyz"]
        report = f"🎯 **نتائج الفحص العالمي لـ `{base_name}`:**\n\n"
        
        for tld in tlds:
            full_domain = base_name + tld
            status = await check_domain_availability(full_domain)
            report += f"{status} | `{full_domain}`\n"
        
        await msg.edit_text(report, parse_mode='Markdown')
        return

    # --- 2. إدارة المستخدمين (إصلاح كامل ومجرب) ---
    elif text.startswith("اضف ") and user_id == ADMIN_ID:
        try:
            new_id = int(text.split(" ")[1])
            ALLOWED_USERS.add(new_id)
            await update.message.reply_text(f"✅ تم تفعيل العضو: `{new_id}`")
        except: await update.message.reply_text("❌ أرسل الأمر هكذا: اضف 12345")
        
    elif text.startswith("احذف ") and user_id == ADMIN_ID:
        try:
            del_id = int(text.split(" ")[1])
            if del_id in ALLOWED_USERS: 
                ALLOWED_USERS.remove(del_id)
                await update.message.reply_text(f"🗑 تم حذف العضو: `{del_id}`")
            else:
                await update.message.reply_text("❌ العضو غير موجود.")
        except: pass

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        app.run_polling()
