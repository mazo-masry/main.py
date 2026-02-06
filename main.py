import os
import time
import random
import whois
import telebot
from threading import Thread
from flask import Flask
from telebot import types

# --- إعدادات البوت ---
API_TOKEN = '8166138523:AAGdGkcpyLTLRSeKeuKD6ofcjOFWSCjSml0'
ADMIN_ID = 665829780  # ضع هنا الـ ID الخاص بك

bot = telebot.TeleBot(API_TOKEN)
server = Flask(__name__)

# --- المتغيرات العامة ---
running = False
users = set([ADMIN_ID])
scanned_domains = set()

# --- القواميس المتنوعة (موضة، تقنية، قانون، طب، عقارات) ---
niches = {
    'fashion': ['cloth', 'style', 'wear', 'trend', 'vogue', 'boutique', 'outfit', 'brand'],
    'ai_tech': ['ai', 'bot', 'data', 'cloud', 'cyber', 'smart', 'neural', 'logic', 'system'],
    'marketing': ['ads', 'market', 'lead', 'seo', 'growth', 'brand', 'sale', 'promo'],
    'legal': ['law', 'legal', 'judge', 'court', 'firm', 'advocate', 'justice', 'suit'],
    'medical': ['med', 'doc', 'clinic', 'health', 'cure', 'care', 'pharma', 'surgery'],
    'realestate': ['home', 'villa', 'estate', 'land', 'rent', 'roof', 'yard', 'place']
}

# --- حل مشكلة Koyeb (فتح سيرفر ويب بسيط) ---
@server.route("/")
def index():
    return "Bot is running and hunting!", 200

def run_web_server():
    # Koyeb بيستخدم بورت 8080 افتراضياً
    port = int(os.environ.get("PORT", 8080))
    server.run(host="0.0.0.0", port=port)

# --- وظيفة التوليد والفحص (منع التكرار) ---
def generate_domain():
    cat1 = random.choice(list(niches.keys()))
    cat2 = random.choice(list(niches.keys()))
    word1 = random.choice(niches[cat1])
    word2 = random.choice(niches[cat2])
    suffix = random.choice(['', '2026', 'hub', 'go', 'up', 'now', 'pro', 'x'])
    ext = random.choice(['.com', '.net', '.ai', '.io', '.org'])
    return f"{word1}{word2}{suffix}{ext}".lower()

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
        return "⚠️ عطل مؤقت"

# --- محرك البحث المستمر ---
def hunting_engine():
    global running
    while True:
        if running:
            domain = generate_domain()
            if domain not in scanned_domains:
                scanned_domains.add(domain)
                result = check_status(domain)
                if "✅" in result or "💰" in result:
                    for user_id in users:
                        try:
                            msg = f"🌐 *Domain:* `{domain}`\n📊 *Status:* {result}"
                            bot.send_message(user_id, msg, parse_mode='Markdown')
                        except: pass
                if len(scanned_domains) > 15000: scanned_domains.clear()
        time.sleep(2.5)

# --- أوامر البوت ولوحة التحكم ---
@bot.message_handler(commands=['start', 'admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add('▶️ تشغيل السكربت', '🛑 إيقاف السكربت', '➕ إضافة مستخدم', '➖ حذف مستخدم')
        bot.send_message(message.chat.id, "🎯 لوحة تحكم القناص (النسخة النهائية):", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    global running
    if message.chat.id != ADMIN_ID: return
    if message.text == '▶️ تشغيل السكربت':
        running = True
        bot.reply_to(message, "🚀 انطلق الوحش! يتم الآن فحص مجالات (الموضة، الطب، القانون، العقارات..)")
    elif message.text == '🛑 إيقاف السكربت':
        running = False
        bot.reply_to(message, "🛑 تم إيقاف الفحص.")

# --- تشغيل البوت ---
if __name__ == "__main__":
    # تشغيل سيرفر الويب في خيط منفصل
    Thread(target=run_web_server).start()
    # تشغيل محرك البحث في خيط منفصل
    Thread(target=hunting_engine).start()
    # تشغيل البوت
    bot.polling(none_stop=True)
