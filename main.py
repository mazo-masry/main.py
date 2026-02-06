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
app = Flask('')

# --- المتغيرات العامة ---
running = False
users = set([ADMIN_ID])
scanned_domains = set() # لمنع التكرار نهائياً

# --- قاموس المجالات الضخم (Fashion, AI, Law, Med, Market, RealEstate) ---
niches = {
    'fashion': ['cloth', 'fashion', 'style', 'wear', 'vogue', 'trend', 'boutique', 'outfit', 'brand'],
    'ai_tech': ['ai', 'bot', 'data', 'cloud', 'cyber', 'tech', 'smart', 'neural', 'logic', 'system'],
    'marketing': ['ads', 'market', 'lead', 'seo', 'growth', 'brand', 'sale', 'promo', 'agency'],
    'legal': ['law', 'legal', 'judge', 'court', 'firm', 'advocate', 'justice', 'suit', 'case'],
    'medical': ['med', 'doc', 'clinic', 'health', 'cure', 'care', 'pharma', 'surgery', 'lab'],
    'realestate': ['home', 'villa', 'estate', 'land', 'rent', 'roof', 'yard', 'place', 'city'],
    'general': ['hub', 'base', 'flow', 'bit', 'net', 'pro', 'max', 'plus', 'top', 'x']
}

# --- وظائف التشغيل للسيرفر الوهمي (لحل مشكلة Koyeb) ---
@app.route('/')
def home(): return "Bot is Alive!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- وظيفة التوليد والفحص (طبق الأصل من السكربت الناجح) ---
def generate_domain():
    cat1 = random.choice(list(niches.keys()))
    cat2 = random.choice(list(niches.keys()))
    word1 = random.choice(niches[cat1])
    word2 = random.choice(niches[cat2])
    # إضافة لاحقة عشوائية لزيادة التنوع ومنع التكرار
    suffix = random.choice(['', '2026', 'hub', 'go', 'up', 'now', 'pro'])
    ext = random.choice(['.com', '.net', '.ai', '.io', '.org'])
    return f"{word1}{word2}{suffix}{ext}".lower()

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
                
                if len(scanned_domains) > 20000: scanned_domains.clear()
        
        time.sleep(2.5) # وقت كافي لمنع حظر الـ IP ولضمان استمرار الفحص

# --- أوامر البوت ولوحة التحكم ---
@bot.message_handler(commands=['start', 'admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add('▶️ تشغيل السكربت', '🛑 إيقاف السكربت', '➕ إضافة مستخدم', '➖ حذف مستخدم')
        bot.send_message(message.chat.id, "🎯 لوحة تحكم القناص (النسخة النهائية):", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "🚫 عذراً، الوصول للأدمن فقط.")

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    global running
    if message.chat.id != ADMIN_ID: return

    if message.text == '▶️ تشغيل السكربت':
        running = True
        bot.reply_to(message, "🚀 انطلق الوحش! يتم الآن فحص مجالات (الموضة، الطب، القانون، التقنية..)")
    
    elif message.text == '🛑 إيقاف السكربت':
        running = False
        bot.reply_to(message, "🛑 تم إيقاف الفحص.")
    
    elif message.text == '➕ إضافة مستخدم':
        msg = bot.send_message(message.chat.id, "أرسل ID المستخدم الجديد:")
        bot.register_next_step_handler(msg, save_user)
        
    elif message.text == '➖ حذف مستخدم':
        msg = bot.send_message(message.chat.id, "أرسل ID المستخدم لحذفه:")
        bot.register_next_step_handler(msg, delete_user)

def save_user(message):
    try:
        users.add(int(message.text))
        bot.send_message(ADMIN_ID, f"✅ تمت إضافة {message.text}")
    except: bot.send_message(ADMIN_ID, "❌ خطأ في الرقم")

def delete_user(message):
    try:
        users.discard(int(message.text))
        bot.send_message(ADMIN_ID, f"🗑️ تم حذف {message.text}")
    except: bot.send_message(ADMIN_ID, "❌ فشل الحذف")

# --- تشغيل الخيوط (Threads) ---
if __name__ == "__main__":
    Thread(target=run_flask).start() # تشغيل السيرفر الوهمي
    Thread(target=hunting_engine).start() # تشغيل محرك البحث
    bot.polling(none_stop=True)
