import os
import random
import socket
import logging
import threading
import yt_dlp
import requests
import re
import whois
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

ALLOWED_USERS = {ADMIN_ID}

BRAND_DATA = {
    "مصانع": ["Mfg", "Fab", "Ind", "Works", "Tech", "Line", "Forge", "Mill"],
    "مطاعم": ["Tasty", "Bite", "Chef", "Dish", "Eats", "Grill", "Foody", "Kitchen"],
    "ملابس": ["Wear", "Style", "Fit", "Vogue", "Thread", "Apparel", "Fabric"],
    "تعبئة": ["Pack", "Wrap", "Box", "Fill", "Seal", "Flow", "Case"],
    "شحن": ["Ship", "Logix", "Cargo", "Move", "Fast", "Route", "Post"],
    "توصيل": ["Dash", "Drop", "Swift", "Zoom", "Go", "Fetch", "Way"],
    "مستشفيات": ["Med", "Care", "Health", "Cure", "Clinic", "Life", "Heal"],
    "AI": ["AI", "Bot", "Neural", "Mind", "Logic", "Data", "Smart", "IQ"],
    "استهداف الخليج": ["Dubai", "DXB", "AD", "Riyadh", "KSA", "UAE", "Gulf", "Najd", "Emirates", "Elite", "Capital", "Sky", "Desert", "Pearl"]
}

EXTENSIONS = [".com", ".net", ".ai", ".io", ".live", ".store", ".tech", ".app", ".ae", ".sa"]

# --- الجزء الجديد: محرك قناص يوتيوب ---
YOUTUBE_QUERIES = ["download my mod 2013", "visit my blog 2012", "clan website link", "personal portfolio 2014"]
YOUTUBE_ACTIVE = False

def is_actually_expired(url):
    try:
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if not domain_match: return False
        domain = domain_match.group(1).lower()
        blacklist = ['youtube', 'google', 'fb.com', 't.co', 'bit.ly', 'github', 'wikipedia', 'wordpress', 'blogspot', 'mediafire']
        if any(x in domain for x in blacklist): return False

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0 Safari/537.36'}
        try:
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200: return False
        except: pass

        w = whois.whois(domain)
        if not w.domain_name or not w.expiration_date: return True
        return False
    except: return True

async def youtube_sniper_task(context: ContextTypes.DEFAULT_TYPE):
    global YOUTUBE_ACTIVE
    while YOUTUBE_ACTIVE:
        query = random.choice(YOUTUBE_QUERIES)
        ydl_opts = {'quiet': True, 'extract_flat': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                results = ydl.extract_info(f"ytsearch10:{query}", download=False)
                for entry in results['entries']:
                    if not YOUTUBE_ACTIVE: break
                    info = ydl.extract_info(entry['url'], download=False)
                    desc = info.get('description', '')
                    links = re.findall(r'(https?://[^\s]+)', desc)
                    for link in set(links):
                        if is_actually_expired(link):
                            msg = f"💎 **صيد جديد من يوتيوب!**\n\n🌐 الدومين: `{link}`\n📺 الفيديو: [اضغط هنا]({entry['url']})"
                            await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode='Markdown')
            except: pass
        time.sleep(10)

# --- الدوال الأصلية للبوت ---
def is_domain_available(domain):
    try:
        socket.gethostbyname(domain)
        return False
    except socket.gaierror:
        return True

def generate_brand(category):
    prefixes = ["Alpha", "Global", "Ultra", "Prime", "Next", "Pro", "Smart", "Ever", "Zen", "Royal", "First"]
    base = random.choice(BRAND_DATA.get(category, ["Brand"]))
    suffix = random.choice(BRAND_DATA.get(category, ["Corp"]))
    if category == "استهداف الخليج":
        name = random.choice([f"{base}{random.choice(['Group', 'Services'])}", f"{random.choice(['The', 'My'])}{base}", f"{base}{random.randint(1, 99)}"]).lower()
        ext = random.choice([".ae", ".sa", ".com"])
    else:
        name = random.choice([f"{random.choice(prefixes)}{base}", f"{base}{suffix}", f"{base}{random.randint(10, 99)}"]).lower()
        ext = random.choice(EXTENSIONS)
    return name + ext

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("🚫 الدخول ممنوع.")
        return
    kb = [
        ["🏢 مصانع", "🍴 مطاعم", "👕 ملابس"],
        ["📦 تعبئة", "🚚 شحن", "🛵 توصيل"],
        ["🏥 مستشفيات", "🤖 AI", "🇦🇪 استهداف الخليج 🇸🇦"],
        ["📺 يوتيوب", "➕ إضافة مستخدم", "➖ حذف مستخدم"]
    ]
    await update.message.reply_text("🚀 **محرك التوليد والقنص جاهز**", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global YOUTUBE_ACTIVE
    user_id = update.effective_user.id
    text = update.message.text
    if user_id not in ALLOWED_USERS: return

    if text == "📺 يوتيوب":
        if not YOUTUBE_ACTIVE:
            YOUTUBE_ACTIVE = True
            threading.Thread(target=lambda: context.application.create_task(youtube_sniper_task(context))).start()
            await update.message.reply_text("✅ تم تفعيل قناص يوتيوب في الخلفية.. سيتم إرسال النتائج فور إيجادها.")
        else:
            YOUTUBE_ACTIVE = False
            await update.message.reply_text("🛑 تم إيقاف قناص يوتيوب.")
        return

    # بقية منطق الإدارة وتوليد البراندات (لم يتغير)
    if user_id == ADMIN_ID:
        if text == "➕ إضافة مستخدم":
            await update.message.reply_text("أرسل ID:")
            context.user_data['state'] = 'ADD'
            return
        elif text == "➖ حذف مستخدم":
            await update.message.reply_text("أرسل ID:")
            context.user_data['state'] = 'DEL'
            return
        
        state = context.user_data.get('state')
        if state in ['ADD', 'DEL']:
            try:
                target = int(text)
                if state == 'ADD': ALLOWED_USERS.add(target)
                else: ALLOWED_USERS.discard(target)
                await update.message.reply_text(f"✅ تم لـ {target}")
            except: pass
            context.user_data['state'] = None
            return

    category = "استهداف الخليج" if "استهداف الخليج" in text else text.split(" ")[-1]
    if category in BRAND_DATA:
        m = await update.message.reply_text(f"🧪 فحص لـ {category}...")
        results = []
        for _ in range(10):
            domain = generate_brand(category)
            status = "✅ متاح" if is_domain_available(domain) else "❌ محجوز"
            results.append((domain, status))
        report = f"🎯 **نتائج ({category}):**\n\n"
        for d, s in results: report += f"🌐 `{d}` - {s}\n"
        await m.edit_text(report, parse_mode='Markdown')

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    print("Bot with YouTube Sniper Started...")
    app.run_polling()
