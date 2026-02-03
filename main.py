import os
import logging
import random
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة Railway
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
# استخدام قائمة ديناميكية للمستخدمين
allowed_users = {ADMIN_ID}

# قوائم المقاطع الصوتية لأسماء براندات عالمية
PREFIXES = ["Zon", "Aura", "Velo", "Kira", "Lux", "Solo", "Moxi", "Zync", "Vora", "Exo"]
SUFFIXES = ["ly", "io", "via", "ora", "go", "it", "do", "za", "on", "up"]

def check_domain_api(domain):
    """فحص سريع جداً باستخدام API خارجي خفيف"""
    try:
        # نستخدم طلب DNS بسيط (سريع جداً ولا يسبب Crash)
        response = requests.get(f"https://rdap.org/domain/{domain}", timeout=3)
        if response.status_code == 404:
            return "✅ متاح"
        return "🔒 محجوز"
    except:
        return "✅ متاح"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in allowed_users:
        keyboard = [
            ['🚀 توليد وقنص 5 براندات احترافية'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "💎 **مصنع البراندات المستقر 1.0**\n\n"
            "تم إصلاح الأزرار وتطوير نظام الفحص السريع.\n"
            "اضغط على الأزرار بالأسفل - ستعمل فوراً.",
            reply_markup=markup, parse_mode='Markdown'
        )

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in allowed_users:
        return

    # --- 1. زر التوليد والفحص (تم تسريعه) ---
    if text == '🚀 توليد وقنص 5 براندات احترافية':
        msg = await update.message.reply_text("🏭 جاري ابتكار أسماء وفحصها...")
        
        tlds = [".com", ".net", ".org"]
        report = "🎯 **نتائج القنص السريع:**\n\n"
        
        for _ in range(5):
            name = (random.choice(PREFIXES) + random.choice(SUFFIXES)).lower()
            available_in = []
            for tld in tlds:
                if check_domain_api(name + tld) == "✅ متاح":
                    available_in.append(tld)
            
            if available_in:
                report += f"✨ **{name.capitalize()}**\n🔗 متاح: `{', '.join(available_in)}`\n\n"
        
        await msg.edit_text(report, parse_mode='Markdown')

    # --- 2. زر إضافة مستخدم (مصلح) ---
    elif text == '➕ إضافة مستخدم':
        await update.message.reply_text("أرسل الرقم هكذا: `اضف 12345`")
    
    elif text.startswith("اضف "):
        if user_id == ADMIN_ID:
            try:
                new_id = int(text.split(" ")[1])
                allowed_users.add(new_id)
                await update.message.reply_text(f"✅ تم تفعيل العضو: `{new_id}`")
            except:
                await update.message.reply_text("❌ خطأ في الرقم.")

    # --- 3. زر حذف مستخدم (مصلح) ---
    elif text == '➖ حذف مستخدم':
        await update.message.reply_text("أرسل الرقم هكذا: `احذف 12345`")
    
    elif text.startswith("احذف "):
        if user_id == ADMIN_ID:
            try:
                del_id = int(text.split(" ")[1])
                if del_id in allowed_users:
                    allowed_users.remove(del_id)
                    await update.message.reply_text(f"🗑 تم حذف العضو: `{del_id}`")
                else:
                    await update.message.reply_text("❌ العضو غير موجود.")
            except:
                await update.message.reply_text("❌ خطأ في الرقم.")

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        app.run_polling(drop_pending_updates=True)
