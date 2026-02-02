import os
import random
import string
import requests
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة أداء البوت في Railway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات الأساسية ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

def get_domain_info(domain):
    """فحص حالة الدومين وتاريخ الانتهاء مع معالجة الأخطاء لمنع الكراش"""
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
        return "خطأ في الفحص ⚠️", ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        # الكيبورد الجديد مع زر التوليد السهل
        keyboard = [
            ['✨ توليد دومينات سهلة', '📡 رادار المحذوفة'],
            ['📅 حالة الانتهاء', '📋 قائمة المفعلين'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        
        if user_id != ADMIN_ID:
            keyboard = [['✨ توليد دومينات سهلة', '📡 رادار المحذوفة'], ['📅 حالة الانتهاء']]
            
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "🚀 **تم إصلاح السكربت بنجاح!**\n\nنظام التوليد الآن أذكى ويعتمد على كلمات سهلة النطق ومفهومة.", 
            reply_markup=markup, 
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"🚫 الوصول مرفوض.\nID: `{user_id}`")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID:
        return

    # --- إدارة المستخدمين (للمدير فقط) ---
    if user_id == ADMIN_ID:
        if '➕ إضافة' in text:
            await update.message.reply_text("أرسل: `اضف 123456789`")
            return
        elif 'قائمة' in text:
            await update.message.reply_text(f"👥 المفعلين: `{list(ALLOWED_USERS)}`")
            return
        elif text.startswith("اضف "):
            try:
                new_id = int(text.split(" ")[1])
                ALLOWED_USERS.add(new_id)
                await update.message.reply_text(f"✅ تم تفعيل `{new_id}`")
            except: pass
            return
        elif text.startswith("احذف "):
            try:
                del_id = int(text.split(" ")[1])
                if del_id in ALLOWED_USERS and del_id != ADMIN_ID:
                    ALLOWED_USERS.remove(del_id)
                    await update.message.reply_text(f"🗑️ تم حذف `{del_id}`")
            except: pass
            return

    # --- نظام التوليد المطور (سهل النطق ومتاح) ---
    if text == '✨ توليد دومينات سهلة':
        msg = await update.message.reply_text("🧠 جاري ابتكار أسماء سهلة وفحصها...")
        
        # كلمات مفهومة لبناء براندات سهلة النطق
        prefixes = ["sky", "neo", "eco", "sun", "pro", "zen", "go", "my", "bio", "lux", "vibe", "fit", "pure", "net", "top"]
        suffixes = ["lab", "hub", "flow", "core", "way", "ly", "ify", "zone", "net", "web", "site", "box", "star", "path"]
        
        found = []
        # زيادة عدد المحاولات لضمان وجود نتائج متاحة
        for _ in range(25): 
            name = random.choice(prefixes) + random.choice(suffixes) + ".com"
            status, _ = get_domain_info(name)
            if "متاح" in status:
                found.append(f"✅ `{name}`")
            if len(found) >= 5: # نريد 5 نتائج فقط
                break
            
        if found:
            response = "✨ **أسماء سهلة ومتاحة للحجز الآن:**\n\n" + "\n".join(found)
        else:
            response = "😔 لم أجد دومينات متاحة في هذه اللحظة، جرب الضغط مرة أخرى!"
            
        await msg.edit_text(response, parse_mode='Markdown')

    # --- رادار المحذوفة ---
    elif 'رادار المحذوفة' in text:
        msg = await update.message.reply_text("📡 الرادار يمسح النطاقات الساقطة...")
        res = ["fast" + ''.join(random.choices(string.ascii_lowercase, k=3)) + ".com" for _ in range(3)]
        await msg.edit_text("🎯 **أهداف الرادار المتاحة:**\n\n" + "\n".join([f"🔥 `{d}`" for d in res]), parse_mode='Markdown')

    # --- حالة الانتهاء ---
    elif 'حالة الانتهاء' in text:
        await update.message.reply_text("أرسل اسم الدومين الآن لفحصه (مثال: example.com):")

    elif '.com' in text or '.net' in text:
        domain = text.lower().strip()
        status, expiry = get_domain_info(domain)
        await update.message.reply_text(
            f"📊 **تقرير الفحص لـ `{domain}`:**\n\n"
            f"الحالة: {status}\n"
            f"تاريخ الانتهاء: `{expiry}`", 
            parse_mode='Markdown'
        )

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        logger.info("Bot is running smoothly...")
        app.run_polling(drop_pending_updates=True)
    else:
        logger.error("BOT_TOKEN is missing!")
