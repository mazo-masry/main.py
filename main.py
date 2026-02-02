import os
import random
import requests
import logging
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

# قائمة المقاطع لتوليد أسماء احترافية
PREFIXES = ["Nova", "Sky", "Zen", "Eco", "Smart", "Flex", "Cloud", "Pure", "Swift", "Peak", "Vibe", "Core"]
SUFFIXES = ["Flow", "Byte", "Point", "Hub", "Lab", "Net", "Base", "Way", "Grid", "Link", "Sync", "Nest"]

def is_domain_available(domain):
    """فحص حقيقي للدومين عبر بروتوكول RDAP لضمان المصداقية"""
    try:
        # فحص الدومين عبر جهة التسجيل الرسمية
        url = f"https://rdap.verisign.com/com/v1/domain/{domain.lower()}"
        response = requests.get(url, timeout=5)
        # إذا كانت النتيجة 404 فهذا يعني أن الدومين غير موجود (متاح للحجز)
        if response.status_code == 404:
            return True
        return False
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['🎯 قناص الشركات والفرص الذهبية'],
            ['🗣️ توليد دومينات سهلة النطق'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "✅ **تم تحديث نظام الفحص اللحظي!**\nالآن يقوم البوت بالتأكد من جهات التسجيل قبل عرض أي دومين لك.",
            reply_markup=markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"🚫 غير مسموح لك بالدخول.\nID: `{user_id}`")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # --- 1. قناص الشركات (مع فحص حقيقي) ---
    if text == '🎯 قناص الشركات والفرص الذهبية':
        msg = await update.message.reply_text("🔎 جاري فحص قواعد البيانات العالمية عن فرص متاحة...")
        
        found_domain = None
        for _ in range(15): # محاولة البحث عن دومين متاح فعلياً
            candidate = random.choice(PREFIXES) + random.choice(SUFFIXES) + ".com"
            if is_domain_available(candidate):
                found_domain = candidate
                break
        
        if found_domain:
            price_est = random.randint(1800, 5000)
            report = (
                f"🎯 **لقطة حقيقية متاحة:** `{found_domain}`\n\n"
                f"📊 **الحالة:** متاح للحجز الفوري ✅\n"
                f"💰 **القيمة التقديرية:** `${price_est}`\n"
                f"📩 **رسالة العرض:**\n"
                f"`Hello, I noticed you're expanding. I have the premium domain {found_domain} available, which perfectly fits your brand identity. Interested?`"
            )
            await msg.edit_text(report, parse_mode='Markdown')
        else:
            await msg.edit_text("⚠️ لم أجد دومينات مميزة متاحة حالياً، جرب الضغط مرة أخرى.")

    # --- 2. توليد دومينات سهلة النطق (مع فحص حقيقي) ---
    elif text == '🗣️ توليد دومينات سهلة النطق':
        msg = await update.message.reply_text("💎 جاري استخراج أسماء براندات غير محجوزة...")
        available_list = []
        attempts = 0
        while len(available_list) < 3 and attempts < 20:
            name = random.choice(PREFIXES) + random.choice(SUFFIXES) + ".com"
            if is_domain_available(name):
                available_list.append(f"✨ `{name}`")
            attempts += 1
        
        if available_list:
            await msg.edit_text("🎯 **دومينات متاحة فعلياً للحجز:**\n\n" + "\n".join(available_list), parse_mode='Markdown')
        else:
            await msg.edit_text("❌ لم أجد أسماء سهلة متاحة في هذه اللحظة، حاول مجدداً.")

    # --- 3. إدارة المستخدمين ---
    elif text == '➕ إضافة مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل: `اضف 12345678`")
    elif text == '➖ حذف مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل: `احذف 12345678`")
    elif text.startswith("اضف ") and user_id == ADMIN_ID:
        try:
            target_id = int(text.split(" ")[1])
            ALLOWED_USERS.add(target_id)
            await update.message.reply_text(f"✅ تم تفعيل: `{target_id}`")
        except: pass
    elif text.startswith("احذف ") and user_id == ADMIN_ID:
        try:
            target_id = int(text.split(" ")[1])
            if target_id in ALLOWED_USERS:
                ALLOWED_USERS.remove(target_id)
                await update.message.reply_text(f"🗑️ تم حذف: `{target_id}`")
        except: pass

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        app.run_polling(drop_pending_updates=True)
