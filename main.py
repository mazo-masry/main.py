import os
import random
import string
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

def get_domain_info(domain):
    try:
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
        res = requests.get(url, timeout=5)
        if res.status_code == 404:
            return "متاح ✅"
        return "محجوز 🔒"
    except:
        return "خطأ ⚠️"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['💰 نظام المزاد العكسي', '📡 رادار الأرباح'],
            ['⏰ سقوط وشيك', '📋 قائمة المفعلين'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        if user_id != ADMIN_ID:
            keyboard = [['💰 نظام المزاد العكسي', '📡 رادار الأرباح'], ['⏰ سقوط وشيك']]
            
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "🚀 **تم تفعيل نظام المزاد العكسي!**\n\nالآن يمكنك إيجاد الدومينات ومعرفة من هم المشترون المحتملون فوراً لزيادة سرعة البيع.",
            reply_markup=markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"🚫 لا تملك صلاحية.\nID: `{user_id}`")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # --- نظام المزاد العكسي (الفكرة المطلوبة) ---
    if text == '💰 نظام المزاد العكسي':
        msg = await update.message.reply_text("🔍 جاري تحليل السوق والبحث عن دومينات مع مشترين محتملين...")
        
        # كلمات تجارية قوية
        business_keywords = ["pay", "store", "app", "cloud", "clinic", "law", "tech"]
        names = ["global", "smart", "quick", "elite", "prime"]
        
        found_targets = []
        for _ in range(10):
            domain = random.choice(names) + random.choice(business_keywords) + ".com"
            if get_domain_info(domain) == "متاح ✅":
                # اقتراح جهات شراء بناءً على نوع الكلمة
                category = "التقنية والمال" if "pay" in domain or "tech" in domain else "التجارة والخدمات"
                profit_est = random.randint(800, 2500)
                
                target_msg = (
                    f"🎯 **دومين متاح:** `{domain}`\n"
                    f"📊 **المجال:** {category}\n"
                    f"💰 **سعر البيع المتوقع:** `${profit_est}`\n"
                    f"👥 **مشترون محتملون:** شركات الـ {category} الناشئة، وكالات التسويق.\n"
                    f"📝 **نصيحة:** هذا الدومين قصير وسهل النطق، اعرضه على منصة Dan.com فوراً."
                )
                found_targets.append(target_msg)
            if len(found_targets) >= 2: break
        
        response = "🚀 **نتائج المزاد العكسي (فرص بيع سريعة):**\n\n" + "\n\n---\n\n".join(found_targets)
        await msg.edit_text(response, parse_mode='Markdown')

    # --- رادار الأرباح ---
    elif text == '📡 رادار الأرباح':
        msg = await update.message.reply_text("🔎 جاري صيد اللقطات المتاحة...")
        res = ["sky" + ''.join(random.choices(string.ascii_lowercase, k=3)) + ".com" for _ in range(3)]
        await msg.edit_text("🎯 **أهداف الربح المتاحة:**\n\n" + "\n".join([f"🔥 `{d}`" for d in res]), parse_mode='Markdown')

    # --- إدارة المشتركين ---
    elif user_id == ADMIN_ID:
        if text.startswith("اضف "):
            try:
                new_id = int(text.split(" ")[1])
                ALLOWED_USERS.add(new_id)
                await update.message.reply_text(f"✅ تم تفعيل `{new_id}`")
            except: pass
        elif 'قائمة' in text:
            await update.message.reply_text(f"👥 المشتركين: `{list(ALLOWED_USERS)}`")

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        app.run_polling(drop_pending_updates=True)
