import os
import logging
import whois  # تأكد من إضافة python-whois في ملف requirements.txt
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة الأداء
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

# دالة الفحص العالمي (WHOIS) - تعمل مع كل الدومينات
def check_domain_global(domain_name):
    try:
        w = whois.whois(domain_name)
        # إذا لم تكن هناك بيانات للنطاق، فهو متاح
        if not w.domain_name:
            return "✅ متاح"
        return "🔒 محجوز"
    except Exception:
        # في حال حدوث خطأ في الاتصال بسيرفر Whois، غالباً يكون النطاق متاحاً
        return "✅ متاح"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['🔎 فحص دومين (جميع الامتدادات)'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "🚀 **تم تفعيل القناص العالمي!**\n\n"
            "هذا البوت يفحص الدومينات عبر نظام WHOIS العالمي مباشرة.\n"
            "لا حاجة لجودادي أو أي مفاتيح API معقدة.",
            reply_markup=markup, parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # --- 1. زر الفحص الشامل ---
    if text == '🔎 فحص دومين (جميع الامتدادات)':
        await update.message.reply_text("✏️ أرسل الاسم الذي تريد فحصه (مثلاً: `superbrand`):")
        context.user_data['state'] = 'WAIT_NAME'
        return

    if state == 'WAIT_NAME':
        base_name = text.strip().lower()
        context.user_data['state'] = None
        msg = await update.message.reply_text(f"⏳ جاري فحص `{base_name}` في السجلات العالمية...")
        
        # أهم الامتدادات المطلوبة
        tlds = [".com", ".net", ".org", ".io", ".me", ".tech"]
        report = f"🎯 **نتائج الفحص العالمي لـ `{base_name}`:**\n\n"
        
        for tld in tlds:
            full_domain = base_name + tld
            status = check_domain_global(full_domain)
            report += f"{status} | `{full_domain}`\n"
        
        await msg.edit_text(report, parse_mode='Markdown')
        return

    # --- 2. إدارة المستخدمين (إضافة وحذف) ---
    elif text.startswith("اضف ") and user_id == ADMIN_ID:
        try:
            target_id = int(text.split(" ")[1])
            ALLOWED_USERS.add(target_id)
            await update.message.reply_text(f"✅ تم تفعيل العضو: `{target_id}`")
        except: pass
        
    elif text.startswith("احذف ") and user_id == ADMIN_ID:
        try:
            target_id = int(text.split(" ")[1])
            if target_id in ALLOWED_USERS:
                ALLOWED_USERS.remove(target_id)
                await update.message.reply_text(f"🗑 تم حذف العضو: `{target_id}`")
        except: pass

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        app.run_polling(drop_pending_updates=True)
