import os
import random
import string
import requests
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")

def generate_domain(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length)) + ".com"

def get_expiry_data(domain):
    """جلب معلومات الانتهاء والسعر التقريبي"""
    try:
        # بنستخدم API مجاني لجلب بيانات الـ WHOIS
        res = requests.get(f"https://rdap.verisign.com/com/v1/domain/{domain}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            # استخراج تاريخ الانتهاء من الأحداث (Events)
            events = data.get("events", [])
            expiry_date = "غير محدد"
            for event in events:
                if event.get("eventAction") == "expiration":
                    # تحويل التاريخ لشكل مفهوم
                    raw_date = event.get("eventDate")
                    expiry_date = raw_date.split("T")[0]
            
            return {"status": "محجوز", "expiry": expiry_date, "price": "مزاد (حسب جودادي)"}
        return {"status": "متاح", "expiry": "N/A", "price": "$12.99"}
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['4 حروف', '5 حروف'], ['بحث عن متاح', 'كلمات مفهومة'], ['قربت تنتهي ⏰']]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("🎯 صائد الدومينات المحترف جاهز!\nاختر نوع البحث اللي محتاجه:", reply_markup=markup)

async def handle_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    msg = await update.message.reply_text("🚀 جاري القنص والتحليل...")
    
    response = ""
    
    if '4' in text or '5' in text:
        length = 4 if '4' in text else 5
        results = [generate_domain(length) for _ in range(8)]
        response = f"🔎 مقترحات {length} حروف عشوائية:\n\n" + "\n".join(results)
        
    elif 'متاح' in text:
        found = []
        for _ in range(25):
            d = generate_domain(5)
            if get_expiry_data(d)["status"] == "متاح":
                found.append(f"✅ {d} - $12.99")
            if len(found) >= 4: break
        response = "💎 دومينات متاحة للتسجيل فوراً:\n\n" + "\n".join(found)

    elif 'قربت تنتهي' in text:
        # هنا البوت بيحاول يلاقي دومينات في مرحلة الـ Redemption أو قربت تنتهي
        expiring = []
        # محاكاة لجلب الدومينات المنتهية اليوم (يمكن ربطها بـ API متخصص لاحقاً)
        for _ in range(5):
            d = generate_domain(random.choice([4, 5]))
            info = get_expiry_data(d)
            if info and info["status"] == "محجوز":
                expiring.append(f"⏰ {d}\n📅 ينتهي في: {info['expiry']}\n💰 السعر: {info['price']}\n")
        
        response = "🔔 دومينات في مرحلة الانتهاء/المزاد:\n\n" + "\n".join(expiring)

    elif 'كلمة' in text:
        words = ["nova", "prime", "swift", "meta", "glow", "edge", "bolt", "vibe"]
        results = [random.choice(words) + generate_domain(2) for _ in range(6)]
        response = "💡 دومينات بكلمات مفهومة (براندات):\n\n" + "\n".join(results)
    
    else:
        response = "استخدم الأزرار يا بطل للوصول لأفضل النتائج."

    await msg.edit_text(response)

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_request))
    app.run_polling(drop_pending_updates=True)
