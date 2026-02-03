import os
import logging
import whois
import random
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة الأداء على Railway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

# قائمة المقاطع الصوتية لإنشاء أسماء سهلة النطق
PREFIXES = ["Zen", "Sky", "Nova", "Pure", "Vibe", "Flex", "Swift", "Core", "Cloud", "Luna"]
SUFFIXES = ["ly", "ify", "hub", "lab", "zone", "base", "flow", "grid", "wave", "nest"]

def generate_brandable_name():
    """توليد اسم براند احترافي سهل النطق"""
    return random.choice(PREFIXES) + random.choice(SUFFIXES)

def check_domain_status(domain):
    """فحص حالة الدومين عالمياً"""
    try:
        w = whois.whois(domain)
        if not w.domain_name:
            return "✅ متاح"
        return "🔒 محجوز"
    except:
        return "✅ متاح"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['🚀 توليد وقنص 10 براندات احترافية'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "💎 **مرحباً بك في مصنع البراندات!**\n\n"
            "هذا الإصدار يولد أسماء قصيرة، سهلة النطق، ومناسبة للمشاريع الناشئة.\n"
            "اضغط على الزر لتبدأ الماكينة في العمل.",
            reply_markup=markup, parse_mode='Markdown'
        )

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    if text == '🚀 توليد وقنص 10 براندات احترافية':
        msg = await update.message.reply_text("🏭 جاري ابتكار أسماء وفحص توفرها عالمياً...")
        
        tlds = [".com", ".net", ".io", ".xyz", ".ai"]
        final_report = "🎯 **أفضل البراندات المتاحة حالياً:**\n\n"
        
        for _ in range(10):
            brand = generate_brandable_name()
            results = []
            # فحص الاسم في أهم الامتدادات
            for tld in tlds:
                full_domain = (brand + tld).lower()
                status = check_domain_status(full_domain)
                if status == "✅ متاح":
                    results.append(tld)
            
            if results:
                final_report += f"✨ البراند: **{brand}**\n🔗 متاح في: `{', '.join(results)}`\n\n"
            
            # تأخير بسيط لتجنب حظر سيرفرات WHOIS
            time.sleep(0.5)

        await msg.edit_text(final_report, parse_mode='Markdown')

    # أزرار الإدارة
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
        app.run_polling(drop_pending_updates=True)
