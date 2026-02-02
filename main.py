import os
import random
import string
import requests
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة الأخطاء في Railway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

def check_domain_availability(domain):
    try:
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
        res = requests.get(url, timeout=3)
        return "متاح ✅" if res.status_code == 404 else "محجوز 🔒"
    except Exception as e:
        logger.error(f"Error checking domain: {e}")
        return "خطأ فحص ⚠️"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['🔥 رادار الكلمات الساخنة', '💎 رادار الدومينات القصيرة'],
            ['📜 فحص العمر الذهبي', '🔔 تنبيه الصياد المخصص'],
            ['📋 قائمة المفعلين', '➕ إضافة', '➖ حذف']
        ]
        if user_id != ADMIN_ID:
            keyboard = [['🔥 رادار الكلمات الساخنة', '💎 رادار الدومينات القصيرة'], ['📜 فحص العمر الذهبي', '🔔 تنبيه الصياد المخصص']]
            
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "🚀 **البوت عاد للعمل بنجاح!**\nتم تحديث كافة الميزات. اختر أداة لبدء الاستثمار:",
            reply_markup=markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"🚫 غير مصرح لك.\nID: `{user_id}`")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # --- إدارة المستخدمين (تعمل 100%) ---
    if user_id == ADMIN_ID:
        if text.startswith("اضف "):
            try:
                new_id = int(text.split(" ")[1])
                ALLOWED_USERS.add(new_id)
                await update.message.reply_text(f"✅ تم تفعيل: `{new_id}`")
            except: await update.message.reply_text("❌ صيغة خاطئة.")
            return
        elif text.startswith("احذف "):
            try:
                del_id = int(text.split(" ")[1])
                if del_id in ALLOWED_USERS:
                    ALLOWED_USERS.remove(del_id)
                    await update.message.reply_text(f"🗑️ تم حذف: `{del_id}`")
            except: await update.message.reply_text("❌ صيغة خاطئة.")
            return
        elif text == '📋 قائمة المفعلين':
            await update.message.reply_text(f"👥 المفعلين: `{list(ALLOWED_USERS)}`")
            return

    # --- 🔥 رادار الكلمات الساخنة ---
    if text == '🔥 رادار الكلمات الساخنة':
        msg = await update.message.reply_text("🔎 جاري تحليل كلمات التريند...")
        words = ["ai", "crypto", "smart", "meta", "cyber", "green", "bio"]
        found = []
        for _ in range(10):
            d = random.choice(words) + random.choice(["lab", "fix", "hub", "node"]) + ".com"
            if check_domain_availability(d) == "متاح ✅": found.append(f"🔥 `{d}`")
            if len(found) >= 3: break
        await msg.edit_text("🎯 **دومينات تريند متاحة:**\n\n" + "\n".join(found))

    # --- 💎 رادار الدومينات القصيرة ---
    elif text == '💎 رادار الدومينات القصيرة':
        msg = await update.message.reply_text("💎 صيد الدومينات القصيرة (4-5 حروف)...")
        v = "aeiou"
        c = "bcdfghjklmnpqrstvwxyz"
        found = []
        for _ in range(15):
            d = random.choice(c) + random.choice(v) + random.choice(c) + random.choice(v) + ".com"
            if check_domain_availability(d) == "متاح ✅": found.append(f"💎 `{d}`")
            if len(found) >= 3: break
        await msg.edit_text("🎯 **دومينات قصيرة متاحة:**\n\n" + "\n".join(found))

    # --- 📜 فحص العمر الذهبي ---
    elif text == '📜 فحص العمر الذهبي':
        await update.message.reply_text("📜 أرسل اسم الدومين لفحص تاريخه (مثال: `google.com`)")

    # --- 🔔 تنبيه الصياد المخصص ---
    elif text == '🔔 تنبيه الصياد المخصص':
        await update.message.reply_text("🎯 أرسل الكلمة التي تريد صيدها وسأبحث لك عن خيارات متاحة لها.")

    # فحص عام للدومينات
    elif '.' in text:
        domain = text.lower().strip()
        status = check_domain_availability(domain)
        await update.message.reply_text(f"📊 فحص `{domain}`:\nالحالة: {status}")

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        logger.info("Bot is running...")
        app.run_polling(drop_pending_updates=True)
    else:
        logger.error("No BOT_TOKEN found!")
