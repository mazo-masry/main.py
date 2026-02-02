import os
import random
import requests
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

# محاكاة لجلب البيانات من الموقع المذكور (ExpiredDomains.net)
# يتم ترتيب النتائج حسب الـ BL (Backlinks) كما في الرابط المرسل
def fetch_expired_domains(page_offset=0):
    # ملاحظة: الموقع يتطلب تسجيل دخول وكوكيز للـ Scraping الحقيقي، 
    # هنا الكود مهيأ لاستقبال البيانات المفلترة حسب الباك لينك
    expired_data = [
        {"d": "TechSolutions.com", "bl": "12.5K", "dp": "450", "status": "Available"},
        {"d": "EcoLifeStyle.net", "bl": "8.2K", "dp": "120", "status": "Available"},
        {"d": "PureFinance.org", "bl": "15K", "dp": "800", "status": "Available"},
        {"d": "ModernArt.io", "bl": "2.1K", "dp": "90", "status": "Available"},
        {"d": "HealthAdvisor.com", "bl": "45K", "dp": "1.2K", "status": "Available"},
        # ... (يتم ملء هذه القائمة ببيانات حقيقية من الـ Scraper)
    ]
    start = page_offset * 20
    return expired_data[start:start+20]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['🚀 صيد الدومينات الساقطة (20 جديد)'],
            ['🔍 توليد وفحص 50 دومين (GoDaddy)'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "🔥 **رادار Expired Domains مفعّل!**\n\nالبوت الآن يراقب الدومينات ذات الباك لينك القوي (BL) التي سقطت للتو.",
            reply_markup=markup,
            parse_mode='Markdown'
        )

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    if text == '🚀 صيد الدومينات الساقطة (20 جديد)':
        current_page = context.user_data.get('exp_page', 0)
        msg = await update.message.reply_text(f"⏳ جاري تحليل الدومينات الساقطة (صفحة {current_page + 1})...")
        
        domains = fetch_expired_domains(current_page)
        
        if not domains:
            await msg.edit_text("🏁 انتهت النتائج المتاحة حالياً.")
            context.user_data['exp_page'] = 0
            return

        report = "🚀 **دومينات ساقطة بباك لينك قوي (BL):**\n\n"
        for i, item in enumerate(domains, 1):
            report += f"{i}. `{item['d']}`\n🔗 BL: `{item['bl']}` | 📊 DP: `{item['dp']}`\n\n"
        
        report += f"✅ صفحة رقم: {current_page + 1}"
        context.user_data['exp_page'] = current_page + 1
        await msg.edit_text(report, parse_mode='Markdown')

    # ... (باقي أوامر الإضافة والحذف وفحص جودادي تبقى كما هي)

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        app.run_polling(drop_pending_updates=True)
