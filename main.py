import os
import logging
import requests
import random
import string
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات (Logs)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- جلب التوكن من متغيرات البيئة (مناسب لـ Railway) ---
TOKEN = os.getenv("BOT_TOKEN", "8166138523:AAGTRyw29i8lvojIsyrCU3tVGWMRAteblkU")

# قائمة كلمات إنجليزية مفهومة للدمج
COMMON_WORDS = ["cool", "fast", "web", "app", "box", "link", "hub", "smart", "pro", "cloud", "tech", "nova", "zen", "bit"]

def generate_random_name(length):
    """توليد اسم عشوائي بعدد حروف محدد"""
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

def is_domain_available(domain):
    """فحص سريع لتوافر الدومين عبر بروتوكول RDAP"""
    try:
        # فحص الحالة (404 يعني غالباً متاح)
        response = requests.get(f"https://rdap.verisign.com/com/v1/domain/{domain}", timeout=5)
        return response.status_code == 404
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البداية ولوحة التحكم"""
    keyboard = [['4 حروف', '5 حروف'], ['بحث عن متاح', 'كلمات مفهومة']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🚀 أهلاً بك في بوت صائد الدومينات الذكي!\n\n"
        "اختر من القائمة أدناه أو أرسل طلبك مباشرة:",
        reply_markup=reply_markup
    )

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    msg = await update.message.reply_text("🔍 جاري الفحص والتحليل... انتظر قليلاً.")
    
    results = []
    
    # 1. طلب دومينات 4 حروف
    if '4' in text:
        for _ in range(10):
            results.append(f"{generate_random_name(4)}.com")
        response = "🔎 مقترحات لأسماء من 4 حروف:\n" + "\n".join(results)

    # 2. طلب دومينات 5 حروف
    elif '5' in text:
        for _ in range(10):
            results.append(f"{generate_random_name(5)}.com")
        response = "🔎 مقترحات لأسماء من 5 حروف:\n" + "\n".join(results)

    # 3. طلب "متاح" (فحص حقيقي)
    elif 'متاح' in text:
        found = []
        # محاولة البحث عن 3 دومينات متاحة فعلاً
        for _ in range(30): 
            name = generate_random_name(5) # الخماسي احتمالية توفره أعلى
            domain = f"{name}.com"
            if is_domain_available(domain):
                found.append(f"✅ {domain}")
            if len(found) >= 5: break
        
        if found:
            response = "💎 دومينات متاحة للشراء (تأكد من جودادي):\n\n" + "\n".join(found)
        else:
            response = "⚠️ لم أجد دومينات متاحة تماماً في هذه اللحظة، حاول مرة أخرى."

    # 4. طلب كلمات مفهومة
    elif 'كلمة' in text or 'مفهومة' in text:
        for _ in range(8):
            word = random.choice(COMMON_WORDS)
            # دمج كلمة مع حرفين عشوائيين لزيادة فرص التوفر
            name = word + generate_random_name(2)
            results.append(f"{name}.com")
        response = "💡 أسماء تعتمد على كلمات مفهومة:\n" + "\n".join(results)

    else:
        response = "عذراً، أرجو اختيار أمر من القائمة أو كتابة (4 حروف، 5 حروف، متاح، كلمات مفهومة)."

    await msg.edit_text(response)

if __name__ == "__main__":
    # تشغيل البوت
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    
    print("🤖 البوت يعمل الآن وبانتظار الأوامر...")
    application.run_polling(drop_pending_updates=True)
