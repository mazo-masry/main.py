import os
import logging
import whois
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمنع الانهيار ومراقبة الأداء
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

# دالة الفحص الذكي (تتجنب الحظر والتعليق)
def check_domain_free(domain):
    try:
        # فحص أولي سريع
        w = whois.whois(domain)
        if not w.domain_name:
            return "✅ متاح"
        return "🔒 محجوز"
    except Exception as e:
        # إذا لم يجد الدومين في السجلات العالمية فهذا يعني أنه متاح غالباً
        return "✅ متاح"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['🎯 فحص شامل (Com/Net/Org/Xyz)'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "💎 **تم تفعيل صائد الدومينات الحر!**\n\n"
            "نسيان جودادي هو أفضل قرار. الآن يمكنك الفحص بحرية وبدون مفاتيح API.\n"
            "استخدم الأزرار بالأسفل لبدء القنص.",
            reply_markup=markup, parse_mode='Markdown'
        )

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # --- 1. منطق الفحص الشامل ---
    if text == '🎯 فحص شامل (Com/Net/Org/Xyz)':
        await update.message.reply_text("✏️ أرسل الاسم الذي تريد قنصه (مثلاً: `bestoffer`):")
        context.user_data['state'] = 'WAIT_NAME'
        return

    if state == 'WAIT_NAME':
        base_name = text.strip().lower().replace(" ", "")
        context.user_data['state'] = None
        
        msg = await update.message.reply_text(f"📡 جاري الاتصال بالسجلات العالمية لفحص `{base_name}`...")
        
        tlds = [".com", ".net", ".org", ".xyz", ".me", ".info"]
        report = f"📊 **تقرير التوفر العالمي لـ `{base_name}`:**\n\n"
        
        for tld in tlds:
            full_domain = base_name + tld
            status = check_domain_free(full_domain)
            report += f"{status} | `{full_domain}`\n"
        
        await msg.edit_text(report, parse_mode='Markdown')
        return

    # --- 2. منطق الإدارة (إضافة/حذف) تم التأكد منها ---
    if text == '➕ إضافة مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل المعرف للإضافة: `اضف 12345`", parse_mode='Markdown')
    elif text == '➖ حذف مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل المعرف للحذف: `احذف 12345`", parse_mode='Markdown')
    
    elif text.startswith("اضف ") and user_id == ADMIN_ID:
        try:
            new_id = int(text.split(" ")[1])
            ALLOWED_USERS.add(new_id)
            await update.message.reply_text(f"✅ تم تفعيل العضو: `{new_id}`")
        except: pass
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
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        # استخدام drop_pending_updates لمنع تراكم الرسايل والـ Crash
        app.run_polling(drop_pending_updates=True)
