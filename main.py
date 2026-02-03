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

# الإعدادات الأساسية
TOKEN = os.getenv("BOT_TOKEN") # تأكد من ضبطه في Railway
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}
GLOBAL_ACTIVE = False 
checked_cache = set() # ذاكرة الدومينات المفحوصة

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

# --- فحص التوافر العميق ---
async def is_available_whois(domain):
    try:
        loop = asyncio.get_event_loop()
        w = await loop.run_in_executor(None, whois.whois, domain)
        if not w.domain_name or (not w.expiration_date and not w.creation_date):
            return True
        return False
    except:
        return True

# --- محرك القنص العالمي الذكي ---
async def global_hunter_task(context: ContextTypes.DEFAULT_TYPE):
    global GLOBAL_ACTIVE, checked_cache
    SOURCES = [
        "https://raw.githubusercontent.com/notracking/hosts-blocklists/master/domains.txt",
        "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
        "https://mirror.cedia.org.ec/malwaredomains/justdomains"
    ]
    
    while GLOBAL_ACTIVE:
        for url in SOURCES:
            if not GLOBAL_ACTIVE: break
            try:
                # إضافة Timestamp لكسر الكاش وجلب بيانات جديدة
                fetch_url = f"{url}?t={time.time()}"
                loop = asyncio.get_event_loop()
                headers = {'User-Agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) {random.randint(1,99)}'}
                r = await loop.run_in_executor(None, lambda: requests.get(fetch_url, headers=headers, timeout=20))
                
                # استخراج الدومينات
                found = re.findall(r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:com|net|org|info|biz|io|co|me)\b', r.text.lower())
                
                # تصفية الدومينات (الجديدة فقط والتي ليست في القائمة السوداء)
                new_domains = [d for d in set(found) if d not in checked_cache]
                random.shuffle(new_domains)

                for domain in new_domains[:50]: # فحص 50 جديد من كل مصدر في الدورة
                    if not GLOBAL_ACTIVE: break
                    
                    checked_cache.add(domain) # تسجيله في الذاكرة فوراً
                    
                    if any(x in domain for x in ['google', 'facebook', 'apple', 'akamai', 'github', 'microsoft']):
                        continue

                    try:
                        # فحص استجابة سريع
                        await loop.run_in_executor(None, lambda: requests.get(f"http://{domain}", timeout=1.5))
                    except:
                        # الموقع ميت -> فحص WHOIS
                        if await is_available_whois(domain):
                            msg = f"🌍 **صيد عالمي جديد!**\n\n🔗 الدومين: `{domain}`\n📊 حالة الذاكرة: فحصت {len(checked_cache)} دومين."
                            await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode='Markdown')
                    
                    await asyncio.sleep(0.1) 
            except Exception as e:
                logger.error(f"Global Source Error: {e}")
        
        await asyncio.sleep(10) # انتظار قصير قبل الجولة التالية

# --- الدوال الأساسية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS: return

    kb = [
        ["🚀 Global", "🤖 AI", "🇦🇪 استهداف الخليج 🇸🇦"],
        ["🏢 مصانع", "🍴 مطاعم", "👕 ملابس"],
        ["📦 تعبئة", "🚚 شحن", "🛵 توصيل"],
        ["🏥 مستشفيات", "➕ إضافة", "➖ حذف"]
    ]
    await update.message.reply_text("🚀 **بوت القنص العالمي المطور 2026**\n\n- تم تفعيل نظام الذاكرة الذكية.\n- تم حذف زر يوتيوب وتعديل المحرك العالمي.", 
                                   reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GLOBAL_ACTIVE, checked_cache
    user_id = update.effective_user.id
    text = update.message.text
    if user_id not in ALLOWED_USERS: return

    if text == "🚀 Global":
        if not GLOBAL_ACTIVE:
            GLOBAL_ACTIVE = True
            asyncio.create_task(global_hunter_task(context))
            await update.message.reply_text(f"📡 تم إطلاق الرادار العالمي..\n- تم تصفير الذاكرة السابقة لضمان صيد جديد.")
        else:
            GLOBAL_ACTIVE = False
            await update.message.reply_text(f"🛑 تم إيقاف الرادار.\n- إجمالي ما تم فحصه: {len(checked_cache)}")
        return

    # إدارة المستخدمين
    if user_id == ADMIN_ID:
        if text == "➕ إضافة":
            await update.message.reply_text("أرسل ID المستخدم الجديد:")
            context.user_data['state'] = 'ADD'
            return
        elif text == "➖ حذف":
            await update.message.reply_text("أرسل ID المستخدم للحذف:")
            context.user_data['state'] = 'DEL'
            return
        
        state = context.user_data.get('state')
        if state in ['ADD', 'DEL']:
            try:
                target = int(text)
                if state == 'ADD': ALLOWED_USERS.add(target)
                else: ALLOWED_USERS.discard(target)
                await update.message.reply_text(f"✅ تم تنفيذ الإجراء للـ ID: {target}")
            except: await update.message.reply_text("❌ خطأ في الرقم المرسل.")
            context.user_data['state'] = None
            return

    # توليد البراندات
    category = "استهداف الخليج" if "استهداف الخليج" in text else text.split(" ")[-1]
    if category in BRAND_DATA:
        m = await update.message.reply_text(f"🧪 جاري توليد براندات لـ {category}...")
        report = f"🎯 **نتائج توليد {category}:**\n\n"
        for _ in range(8):
            prefix = random.choice(["Alpha", "Smart", "Global", "Pro", "Prime"])
            base = random.choice(BRAND_DATA[category])
            ext = random.choice(EXTENSIONS) if category != "استهداف الخليج" else random.choice([".ae", ".sa", ".com"])
            domain = f"{prefix}{base}{random.randint(1,9)}".lower() + ext
            
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
    print("Bot is LIVE and Global...")
    app.run_polling()
