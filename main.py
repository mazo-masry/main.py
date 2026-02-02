import os
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
# تم وضع رقم الـ ID الخاص بك هنا لفتح البوت لك مباشرة
ADMIN_ID = 665829780  

# تخزين المفاتيح والمستخدمين في الذاكرة
AUTHORIZED_USERS = {ADMIN_ID} 
VALID_KEYS = {} 

def generate_key():
    return "DH-" + ''.join(random.choices(string.ascii_upper + string.digits, k=10))

def get_domain_info(domain):
    try:
        res = requests.get(f"https://rdap.verisign.com/com/v1/domain/{domain}", timeout=5)
        # تقدير السعر
        val = "$500+" if len(domain.split('.')[0]) <= 4 else "$100+"
        if res.status_code == 404:
            return {"status": "متاح ✅", "expiry": "N/A", "value": val}
        data = res.json()
        expiry = next((e['eventDate'].split('T')[0] for e in data.get('events', []) if e.get('eventAction') == 'expiration'), "غير محدد")
        return {"status": "محجوز 🔒", "expiry": expiry, "value": val}
    except: return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # التحقق من الصلاحية
    if user_id in AUTHORIZED_USERS:
        keyboard = [['4 حروف', '5 حروف'], ['بحث عن متاح', 'قربت تنتهي ⏰'], ['كلمات مفهومة']]
        if user_id == ADMIN_ID:
            keyboard.append(['توليد مفتاح جديد 🔑'])
        
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"✅ تم التعرف عليك كمدير (ID: {user_id})\nكل المميزات مفتوحة الآن 🚀", reply_markup=markup)
    else:
        await update.message.reply_text("🚫 الوصول مرفوض. هذا البوت خاص، يرجى إرسال مفتاح التفعيل.")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # نظام تفعيل المفاتيح للأجهزة الأخرى
    if text.startswith("DH-"):
        if text in VALID_KEYS and VALID_KEYS[text] == "unused":
            AUTHORIZED_USERS.add(user_id)
            VALID_KEYS[text] = "used"
            await update.message.reply_text("🎉 تم تفعيل جهازك بنجاح! اضغط /start")
        else:
            await update.message.reply_text("❌ مفتاح غير صحيح أو منتهي.")
        return

    # منع غير المصرح لهم
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("⚠️ يرجى التفعيل أولاً.")
        return

    # زر توليد المفاتيح (لك أنت فقط)
    if text == 'توليد مفتاح جديد 🔑' and user_id == ADMIN_ID:
        new_key = generate_key()
        VALID_KEYS[new_key] = "unused"
        await update.message.reply_text(f"🔑 مفتاح جديد للمستخدمين:\n`{new_key}`", parse_mode='Markdown')
        return

    # تنفيذ أوامر البحث
    msg = await update.message.reply_text("⏳ جاري قنص البيانات...")
    
    if '4' in text or '5' in text:
        length = 4 if '4' in text else 5
        res = [f"{''.join(random.choice(string.ascii_lowercase) for _ in range(length))}.com" for _ in range(8)]
        response = f"🔎 مقترحات {length} حروف:\n\n" + "\n".join(res)
    elif 'متاح' in text:
        found = []
        for _ in range(15):
            d = ''.join(random.choice(string.ascii_lowercase) for _ in range(5)) + ".com"
            info = get_domain_info(d)
            if info and "متاح" in info["status"]: found.append(f"✅ {d} ({info['value']})")
            if len(found) >= 4: break
        response = "💎 متاح للتسجيل:\n\n" + "\n".join(found)
    elif 'تنتهي' in text:
        exp = []
        for _ in range(5):
            d = ''.join(random.choice(string.ascii_lowercase) for _ in range(4)) + ".com"
            info = get_domain_info(d)
            if info and "محجوز" in info["status"]: exp.append(f"⏰ {d}\n📅 ينتهي: {info['expiry']}\n")
        response = "🔔 قربت تنتهي:\n\n" + "\n".join(exp)
    else:
        response = "اختر من القائمة بالأسفل."

    await msg.edit_text(response)

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Missing BOT_TOKEN")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        print("🤖 Bot is Online for Admin 665829780")
        app.run_polling(drop_pending_updates=True)
