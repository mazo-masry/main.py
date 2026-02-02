import os
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات الأساسية ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780  # معرف المدير الخاص بك (ثابت لضمان الدخول)

# الذاكرة المؤقتة للمستخدمين المفعلين والمفاتيح
AUTHORIZED_USERS = {ADMIN_ID}
VALID_KEYS = {}

def generate_key():
    """توليد مفتاح تفعيل فريد"""
    return "DH-" + ''.join(random.choices(string.ascii_upper + string.digits, k=10))

def get_domain_info(domain):
    """فحص حالة الدومين وتاريخ الانتهاء"""
    try:
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
        res = requests.get(url, timeout=5)
        if res.status_code == 404:
            return "متاح ✅", "N/A"
        
        data = res.json()
        expiry = "غير معروف"
        # استخراج تاريخ الانتهاء من بيانات RDAP
        for event in data.get("events", []):
            if event.get("eventAction") == "expiration":
                expiry = event.get("eventDate").split("T")[0]
        return "محجوز 🔒", expiry
    except:
        return "خطأ في الفحص ⚠️", ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in AUTHORIZED_USERS:
        # لوحة التحكم تظهر فقط للمفعلين
        keyboard = [
            ['4 حروف', '5 حروف'],
            ['بحث عن متاح', 'قربت تنتهي ⏰'],
            ['كلمات مفهومة'],
            ['توليد مفتاح جديد 🔑'] # الزر الذي سنقوم بمعالجته
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"✅ أهلاً بك يا مدير (ID: {user_id})\nالبوت جاهز للعمل. اختر من القائمة:",
            reply_markup=markup
        )
    else:
        await update.message.reply_text("🚫 الوصول مرفوض. يرجى إدخال مفتاح التفعيل للمتابعة.")

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # 1. التحقق من مفاتيح التفعيل للأجهزة الأخرى
    if text.startswith("DH-"):
        if text in VALID_KEYS and VALID_KEYS[text] == "unused":
            AUTHORIZED_USERS.add(user_id)
            VALID_KEYS[text] = "used"
            await update.message.reply_text("🎉 تم تفعيل جهازك بنجاح! اضغط /start لاستخدام البوت.")
        else:
            await update.message.reply_text("❌ مفتاح غير صحيح أو تم استخدامه مسبقاً.")
        return

    # 2. حماية البوت: منع غير المصرح لهم من المتابعة
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("⚠️ يرجى تفعيل البوت أولاً.")
        return

    # 3. تعديل جزئية المفتاح (المطابقة المرنة)
    if ("توليد" in text or "مفتاح" in text) and user_id == ADMIN_ID:
        new_key = generate_key()
        VALID_KEYS[new_key] = "unused"
        await update.message.reply_text(
            f"🔑 **تم إنشاء مفتاح جديد:**\n\n`{new_key}`\n\nأرسله للمستخدم المطلوب تفعيله.",
            parse_mode='Markdown'
        )
        return

    # 4. تنفيذ أوامر البحث والتحليل
    msg = await update.message.reply_text("⏳ جاري المعالجة...")
    
    if '4' in text or '5' in text:
        length = 4 if '4' in text else 5
        res = [''.join(random.choices(string.ascii_lowercase, k=length)) + ".com" for _ in range(8)]
        response = f"🔎 مقترحات {length} حروف:\n\n" + "\n".join(res)
        
    elif 'متاح' in text:
        found = []
        for _ in range(10): # فحص عدد محدود لضمان الاستقرار
            d = ''.join(random.choices(string.ascii_lowercase, k=5)) + ".com"
            status, _ = get_domain_info(d)
            if status == "متاح ✅": found.append(d)
            if len(found) >= 3: break
        response = "💎 دومينات متاحة حالياً:\n\n" + "\n".join(found) if found else "لم أجد متاحاً حالياً، جرب ثانية."

    elif 'تنتهي' in text:
        expiring = []
        for _ in range(3):
            d = ''.join(random.choices(string.ascii_lowercase, k=4)) + ".com"
            status, expiry = get_domain_info(d)
            if status == "محجوز 🔒":
                expiring.append(f"⏰ {d}\n📅 ينتهي: {expiry}")
        response = "🔔 دومينات قربت تنتهي:\n\n" + "\n\n".join(expiring)

    elif 'كلمة' in text:
        words = ["nova", "fast", "web", "smart", "go"]
        res = [random.choice(words) + ''.join(random.choices(string.ascii_lowercase, k=2)) + ".com" for _ in range(5)]
        response = "💡 دومينات بكلمات مفهومة:\n\n" + "\n".join(res)
    
    else:
        response = "يرجى اختيار أمر من القائمة بالأسفل."

    await msg.edit_text(response)

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
    print("🤖 البوت يعمل الآن بنجاح...")
    app.run_polling(drop_pending_updates=True)
