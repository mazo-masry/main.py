import os
import random
import socket
import logging
import asyncio
import yt_dlp
import requests
import re
import whois
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات للمراقبة في Railway Logs
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

ALLOWED_USERS = {ADMIN_ID}
YOUTUBE_ACTIVE = False # حالة القناص

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

# --- وظائف فحص الدومينات ---
def is_domain_available(domain):
    try:
        socket.gethostbyname(domain)
        return False
    except socket.gaierror:
        return True

async def is_actually_expired(url):
    try:
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if not domain_match: return False
        domain = domain_match.group(1).lower()
        blacklist = ['youtube', 'google', 'fb.com', 't.co', 'bit.ly', 'github', 'wikipedia', 'wordpress', 'blogspot', 'mediafire']
        if any(x in domain for x in blacklist): return False

        # محاولة طلب سريعة
        try:
            loop = asyncio.get_event_loop()
            r = await loop.run_in_executor(None, lambda: requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3))
            if r.status_code == 200: return False
        except: pass

        # فحص WHOIS (تشغيله في Thread منفصل لمنع تهنيج البوت)
        try:
            w = await asyncio.get_event_loop().run_in_executor(None, whois.whois, domain)
            if not w.domain_name or not w.expiration_date: return True
        except: return True # متاح
        return False
    except: return False

# --- مهمة قناص يوتيوب (Background Task) ---
async def youtube_sniper_task(context: ContextTypes.DEFAULT_TYPE):
    global YOUTUBE_ACTIVE
    queries = ["download my mod 2013", "visit my gaming blog 2012", "my old clan site link", "check my app 2014"]
    
    while YOUTUBE_ACTIVE:
        query = random.choice(queries)
        ydl_opts = {'quiet': True, 'extract_flat': True, 'skip_download': True}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # سحب فيديوهات
                search_results = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(f"ytsearch15:{query}", download=False))
                for entry in search_results['entries']:
                    if not YOUTUBE_ACTIVE: break
                    
                    video_url = entry['url']
                    logger.info(f"🔎 Scanning video: {entry['title']}")
                    
                    info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(video_url, download=False))
                    desc = info.get('description', '')
                    links = re.findall(r'(https?://[^\s]+)', desc)
                    
                    for link in set(links):
                        if await is_actually_expired(link):
                            msg = f"💎 **لقطة يوتيوب جديدة!**\n\n🌐 الدومين: `{link}`\n📺 فيديو: [اضغط للمشاهدة]({video_url})"
                            await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Sniper Error: {e}")
        
        await asyncio.sleep(10) # انتظار بين الجولات

# --- دوال التعامل مع الرسائل ---
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
    await update.message.reply_text("🚀 **مرحباً بك في النظام المتكامل**\nاختر فئة لتوليد الدومينات أو فعل قناص يوتيوب.", 
                                   reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global YOUTUBE_ACTIVE
    user_id = update.effective_user.id
    text = update.message.text
    if user_id not in ALLOWED_USERS: return

    # زر يوتيوب
    if text == "📺 يوتيوب":
        if not YOUTUBE_ACTIVE:
            YOUTUBE_ACTIVE = True
            asyncio.create_task(youtube_sniper_task(context))
            await update.message.reply_text("✅ تم تشغيل قناص يوتيوب في الخلفية.. ستصلك الإشعارات هنا.")
        else:
            YOUTUBE_ACTIVE = False
            await update.message.reply_text("🛑 تم إيقاف القناص.")
        return

    # إدارة المستخدمين
    if user_id == ADMIN_ID:
        if text == "➕ إضافة مستخدم":
            await update.message.reply_text("أرسل ID المستخدم:")
            context.user_data['state'] = 'ADD'
            return
        elif text == "➖ حذف مستخدم":
            await update.message.reply_text("أرسل ID المستخدم:")
            context.user_data['state'] = 'DEL'
            return
        
        state = context.user_data.get('state')
        if state in ['ADD', 'DEL']:
            try:
                target = int(text)
                if state == 'ADD': ALLOWED_USERS.add(target)
                else: ALLOWED_USERS.discard(target)
                await update.message.reply_text(f"✅ تمت العملية لـ {target}")
            except: await update.message.reply_text("❌ ID غير صحيح")
            context.user_data['state'] = None
            return

    # توليد البراندات
    category = "استهداف الخليج" if "استهداف الخليج" in text else text.split(" ")[-1]
    if category in BRAND_DATA:
        m = await update.message.reply_text(f"🧪 جاري فحص 10 دومينات لـ {category}...")
        report = f"🎯 **نتائج ({category}):**\n\n"
        for _ in range(10):
            # توليد دومين (تبسيط للمثال)
            prefix = random.choice(["Alpha", "Smart", "Global", "Pro"])
            base = random.choice(BRAND_DATA[category])
            ext = random.choice(EXTENSIONS) if category != "استهداف الخليج" else random.choice([".ae", ".sa", ".com"])
            domain = f"{prefix}{base}{random.randint(1,99)}".lower() + ext
            
            status = "✅ متاح" if is_domain_available(domain) else "❌ محجوز"
            report += f"🌐 `{domain}` \n  Status: {s}\n\n".replace("s", status)
        
        await m.edit_text(report, parse_mode='Markdown')

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    print("System Started Successfully...")
    app.run_polling()
