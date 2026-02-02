import os
import random
import string
import requests
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# تفعيل سجلات الأخطاء لمراقبة البوت في Railway
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات الأساسية ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

# قائمة المستخدمين المسموح لهم
ALLOWED_USERS = {ADMIN_ID}

def get_domain_info(domain):
    """وظيفة فحص الدومين مع معالجة الأخطاء لمنع توقف السكربت"""
    try:
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
        res = requests.get(url, timeout=5)
        if res.status_code == 404:
            return "متاح ✅", "N/A"
        data = res.json()
        expiry = "غير معروف"
        for event in data.get("events", []):
            if event.get("eventAction") == "expiration":
                expiry = event.get("eventDate").split("T")[0]
        return "محجوز 🔒", expiry
    except Exception as e:
        logger.error(f"Error checking {domain}: {e}")
        return "خطأ فحص ⚠️", ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['🎯 صيد الدومينات', '💎 قناص الثلاثي'],
            ['🔍 فحص يدوي', '📋 قائمة المفعلين'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        if user_id != ADMIN_ID:
            keyboard = [['🎯 صيد الدومينات', '💎 قناص الثلاثي'], ['🔍 فحص يدوي']]
            
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("🎯 **تم تشغيل نظام القناص بنجاح!**\nالبوت مستقر الآن وجاهز للصيد.", reply_markup=markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(f"🚫 غير مسموح لك.\nID: `{user_id}`")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # --- إدارة المستخدمين (للمدير فقط) ---
    if user_id == ADMIN_ID:
        if '➕ إضافة' in text:
            await update.message.reply_text("أرسل: `اضف 123456789`")
            return
        elif 'حذف' in text:
            await update.message.reply_text("أرسل: `احذف 123456789`")
            return
        elif 'قائمة' in text:
            await update.message.reply_text(f"👥 المفعلين: `{list(ALLOWED_USERS)}`")
            return
        elif text.startswith("اضف "):
            try:
                new_id = int(text.split(" ")[1])
                ALLOWED_USERS.add(new_id)
                await update.message.reply_text(f"✅ تم تفعيل `{new_id}`")
            except: await update.message.reply_text("❌ خطأ في الرقم")
            return
        elif text.startswith("احذف "):
            try:
                del_id = int(text.split(" ")[1])
                if del_id in ALLOWED_USERS and del_id != ADMIN_ID:
                    ALLOWED_USERS.remove(del_id)
                    await update.message.reply_text(f"🗑️ تم حذف `{del_id}`")
            except: pass
            return

    # --- حماية البوت ---
    if user_id not in ALLOWED_USERS:
        return

    # --- خيارات القنص ---
    if 'صيد الدومينات' in text:
        msg = await update.message.reply_text("📡 جاري البحث عن لقطات...")
        prefixes = ["pro", "top", "my", "fast", "go"]
        keywords = ["tech", "web", "app", "hub", "site"]
        results = []
        for _ in range(4):
            d = random.choice(prefixes) + random.choice(keywords) + ".com"
            status, _ = get_domain_info(d)
            if "متاح" in status:
                results.append(f"🔥 `{d}`\n🔗 [قنص الآن](https://www.namecheap.com/domains/registration/results/?domain={d})")
        
        await msg.edit_text("🎯 **دومينات متاحة للصيد:**\n\n" + ("\n\n".join(results) if results else "حاول مجدداً للبحث عن أهداف جديدة."), parse_mode='Markdown', disable_web_page_preview=True)

    elif 'قناص الثلاثي' in text:
        msg = await update.message.reply_text("💎 جاري قنص الثلاثي...")
        chars = string.ascii_lowercase + string.digits
        found = []
        for _ in range(5):
            d = ''.join(random.choices(chars, k=3)) + ".com"
            status, _ = get_domain_info(d)
            if "متاح" in status: found.append(f"💎 `{d}`")
        await msg.edit_text("🎯 **أهداف ثلاثية متاحة:**\n\n" + "\n".join(found) if found else "لم أجد أهدافاً حالياً.", parse_mode='Markdown')

    elif '.com' in text:
        status, expiry = get_domain_info(text.lower().strip())
        await update.message.reply_text(f"📊 **تقرير الفحص:**\n\n🌐 `{text}`\nالحالة: {status}\nالانتهاء: `{expiry}`", parse_mode='Markdown')

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        logger.info("Bot started successfully...")
        app.run_polling(drop_pending_updates=True)
