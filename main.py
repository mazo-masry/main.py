import os
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات الأساسية ---
TOKEN = os.getenv("BOT_TOKEN")

# 📋 قائمة الأشخاص المسموح لهم (القائمة البيضاء)
# قم باستبدال الـ XXXXXXXX بأرقام ID الأشخاص الذين تريد تفعيلهم
ALLOWED_USERS = {
    665829780,    # أنت (المدير) - لا تحذف هذا الرقم
    XXXXXXXX1,    # الشخص رقم 2
    XXXXXXXX2,    # الشخص رقم 3
    XXXXXXXX3,    # الشخص رقم 4
    # يمكنك إضافة حتى 100 شخص أو أكثر بنفس الطريقة (رقم ثم فاصلة)
}

def get_domain_info(domain):
    """جلب حالة الدومين وتاريخ الانتهاء بدقة"""
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
    except:
        return "خطأ في الفحص ⚠️", ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in ALLOWED_USERS:
        keyboard = [
            ['4 حروف', '5 حروف'],
            ['بحث عن متاح', 'قربت تنتهي ⏰'],
            ['كلمات مفهومة']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"🚀 أهلاً بك! جهازك مفعل بالكامل.\nاختر من القائمة للبدء في القنص:",
            reply_markup=markup
        )
    else:
        # إذا حاول شخص غير مضاف في القائمة استخدام البوت
        await update.message.reply_text(
            f"🚫 الوصول مرفوض.\nجهازك غير مضاف في قائمة الـ 100 شخص المسموح لهم.\n\n"
            f"رقم تعريفك (ID) هو: `{user_id}`\n"
            f"أرسل هذا الرقم للمدير ليقوم بإضافتك."
        )

async def handle_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # التحقق من الصلاحية قبل المعالجة
    if user_id not in ALLOWED_USERS:
        return

    msg = await update.message.reply_text("⏳ جاري البحث والتحليل...")
    
    if '4' in text or '5' in text:
        length = 4 if '4' in text else 5
        res = [''.join(random.choices(string.ascii_lowercase, k=length)) + ".com" for _ in range(8)]
        response = f"🔎 مقترحات {length} حروف:\n\n" + "\n".join(res)
        
    elif 'متاح' in text:
        found = []
        for _ in range(12):
            d = ''.join(random.choices(string.ascii_lowercase, k=5)) + ".com"
            status, _ = get_domain_info(d)
            if status == "متاح ✅":
                found.append(d)
            if len(found) >= 3: break
        response = "💎 دومينات متاحة فوراً:\n\n" + "\n".join(found) if found else "جرب البحث مرة أخرى."

    elif 'تنتهي' in text:
        expiring = []
        for _ in range(3):
            d = ''.join(random.choices(string.ascii_lowercase, k=4)) + ".com"
            status, expiry = get_domain_info(d)
            if status == "محجوز 🔒":
                expiring.append(f"⏰ {d}\n📅 تاريخ الانتهاء: {expiry}")
        response = "🔔 دومينات قاربت على الانتهاء:\n\n" + "\n\n".join(expiring)

    elif 'كلمة' in text:
        words = ["smart", "nova", "web", "fast", "pro"]
        res = [random.choice(words) + ''.join(random.choices(string.ascii_lowercase, k=2)) + ".com" for _ in range(5)]
        response = "💡 براندات مقترحة:\n\n" + "\n".join(res)
    
    else:
        response = "يرجى اختيار أمر من القائمة بالأسفل."

    await msg.edit_text(response)

if __name__ == "__main__":
    if not TOKEN:
        print("❌ خطأ: BOT_TOKEN مفقود!")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_requests))
        print("🤖 البوت يعمل بنظام القائمة البيضاء (100 شخص)...")
        app.run_polling(drop_pending_updates=True)
            d = ''.join(random.choices(string.ascii_lowercase, k=4)) + ".com"
            status, expiry = get_domain_info(d)
            if status == "محجوز 🔒":
                expiring.append(f"⏰ {d}\n📅 ينتهي: {expiry}")
        response = "🔔 دومينات قربت تنتهي:\n\n" + "\n\n".join(expiring) if expiring else "حاول مجدداً للبحث في عينة أخرى."
    
    else:
        response = "يرجى اختيار أمر من القائمة بالأسفل."

    await msg.edit_text(response)

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    
    # إضافة الأوامر والرسائل
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate_key_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
    
    print("🤖 البوت يعمل الآن بنجاح...")
    app.run_polling(drop_pending_updates=True)
