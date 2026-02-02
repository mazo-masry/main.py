import os
import random
import string
import requests
import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد سجلات الأخطاء لمراقبة البوت في Railway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات الأساسية ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

def check_domain_availability(domain):
    """فحص سريع للدومين مع معالجة الأخطاء لمنع الكراش"""
    try:
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
        res = requests.get(url, timeout=3)
        return "متاح ✅" if res.status_code == 404 else "محجوز 🔒"
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
            "🚀 **تم تحديث وإصلاح النظام!**\nالزراير الآن تعمل بكفاءة عالية. اختر أداة لبدء الصيد:",
            reply_markup=markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"🚫 لا تملك صلاحية.\nID: `{user_id}`")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID:
        return

    # --- 💰 نظام المزاد العكسي (مصلح) ---
    if text == '💰 نظام المزاد العكسي':
        sent_msg = await update.message.reply_text("🔎 جاري تحليل الفرص الاستثمارية...")
        
        keywords = ["pay", "coin", "tech", "web", "cloud", "law", "med"]
        prefixes = ["pro", "smart", "nova", "fast", "pure"]
        
        results = []
        for _ in range(5):
            domain = random.choice(prefixes) + random.choice(keywords) + ".com"
            status = check_domain_availability(domain)
            if status == "متاح ✅":
                price = random.randint(1200, 3500)
                results.append(f"🎯 **هدف:** `{domain}`\n💰 القيمة: `${price}`\n👥 المشتري: شركات التقنية والناشئة.")
            if len(results) >= 2: break
        
        final_text = "🚀 **نتائج المزاد العكسي:**\n\n" + ("\n\n".join(results) if results else "السوق مزدحم، حاول مجدداً.")
        await sent_msg.edit_text(final_text, parse_mode='Markdown')

    # --- 📡 رادار الأرباح (مصلح) ---
    elif text == '📡 رادار الأرباح':
        sent_msg = await update.message.reply_text("📡 جاري رصد الدومينات المربحة...")
        found = []
        for _ in range(8):
            d = "sky" + "".join(random.choices(string.ascii_lowercase, k=3)) + ".com"
            status = check_domain_availability(d)
            if status == "متاح ✅":
                found.append(f"🔥 `{d}`")
            if len(found) >= 3: break
            
        res_text = "🎯 **أهداف الربح المتاحة:**\n\n" + ("\n".join(found) if found else "لم يتم رصد أهداف حالياً.")
        await sent_msg.edit_text(res_text, parse_mode='Markdown')

    # --- ⏰ سقوط وشيك ---
    elif text == '⏰ سقوط وشيك':
        await update.message.reply_text("⏳ ميزة مراقبة السقوط قيد التحديث لتعمل ببيانات حية قريباً.")

    # --- إدارة المستخدمين (للمدير فقط) ---
    elif user_id == ADMIN_ID:
        if text.startswith("اضف "):
            try:
                new_id = int(text.split(" ")[1])
                ALLOWED_USERS.add(new_id)
                await update.message.reply_text(f"✅ تم تفعيل `{new_id}`")
            except: pass
        elif text == '📋 قائمة المفعلين':
            await update.message.reply_text(f"👥 المفعلين: `{list(ALLOWED_USERS)}`")

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        logger.info("Bot started successfully and ready for Railway.")
        app.run_polling(drop_pending_updates=True)
