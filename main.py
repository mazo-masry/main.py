import os
import random
import string
import requests
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
# قائمة لتخزين الدومينات التي يراقبها البوت (في Railway يفضل استخدام قاعدة بيانات لاحقاً)
MONITORED_DOMAINS = {}

def get_expiry_data(domain):
    try:
        res = requests.get(f"https://rdap.verisign.com/com/v1/domain/{domain}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            events = data.get("events", [])
            expiry_date = "غير محدد"
            for event in events:
                if event.get("eventAction") == "expiration":
                    expiry_date = event.get("eventDate").split("T")[0]
            return {"status": "محجوز", "expiry": expiry_date}
        return {"status": "متاح"}
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['4 حروف', '5 حروف'], ['بحث عن متاح', 'قربت تنتهي ⏰'], ['راقب دومين 🎯']]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("🎯 صائد الدومينات العبقري جاهز!\n\nيمكنك الآن مراقبة دومين معين وسأخبرك فور سقوطه.", reply_markup=markup)

async def monitor_task(context: ContextTypes.DEFAULT_TYPE):
    """دالة تعمل في الخلفية لفحص الدومينات المراقبة كل ساعة"""
    for chat_id, domains in MONITORED_DOMAINS.items():
        for domain in domains:
            data = get_expiry_data(domain)
            if data and data["status"] == "متاح":
                await context.bot.send_message(chat_id, f"🚨 عاجل: الدومين {domain} أصبح متاحاً الآن! اشترِه بسرعة!")
                MONITORED_DOMAINS[chat_id].remove(domain)

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.message.chat_id

    if 'راقب' in text:
        await update.message.reply_text("أرسل اسم الدومين الذي تريد مراقبته (مثال: example.com)")
        context.user_data['action'] = 'monitor'
        return

    if context.user_data.get('action') == 'monitor':
        domain = text.strip().lower()
        if chat_id not in MONITORED_DOMAINS: MONITORED_DOMAINS[chat_id] = []
        MONITORED_DOMAINS[chat_id].append(domain)
        context.user_data['action'] = None
        await update.message.reply_text(f"✅ تم إضافة {domain} لقائمة المراقبة. سأخبرك فور توفره.")
        return

    # ... (بقية الأكواد السابقة الخاصة بـ 4 حروف و 5 حروف ومتاح) ...
    # سيقوم البوت بتنفيذ الأوامر كما في النسخة السابقة
    await update.message.reply_text(f"جاري معالجة طلبك لـ {text}...")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    
    # تشغيل مهمة المراقبة كل 3600 ثانية (ساعة)
    job_queue = app.job_queue
    job_queue.run_repeating(monitor_task, interval=3600, first=10)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    app.run_polling(drop_pending_updates=True)
