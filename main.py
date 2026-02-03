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

# إعداد السجلات للمراقبة في Railway Logs (وليس على البوت)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

ALLOWED_USERS = {ADMIN_ID}
YOUTUBE_ACTIVE = False 

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

# --- فحص الدومينات المتاحة (توليد براندات) ---
def is_domain_available(domain):
    try:
        socket.gethostbyname(domain)
        return False
    except socket.gaierror:
        return True

# --- فحص الدومينات المكسورة (يوتيوب) ---
async def is_actually_expired(url):
    try:
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if not domain_match: return False
        domain = domain_match.group(1).lower()
        
        # استبعاد المواقع المستحيل سقوطها
        blacklist = ['youtube', 'google', 'fb.com', 'facebook', 't.co', 'bit.ly', 'github', 'wikipedia', 'wordpress', 'blogspot', 'mediafire', 'mega', 'instagram', 'twitter', 'amazon', 'apple', 'microsoft']
        if any(x in domain for x in blacklist): return False

        # الخطوة 1: فحص الاستجابة (باسم متصفح حقيقي)
        try:
            loop = asyncio.get_event_loop()
            r = await loop.run_in_executor(None, lambda: requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0'}, timeout=4))
            if r.status_code < 400: return False # الموقع شغال
        except:
            pass # فشل الاتصال، قد يكون متاحاً

        # الخطوة 2: فحص WHOIS الصارم
        try:
            w = await asyncio.get_event_loop().run_in_executor(None, whois.whois, domain)
            # إذا لم يوجد تاريخ انتهاء أو لم يتم العثور على اسم الدومين في السجلات
            if not w.domain_name or (not w.expiration_date and not w.creation_date):
                return True
        except:
            return True # خطأ في WHOIS غالباً يعني أن الدومين غير مسجل
            
        return False
    except:
        return False

# --- مهمة قناص يوتيوب ---
async def youtube_sniper_task(context: ContextTypes.DEFAULT_TYPE):
    global YOUTUBE_ACTIVE
    queries = [
        "official website 2012", "download my app 2013", "visit my blogspot 2011",
        "clan site link", "portfolio website 2014", "my old gaming forum",
        "check my new project 2012", "my personal site link old"
    ]
    
    while YOUTUBE_ACTIVE:
        query = random.choice(queries)
        ydl_opts = {'quiet': True, 'extract_flat': True, 'skip_download': True}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # جلب فيديوهات أكثر لزيادة فرص الصيد
                search_results = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(f"ytsearch20:{query}", download=False))
                for entry in search_results['entries']:
                    if not YOUTUBE_ACTIVE: break
                    
                    video_url = entry['url']
                    # يطبع في الـ Logs فقط للمتابعة
                    logger.info(f"Checking: {entry['title']}")
                    
                    info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(video_url, download=False))
                    desc = info.get('description', '')
                    links = re.findall(r'(https?://[^\s]+)', desc)
                    
                    for link in set(links):
                        if await is_actually_expired(link):
                            # لا يرسل إلا الدومين المتاح فعلياً
                            msg = f"💎 **صيد ثمين متاح للشراء!**\n\n🌐 الدومين: `{link}`\n📺 المصدر: [فيديو يوتيوب]({video_url})"
                            await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Search Loop Error: {e}")
        
        await asyncio.sleep(5) # استراحة قصيرة بين الكلمات

# --- الدوال الأساسية للبوت ---
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
    await update.message.reply_text("🚀 **نظام القنص والتوليد الذكي**\nتم التعديل: القناص سيعمل بصمت ولن يرسل إلا الدومينات المتاحة فقط.", 
                                   reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global YOUTUBE_ACTIVE
    user_id = update.effective_user.id
    text = update.message.text
    if user_id not in ALLOWED_USERS: return

    # تشغيل/إيقاف القناص
    if text == "📺 يوتيوب":
        if not YOUTUBE_ACTIVE:
            YOUTUBE_ACTIVE = True
            asyncio.create_task(youtube_sniper_task(context))
            await update.message.reply_text("✅ تم تفعيل قناص يوتيوب.. سأرسل لك الدومينات المتاحة فور العثور عليها.")
        else:
            YOUTUBE_ACTIVE = False
            await update.message.reply_text("🛑 تم إيقاف القناص.")
        return

    # إدارة المستخدمين (Admin)
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
                await update.message.reply_text(f"✅ تم تنفيذ العملية لـ {target}")
            except: await update.message.reply_text("❌ خطأ في الـ ID")
            context.user_data['state'] = None
            return

    # توليد الدومينات (البراندات)
    category = "استهداف الخليج" if "استهداف الخليج" in text else text.split(" ")[-1]
    if category in BRAND_DATA:
        m = await update.message.reply_text(f"🧪 جاري فحص 10 دومينات لـ {category}...")
        report = f"🎯 **نتائج توليد براندات ({category}):**\n\n"
        for _ in range(10):
            prefix = random.choice(["Alpha", "Smart", "Global", "Pro", "Prime", "Ultra"])
            base = random.choice(BRAND_DATA[category])
            ext = random.choice(EXTENSIONS) if category != "استهداف الخليج" else random.choice([".ae", ".sa", ".com"])
            domain = f"{prefix}{base}{random.randint(1,99)}".lower() + ext
            
            status = "✅ متاح" if is_domain_available(domain) else "❌ محجوز"
            report += f"🌐 `{domain}` \n  Status: {status}\n\n"
        
        await m.edit_text(report, parse_mode='Markdown')

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    print("Bot is Running...")
    app.run_polling()
