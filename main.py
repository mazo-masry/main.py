import os
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")

def generate_domain(length):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length)) + ".com"

def get_domain_info(domain):
    """فحص التوافر وتاريخ الانتهاء وتقدير السعر"""
    try:
        res = requests.get(f"https://rdap.verisign.com/com/v1/domain/{domain}", timeout=5)
        
        # تقدير السعر بناءً على طول الاسم
        name_only = domain.split('.')[0]
        if len(name_only) <= 4:
            value = "$500 - $2,000"
        elif len(name_only) == 5:
            value = "$100 - $500"
        else:
            value = "$20 - $100"

        if res.status_code == 404:
            return {"status": "متاح ✅", "expiry": "N/A", "value": value}
        
        data = res.json()
        events = data.get("events", [])
        expiry = "غير محدد"
        for event in events:
            if event.get("eventAction") == "expiration":
                expiry = event.get("eventDate").split("T")[0]
        
        return {"status": "محجوز 🔒", "expiry": expiry, "value": value}
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['4 حروف', '5 حروف'], ['بحث عن متاح', 'كلمات مفهومة'], ['قربت تنتهي ⏰']]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("🚀 بوت صائد الدومينات يعمل الآن!\nاختر ما تريد من القائمة بالأسفل:", reply_markup=markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # إرسال رسالة مؤقتة لتأكيد الاستلام
    temp_msg = await update.message.reply_text("⏳ جاري المعالجة...")
    
    response = ""
    
    if '4' in text or '5' in text:
        length = 4 if '4' in text else 5
        domains = [generate_domain(length) for _ in range(8)]
        response = f"🔎 مقترحات {length} حروف:\n\n" + "\n".join(domains)

    elif 'متاح' in text:
        found = []
        for _ in range(20):
            d = generate_domain(5)
            info = get_domain_info(d)
            if info and "متاح" in info["status"]:
                found.append(f"✅ {d} (القيمة: {info['value']})")
            if len(found) >= 4: break
        response = "💎 دومينات متاحة للتسجيل:\n\n" + "\n".join(found)

    elif 'كلمة' in text:
        words = ["smart", "fast", "pro", "hub", "web", "go", "app", "bit"]
        domains = [random.choice(words) + generate_domain(2) for _ in range(6)]
        response = "💡 دومينات بكلمات مفهومة:\n\n" + "\n".join(domains)

    elif 'تنتهي' in text:
        expiring = []
        for _ in range(5):
            d = generate_domain(random.choice([4, 5]))
            info = get_domain_info(d)
            if info and "محجوز" in info["status"]:
                expiring.append(f"⏰ {d}\n📅 ينتهي: {info['expiry']}\n💰 القيمة: {info['value']}\n")
        response = "🔔 دومينات قربت تنتهي:\n\n" + "\n".join(expiring)

    else:
        response = "استخدم الأزرار الموجودة في القائمة."

    await temp_msg.edit_text(response)

if __name__ == "__main__":
    if not TOKEN:
        print("❌ الخطأ: لم يتم العثور على BOT_TOKEN")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        print("🤖 البوت شغال...")
        app.run_polling(drop_pending_updates=True)
