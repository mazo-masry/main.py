import os
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات الثابتة ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 # رقمك المسجل في لقطة الشاشة

# الذاكرة المؤقتة (ستحذف عند رسترت Railway)
AUTHORIZED_USERS = {ADMIN_ID} 
VALID_KEYS = {} 

def generate_key():
    return "DH-" + ''.join(random.choices(string.ascii_upper + string.digits, k=10))

def get_domain_info(domain):
    try:
        res = requests.get(f"https://rdap.verisign.com/com/v1/domain/{domain}", timeout=5)
        if res.status_code == 404:
            return {"status": "متاح ✅", "expiry": "N/A"}
        data = res.json()
        expiry = next((e['eventDate'].split('T')[0] for e in data.get('events', []) if e.get('eventAction') == 'expiration'), "غير محدد")
        return {"status": "محجوز 🔒", "expiry": expiry}
    except: return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in AUTHORIZED_USERS:
        # ترتيب الأزرار ليكون زر التوليد واضحاً ومنفصلاً
        keyboard = [
            ['4 حروف', '5 حروف'],
            ['بحث عن متاح', 'قربت تنتهي ⏰'],
            ['كلمات مفهومة'],
            ['توليد مفتاح جديد 🔑']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"✅ أهلاً بك يا مدير!\nاختر ما تريد من القائمة:", reply_markup=markup)
    else:
        await update.message.reply_text("🚫 الوصول مرفوض. أرسل مفتاح التفعيل الخاص بك.")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # 1. نظام تفعيل المفاتيح للأجهزة الأخرى
    if text.startswith("DH-"):
        if text in VALID_KEYS and VALID_KEYS[text] == "unused":
            AUTHORIZED_USERS.add(user_id)
            VALID_KEYS[text] = "used"
            await update.message.reply_text("🎉 تم تفعيل جهازك بنجاح! اضغط /start لاستخدام القائمة.")
        else:
            await update.message.reply_text("❌ مفتاح غير صحيح أو تم استخدامه مسبقاً.")
        return

    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("⚠️ يرجى التفعيل أولاً.")
        return

    # 2. أمر توليد المفتاح (البحث بالكلمة المفتاحية لضمان العمل)
    if 'توليد' in text and user_id == ADMIN_ID:
        new_key = generate_key()
        VALID_KEYS[new_key] = "unused"
        await update.message.reply_text(
            f"🔑 **مفتاح تفعيل جديد:**\n\n`{new_key}`\n\nأرسل هذا الكود للمستخدم الآخر لتفعيل البوت لديه.",
            parse_mode='Markdown'
        )
        return

    # 3. معالجة أوامر البحث عن الدومينات
    msg = await update.message.reply_text("⏳ جاري قنص البيانات...")
    
    if '4' in text:
        res = [f"{''.join(random.choice(string.ascii_lowercase) for _ in range(4))}.com" for _ in range(8)]
        response = "🔎 مقترحات 4 حروف:\n\n" + "\n".join(res)
    elif '5' in text:
        res = [f"{''.join(random.choice(string.ascii_lowercase) for _ in range(5))}.com" for _ in range(8)]
        response = "🔎 مقترحات 5 حروف:\n\n" + "\n".join(res)
    elif 'متاح' in text:
        found = []
        for _ in range(15):
            d = ''.join(random.choice(string.ascii_lowercase) for _ in range(5)) + ".com"
            info = get_domain_info(d)
            if info and "متاح" in info["status"]: found.append(f"✅ {d}")
            if len(found) >= 4: break
        response = "💎 دومينات متاحة حالياً:\n\n" + "\n".join(found)
    elif 'تنتهي' in text:
        exp = []
        for _ in range(5):
            d = ''.join(random.choice(string.ascii_lowercase) for _ in range(5)) + ".com"
            info = get_domain_info(d)
            if info and "محجوز" in info["status"]: exp.append(f"⏰ {d} -> ينتهي: {info['expiry']}")
        response = "🔔 دومينات قربت تنتهي:\n\n" + "\n".join(exp)
    elif 'كلمة' in text:
        words = ["smart", "swift", "meta", "vibe", "bolt"]
        res = [random.choice(words) + ''.join(random.choice(string.ascii_lowercase) for _ in range(2)) + ".com" for _ in range(5)]
        response = "💡 كلمات مفهومة مقترحة:\n\n" + "\n".join(res)
    else:
        response = "❓ لم أفهم الأمر، يرجى اختيار زر من القائمة."

    await msg.edit_text(response)

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    app.run_polling(drop_polling_updates=True)
