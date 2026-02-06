import telebot
import whois
import random
import time
from threading import Thread
from telebot import types

# --- الإعدادات الأساسية ---
API_TOKEN = 'ضع_توكن_بوت_تليجرام_هنا'
ADMIN_ID = 123456789  # ضع هنا الـ ID الخاص بك (الأدمن) لتتحكم في البوت

bot = telebot.TeleBot(API_TOKEN)

# حالات التشغيل
running = False
users = set([ADMIN_ID]) # قائمة المستخدمين المسموح لهم (تبدأ بك)

# القواميس (تأكد من إضافة كلمات كثيرة هنا لزيادة الاحتمالات)
words = ['tech', 'smart', 'fast', 'free', 'pro', 'net', 'app', 'soft', 'cloud', 'bolt', 'ai', 'go', 'web']
exts = ['.com', '.net', '.org', '.io', '.ai']

# --- وظائف الفحص (طبق الأصل من السكربت الناجح) ---
def check_status(domain):
    try:
        w = whois.whois(domain)
        if not w.domain_name:
            return "✅ متاح تماماً"
        expiry = w.expiration_date
        if isinstance(expiry, list): expiry = expiry[0]
        if expiry:
            year = expiry.replace(tzinfo=None).year
            if year > 2027: return f"💰 سمسار ({year})"
            else: return f"❌ محجوز ({year})"
        return "❌ محجوز"
    except Exception as e:
        err = str(e).lower()
        if "no match" in err or "not found" in err:
            return "✅ متاح تماماً"
        return "⚠️ عطل"

# --- محرك التخمين المستمر ---
def hunting_engine():
    global running
    while True:
        if running:
            # توليد اسم عشوائي
            domain = f"{random.choice(words)}{random.choice(words)}{random.choice(exts)}"
            result = check_status(domain)
            
            # إرسال النتائج لكل المستخدمين المضافين
            if "✅" in result or "💰" in result: # نرسل المتاح والسمسار فقط لتقليل الإزعاج
                for user_id in users:
                    try:
                        bot.send_message(user_id, f"🌐 {domain}\n📊 الحالة: {result}")
                    except: pass
            
        time.sleep(2) # تأخير بسيط لضمان استقرار السيرفر في Render

# --- لوحة التحكم والزراير ---
@bot.message_handler(commands=['start', 'admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        btn1 = types.KeyboardButton('▶️ تشغيل السكربت')
        btn2 = types.KeyboardButton('🛑 إيقاف السكربت')
        btn3 = types.KeyboardButton('➕ إضافة مستخدم')
        btn4 = types.KeyboardButton('➖ حذف مستخدم')
        markup.add(btn1, btn2, btn3, btn4)
        bot.send_message(message.chat.id, "🎯 لوحة تحكم القناص:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "عذراً، هذا البوت خاص بالأدمن فقط.")

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    global running
    if message.chat.id != ADMIN_ID: return

    if message.text == '▶️ تشغيل السكربت':
        running = True
        bot.reply_to(message, "🚀 السكربت بدأ يولد ويفحص الآن.. سيتم إرسال النتائج فور إيجادها.")
    
    elif message.text == '🛑 إيقاف السكربت':
        running = False
        bot.reply_to(message, "🛑 تم إيقاف الفحص.")
    
    elif message.text == '➕ إضافة مستخدم':
        msg = bot.send_message(message.chat.id, "أرسل الـ ID الخاص بالمستخدم الجديد:")
        bot.register_next_step_handler(msg, save_user)
        
    elif message.text == '➖ حذف مستخدم':
        msg = bot.send_message(message.chat.id, "أرسل الـ ID الذي تريد حذفه:")
        bot.register_next_step_handler(msg, delete_user)

def save_user(message):
    try:
        users.add(int(message.text))
        bot.send_message(ADMIN_ID, f"✅ تم إضافة المستخدم {message.text}")
    except: bot.send_message(ADMIN_ID, "❌ خطأ في الـ ID")

def delete_user(message):
    try:
        users.discard(int(message.text))
        bot.send_message(ADMIN_ID, f"🗑️ تم حذف المستخدم {message.text}")
    except: bot.send_message(ADMIN_ID, "❌ فشل الحذف")

# تشغيل محرك البحث في خلفية البوت
Thread(target=hunting_engine).start()

bot.polling(none_stop=True)
