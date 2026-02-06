import telebot
import whois
import random
import time
from threading import Thread
from telebot import types

# --- الإعدادات ---
API_TOKEN = '8166138523:AAGdGkcpyLTLRSeKeuKD6ofcjOFWSCjSml0'
ADMIN_ID = 665829780 # الـ ID بتاعك

bot = telebot.TeleBot(API_TOKEN)
running = False
users = set([ADMIN_ID])
scanned_domains = set() # مخزن لمنع التكرار

# --- قاموس المجالات الشامل (موضة، طب، قانون، تسويق، تقنية) ---
niches = {
    'fashion': ['cloth', 'fashion', 'style', 'wear', 'look', 'boutique', 'outfit', 'brand', 'trend'],
    'medical': ['med', 'doc', 'clinic', 'health', 'cure', 'care', 'surgery', 'lab', 'dental'],
    'legal': ['law', 'legal', 'judge', 'court', 'firm', 'advocate', 'justice', 'suit', 'case'],
    'marketing': ['ads', 'market', 'lead', 'seo', 'growth', 'brand', 'sale', 'promo', 'agency'],
    'ai_tech': ['ai', 'bot', 'data', 'cloud', 'cyber', 'tech', 'smart', 'neural', 'logic', 'web']
}
exts = ['.com', '.net', '.org', '.io', '.ai']

# --- وظيفة الفحص (نفس منطقك الموثوق) ---
def check_status(domain):
    try:
        w = whois.whois(domain)
        if not w.domain_name: return "✅ متاح تماماً"
        expiry = w.expiration_date
        if isinstance(expiry, list): expiry = expiry[0]
        if expiry:
            year = expiry.replace(tzinfo=None).year
            if year > 2027: return f"💰 سمسار ({year})"
            else: return f"❌ محجوز ({year})"
        return "❌ محجوز"
    except Exception as e:
        err = str(e).lower()
        if "no match" in err or "not found" in err: return "✅ متاح تماماً"
        return "⚠️ عطل"

# --- محرك التخمين (اللا نهائي وغير المكرر) ---
def hunting_engine():
    global running
    while True:
        if running:
            # دمج كلمات من مجالات مختلفة لتوليد ملايين الاحتمالات
            cat1 = random.choice(list(niches.keys()))
            cat2 = random.choice(list(niches.keys()))
            domain = f"{random.choice(niches[cat1])}{random.choice(niches[cat2])}{random.choice(['', '2026', 'x', 'up'])}{random.choice(exts)}"
            
            if domain not in scanned_domains:
                scanned_domains.add(domain)
                result = check_status(domain)
                
                if "✅" in result or "💰" in result:
                    for user_id in users:
                        try:
                            bot.send_message(user_id, f"🌐 {domain}\n📊 الحالة: {result}")
                        except: pass
                
                # تنظيف الذاكرة كل 10 آلاف فحص
                if len(scanned_domains) > 10000: scanned_domains.clear()
            
        time.sleep(2)

# --- الزراير (نفس اللي طلبتها بالظبط) ---
@bot.message_handler(commands=['start', 'admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add('▶️ تشغيل السكربت', '🛑 إيقاف السكربت', '➕ إضافة مستخدم', '➖ حذف مستخدم')
        bot.send_message(message.chat.id, "🎯 لوحة تحكم القناص الشامل:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    global running
    if message.chat.id != ADMIN_ID: return
    if message.text == '▶️ تشغيل السكربت':
        running = True
        bot.reply_to(message, "🚀 السكربت انطلق لفحص ملايين الدومينات (موضة، طب، قانون...)")
    elif message.text == '🛑 إيقاف السكربت':
        running = False
        bot.reply_to(message, "🛑 تم إيقاف الفحص.")
    elif message.text == '➕ إضافة مستخدم':
        msg = bot.send_message(message.chat.id, "أرسل الـ ID الجديد:")
        bot.register_next_step_handler(msg, save_user)
    elif message.text == '➖ حذف مستخدم':
        msg = bot.send_message(message.chat.id, "أرسل الـ ID لحذفه:")
        bot.register_next_step_handler(msg, delete_user)

def save_user(message):
    try:
        users.add(int(message.text))
        bot.send_message(ADMIN_ID, f"✅ تمت إضافة {message.text}")
    except: bot.send_message(ADMIN_ID, "❌ خطأ")

def delete_user(message):
    try:
        users.discard(int(message.text))
        bot.send_message(ADMIN_ID, f"🗑️ تم حذف {message.text}")
    except: pass

Thread(target=hunting_engine).start()
bot.polling(none_stop=True)
