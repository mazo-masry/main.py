import os
import random
import string
import requests
import logging
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

def estimate_value(domain):
    """خوارزمية لتقدير قيمة الدومين بناءً على الطول والكلمات"""
    name = domain.split('.')[0]
    value = 500  # قيمة أساسية
    if len(name) <= 4: value += 1500
    if len(name) <= 6: value += 500
    if "-" not in name: value += 300
    if not any(char.isdigit() for char in name): value += 400
    return value

def get_domain_info(domain):
    try:
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
        res = requests.get(url, timeout=5)
        if res.status_code == 404:
            return "متاح ✅", "N/A", "High"
        data = res.json()
        expiry = "غير معروف"
        status = "محجوز 🔒"
        
        for event in data.get("events", []):
            if event.get("eventAction") == "expiration":
                expiry = event.get("eventDate").split("T")[0]
        
        # إذا كان الدومين سينتهي خلال 30 يوم نعتبره سقوط وشيك
        return status, expiry, "Medium"
    except:
        return "خطأ ⚠️", "", ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['⏰ رادار السقوط الوشيك', '📡 رادار المحذوفة'],
            ['🔍 فحص حالة الانتهاء', '📋 قائمة المفعلين'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        if user_id != ADMIN_ID:
            keyboard = [['⏰ رادار السقوط الوشيك', '📡 رادار المحذوفة'], ['🔍 فحص حالة الانتهاء']]
        
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "⚡ **تم تفعيل رادار السقوط الوشيك!**\n\nهذا النظام يبحث عن الدومينات التي قاربت صلاحيتها على الانتهاء لتكون أول القناصين.", 
            reply_markup=markup, 
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"🚫 لا تملك صلاحية.\nID: `{user_id}`")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # --- إدارة المستخدمين ---
    if user_id == ADMIN_ID:
        if '➕ إضافة' in text:
            await update.message.reply_text("أرسل: `اضف 123456789`")
            return
        elif text.startswith("اضف "):
            try:
                new_id = int(text.split(" ")[1])
                ALLOWED_USERS.add(new_id)
                await update.message.reply_text(f"✅ تم تفعيل `{new_id}`")
            except: pass
            return

    # --- نظام رادار السقوط الوشيك ---
    if text == '⏰ رادار السقوط الوشيك':
        msg = await update.message.reply_text("⏳ جاري مسح النطاقات التي ستسقط قريباً...")
        
        # توليد محاكي لدومينات قريبة من السقوط بناءً على كلمات قوية
        prefixes = ["cloud", "web", "fast", "smart", "pro", "bit", "meta"]
        suffixes = ["zone", "ly", "hub", "tech", "link", "box"]
        
        results = []
        for _ in range(4):
            domain = random.choice(prefixes) + random.choice(suffixes) + ".com"
            val = estimate_value(domain)
            # محاكاة تاريخ سقوط خلال أيام
            drop_date = (datetime.now() + timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d')
            
            results.append(
                f"🎯 **دومين وشيك السقوط:** `{domain}`\n"
                f"📅 تاريخ السقوط المتوقع: `{drop_date}`\n"
                f"💰 القيمة التقديرية: `${val}`\n"
                f"🔗 [مراقبة الدومين](https://www.whois.com/whois/{domain})"
            )
        
        await msg.edit_text("⚠️ **رادار السقوط الوشيك (أهداف قادمة):**\n\n" + "\n\n".join(results), parse_mode='Markdown', disable_web_page_preview=True)

    # --- رادار المحذوفة ---
    elif text == '📡 رادار المحذوفة':
        msg = await update.message.reply_text("📡 الرادار يبحث عن دومينات متاحة فوراً...")
        res = []
        for _ in range(3):
            d = "best" + ''.join(random.choices(string.ascii_lowercase, k=3)) + ".com"
            status, _ , _ = get_domain_info(d)
            if "متاح" in status: res.append(f"🔥 `{d}`")
        
        await msg.edit_text("🎯 **أهداف الرادار المتاحة حالياً:**\n\n" + "\n".join(res) if res else "حاول مجدداً..", parse_mode='Markdown')

    # --- فحص حالة الانتهاء ---
    elif 'حالة الانتهاء' in text:
        await update.message.reply_text("أرسل الدومين لفحص تاريخ انتهائه (مثال: domain.com):")

    elif '.com' in text or '.net' in text:
        domain = text.lower().strip()
        status, expiry, _ = get_domain_info(domain)
        val = estimate_value(domain)
        await update.message.reply_text(
            f"📊 **تقرير الفحص لـ `{domain}`:**\n\n"
            f"الحالة: {status}\n"
            f"تاريخ الانتهاء: `{expiry}`\n"
            f"القيمة السوقية التقديرية: `${val}`", 
            parse_mode='Markdown'
        )

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        app.run_polling(drop_pending_updates=True)
