import os
import random
import requests
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة الأخطاء
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

# وظيفة فحص الدومين
def check_domain_availability(domain):
    try:
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
        res = requests.get(url, timeout=3)
        return "متاح ✅" if res.status_code == 404 else "محجوز 🔒"
    except:
        return "خطأ فحص ⚠️"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        # تعريف الأزرار بشكل دقيق
        keyboard = [
            ['🔥 رادار الكلمات الساخنة', '💎 رادار الدومينات القصيرة'],
            ['📜 فحص العمر الذهبي', '🔔 تنبيه الصياد المخصص'],
            ['📋 قائمة المفعلين', '➕ إضافة', '➖ حذف']
        ]
        
        # لوحة المستخدم العادي (بدون صلاحيات الإدارة)
        if user_id != ADMIN_ID:
            keyboard = [['🔥 رادار الكلمات الساخنة', '💎 رادار الدومينات القصيرة'], ['📜 فحص العمر الذهبي', '🔔 تنبيه الصياد المخصص']]
            
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "⚡ **تم تحديث وإصلاح كافة الأزرار!**\nالآن يمكنك استكشاف الدومينات الحقيقية والتريندات بسهولة.",
            reply_markup=markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"🚫 غير مصرح لك.\nID: `{user_id}`")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # التحقق من الصلاحية
    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID:
        return

    # --- 1. رادار الكلمات الساخنة (كلمات حقيقية) ---
    if text == '🔥 رادار الكلمات الساخنة':
        msg = await update.message.reply_text("🔎 جاري مسح الكلمات الأكثر بحثاً في مجالات التقنية...")
        hot_base = ["crypto", "token", "neural", "meta", "smart", "cyber", "web3", "cloud", "fast"]
        suffixes = ["hub", "lab", "base", "fix", "box", "node"]
        
        found = []
        for _ in range(12):
            domain = random.choice(hot_base) + random.choice(suffixes) + ".com"
            if check_domain_availability(domain) == "متاح ✅":
                found.append(f"🔥 `{domain}`")
            if len(found) >= 3: break
        
        await msg.edit_text("🎯 **أهداف تريند حقيقية متاحة:**\n\n" + ("\n".join(found) if found else "حاول مرة أخرى.."))

    # --- 2. رادار الدومينات القصيرة (سهلة النطق) ---
    elif text == '💎 رادار الدومينات القصيرة':
        msg = await update.message.reply_text("💎 جاري البحث عن نطاقات خماسية وسداسية جذابة...")
        parts = ["lex", "vibe", "zen", "nova", "core", "flux", "sky", "peak", "glow"]
        found = []
        for _ in range(12):
            domain = random.choice(parts) + random.choice(["ly", "io", "go", "up"]) + ".com"
            if check_domain_availability(domain) == "متاح ✅":
                found.append(f"💎 `{domain}`")
            if len(found) >= 3: break
        
        await msg.edit_text("🎯 **دومينات قصيرة وجذابة:**\n\n" + ("\n".join(found) if found else "جاري البحث.."))

    # --- 3. إدارة المستخدمين (إصلاح كامل للأوامر) ---
    elif text == '➕ إضافة':
        await update.message.reply_text("أرسل المعرف بالشكل التالي:\n`اضف 12345678`", parse_mode='Markdown')
        
    elif text == '➖ حذف':
        await update.message.reply_text("أرسل المعرف بالشكل التالي:\n`احذف 12345678`", parse_mode='Markdown')

    elif text == '📋 قائمة المفعلين':
        await update.message.reply_text(f"👥 **قائمة المستخدمين المعتمدين:**\n`{list(ALLOWED_USERS)}`", parse_mode='Markdown')

    elif text.startswith("اضف ") and user_id == ADMIN_ID:
        try:
            target_id = int(text.split(" ")[1])
            ALLOWED_USERS.add(target_id)
            await update.message.reply_text(f"✅ تم تفعيل المستخدم: `{target_id}`")
        except: await update.message.reply_text("❌ خطأ في المعرف.")

    elif text.startswith("احذف ") and user_id == ADMIN_ID:
        try:
            target_id = int(text.split(" ")[1])
            if target_id in ALLOWED_USERS and target_id != ADMIN_ID:
                ALLOWED_USERS.remove(target_id)
                await update.message.reply_text(f"🗑️ تم حذف المستخدم: `{target_id}`")
            else: await update.message.reply_text("❌ المستخدم غير موجود.")
        except: await update.message.reply_text("❌ خطأ في المعرف.")

    # --- 4. فحص الدومينات المباشر ---
    elif '.' in text:
        domain = text.lower().strip()
        status = check_domain_availability(domain)
        await update.message.reply_text(f"📊 **نتيجة فحص الدومين:**\n\nالدومين: `{domain}`\nالحالة: {status}", parse_mode='Markdown')

    # --- 5. الرسائل الأخرى (تنبيه الصياد / العمر الذهبي) ---
    elif text == '🔔 تنبيه الصياد المخصص':
        await update.message.reply_text("🎯 أرسل الكلمة التي تود البحث عنها كدومين (مثل: Dubai).")
        
    elif text == '📜 فحص العمر الذهبي':
        await update.message.reply_text("📜 أرسل اسم الدومين لفحص تاريخه وحالته.")

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        logger.info("Bot is running...")
        app.run_polling(drop_pending_updates=True)
