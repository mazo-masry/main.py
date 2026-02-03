import os
import random
import socket
import logging
import asyncio
import requests
import re
import whois
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# تأكد من وضع التوكن في إعدادات Railway باسم BOT_TOKEN
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

ALLOWED_USERS = {ADMIN_ID}
GLOBAL_ACTIVE = False 

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

# --- فحص التوافر عبر WHOIS ---
async def check_whois_async(domain):
    try:
        loop = asyncio.get_event_loop()
        w = await loop.run_in_executor(None, whois.whois, domain)
        if not w.domain_name or (not w.expiration_date and not w.creation_date):
            return True
        return False
    except:
        return True

# --- محرك القنص العالمي (الميزة الجديدة) ---
async def global_hunter_task(context: ContextTypes.DEFAULT_TYPE):
    global GLOBAL_ACTIVE
    SOURCES = [
        f"https://raw.githubusercontent.com/notracking/hosts-blocklists/master/domains.txt?t={time.time()}",
        f"https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts?t={time.time()}"
    ]
    
    while GLOBAL_ACTIVE:
        for url in SOURCES:
            if not GLOBAL_ACTIVE: break
            try:
                loop = asyncio.get_event_loop()
                r = await loop.run_in_executor(None, lambda: requests.get(url, timeout=15))
                # استخراج دومينات حقيقية بامتدادات مشهورة
                domains = re.findall(r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:com|net|org|info|biz)\b', r.text.lower())
                unique_domains = list(set(domains))
                random.shuffle(unique_domains)

                for domain in unique_domains[:100]: # فحص عينة من كل مصدر
                    if not GLOBAL_ACTIVE: break
                    
                    # استبعاد المواقع الكبرى
                    if any(x in domain for x in ['google', 'facebook', 'apple', 'akamai', 'github']): continue
                    
                    # فحص سريع للاتصال أولاً
                    try:
                        await loop.run_in_executor(None, lambda: requests.get(f"http://{domain}", timeout=2))
                    except:
                        # إذا كان الموقع لا يستجيب، نفحص WHOIS
                        if await check_whois_async(domain):
                            msg = f"🌍 **صيد عالمي متاح!**\n\n🔗 الدومين: `{domain}`\n⏳ تم الفحص عبر المحرك المتجدد."
                            await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode='Markdown')
                    
                    await asyncio.sleep(0.2) # سرعة معتدلة
            except Exception as e:
                logger.error(f"Global Hunter Error: {e}")
        
        await asyncio.sleep(60) # استراحة قبل تحديث القوائم مرة أخرى

# --- الدوال الأساسية للبوت ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS: return

    kb = [
        ["🚀 Global", "🤖 AI", "🇦🇪 استهداف الخليج 🇸🇦"],
        ["🏢 مصانع", "🍴 مطاعم", "👕 ملابس"],
        ["📦 تعبئة", "🚚 شحن", "🛵 توصيل"],
        ["🏥 مستشفيات", "➕ إضافة", "➖ حذف"]
    ]
    await update.message.reply_text("💎 **مرحباً بك في نظام القنص العالمي 2026**\nتم تحديث الأزرار وإضافة المحرك العالمي الجديد.", 
                                   reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GLOBAL_ACTIVE
    user_id = update.effective_user.id
    text = update.message.text
    if user_id not in ALLOWED_USERS: return

    # زر القنص العالمي الجديد
    if text == "🚀 Global":
        if not GLOBAL_ACTIVE:
            GLOBAL_ACTIVE = True
            asyncio.create_task(global_hunter_task(context))
            await update.message.reply_text("📡 تم تشغيل الرادار العالمي.. سأرسل لك أي دومين متاح فوراً.")
        else:
            GLOBAL_ACTIVE = False
            await update.message.reply_text("🛑 تم إيقاف الرادار العالمي.")
        return

    # إدارة المستخدمين
    if user_id == ADMIN_ID:
        if text == "➕ إضافة":
            await update.message.reply_text("أرسل ID المستخدم:")
            context.user_data['state'] = 'ADD'
            return
        elif text == "➖ حذف":
            await update.message.reply_text("أرسل ID المستخدم:")
            context.user_data['state'] = 'DEL'
            return
        
        state = context.user_data.get('state')
        if state in ['ADD', 'DEL']:
            try:
                target = int(text)
                if state == 'ADD': ALLOWED_USERS.add(target)
                else: ALLOWED_USERS.discard(target)
                await update.message.reply_text(f"✅ تم التحديث لـ {target}")
            except: await update.message.reply_text("❌ ID غير صحيح")
            context.user_data['state'] = None
            return

    # توليد البراندات (نفس منطقك القديم مع تحسين الفحص)
    category = "استهداف الخليج" if "استهداف الخليج" in text else text.split(" ")[-1]
    if category in BRAND_DATA:
        m = await update.message.reply_text(f"🔍 جاري توليد وفحص براندات {category}...")
        report = f"🎯 **مقترحات براندات ({category}):**\n\n"
        for _ in range(8):
            prefix = random.choice(["Alpha", "Smart", "Global", "Pro", "Prime"])
            base = random.choice(BRAND_DATA[category])
            ext = random.choice(EXTENSIONS) if category != "استهداف الخليج" else random.choice([".ae", ".sa", ".com"])
            domain = f"{prefix}{base}{random.randint(1,9)}".lower() + ext
            
            # فحص DNS سريع
            try:
                socket.gethostbyname(domain)
                status = "❌ محجوز"
            except:
                status = "✅ متاح"
            
            report += f"🌐 `{domain}` | {status}\n"
        
        await m.edit_text(report, parse_mode='Markdown')

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    print("Bot is Running Globally...")
    app.run_polling()
