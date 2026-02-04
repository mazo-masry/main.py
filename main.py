import os
import random
import logging
import asyncio
import requests
import re
import whois
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة الأداء في Koyeb
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# الإعدادات الأساسية
TOKEN = os.getenv("BOT_TOKEN") 
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

# نظام التحكم والذاكرة الضخمة
GLOBAL_ACTIVE = False 
checked_cache = set() 

# قائمة مصادر عالمية ضخمة (يمكنك إضافة مئات الروابط هنا)
SOURCES = [
    "https://raw.githubusercontent.com/notracking/hosts-blocklists/master/domains.txt",
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
    "https://mirror.cedia.org.ec/malwaredomains/justdomains",
    "https://raw.githubusercontent.com/PolishFiltersTeam/Kolejne-domeny/master/domains.txt",
    "https://raw.githubusercontent.com/FadeMind/hosts.extras/master/add.2o7Net/hosts",
    "https://adaway.org/hosts.txt"
]

# --- فحص التوافر العميق (WHOIS) مع معالجة الأخطاء ---
async def is_available_whois(domain):
    try:
        loop = asyncio.get_event_loop()
        # تنفيذ whois في خيط منفصل لعدم تعطيل البوت
        w = await loop.run_in_executor(None, whois.whois, domain)
        if not w.domain_name or (not w.expiration_date and not w.creation_date):
            return True
        return False
    except Exception:
        return True

# --- المحرك المتوازي (The Engine) ---
async def check_domain_batch(domain, context):
    """دالة لفحص دومين واحد وإرسال إشعار إذا كان متاحاً"""
    if any(x in domain for x in ['google', 'facebook', 'apple', 'akamai', 'github', 'microsoft', 'instagram']):
        return

    try:
        # فحص DNS سريع جداً أولاً
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, socket.gethostbyname, domain)
    except Exception:
        # إذا لم يجد IP، ننتقل للفحص العميق
        if await is_available_whois(domain):
            msg = f"💎 **صيد عالمي ثمين!**\n\n🔗 الدومين: `{domain}`\n📊 إجمالي الذاكرة: {len(checked_cache)}"
            await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode='Markdown')

async def global_hunter_task(context: ContextTypes.DEFAULT_TYPE):
    global GLOBAL_ACTIVE, checked_cache
    
    while GLOBAL_ACTIVE:
        for url in SOURCES:
            if not GLOBAL_ACTIVE: break
            logger.info(f"Fetching from source: {url}")
            
            try:
                headers = {'User-Agent': f'Mozilla/5.0 (Windows 10; Win64; x64) {random.randint(1,99)}'}
                r = requests.get(f"{url}?t={time.time()}", headers=headers, timeout=20)
                
                # استخراج الدومينات بنمط Regex سريع
                found = re.findall(r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:com|net|org|io|ai|me|info|co)\b', r.text.lower())
                
                # تصفية الدومينات غير المفحوصة
                new_domains = [d for d in set(found) if d not in checked_cache]
                random.shuffle(new_domains)

                # معالجة الدومينات في مجموعات (Batches) لزيادة السرعة القصوى
                batch_size = 20 
                for i in range(0, len(new_domains), batch_size):
                    if not GLOBAL_ACTIVE: break
                    
                    batch = new_domains[i:i+batch_size]
                    tasks = []
                    for domain in batch:
                        checked_cache.add(domain)
                        tasks.append(check_domain_batch(domain, context))
                    
                    # تنفيذ الفحص المتوازي لـ 20 دومين في نفس اللحظة
                    await asyncio.gather(*tasks)
                    await asyncio.sleep(0.05) # جزء من الثانية لتجنب ضغط الشبكة

            except Exception as e:
                logger.error(f"Global Engine Error: {e}")
        
        await asyncio.sleep(5) # استراحة قصيرة جداً قبل إعادة الدورة

# --- واجهة البوت ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS: return
    
    kb = [["🚀 Global"], ["➕ إضافة مستخدم", "➖ حذف مستخدم"]]
    await update.message.reply_text(
        "⚡ **محرك القنص الموازي (Infinite Edition)**\n\n"
        "- نظام الفحص المتوازي مفعل ✅\n"
        "- الذاكرة الذكية تعمل ✅\n"
        "- جاهز لسحب ملايين الدومينات ✅", 
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GLOBAL_ACTIVE
    user_id = update.effective_user.id
    text = update.message.text
    if user_id not in ALLOWED_USERS: return

    if text == "🚀 Global":
        if not GLOBAL_ACTIVE:
            GLOBAL_ACTIVE = True
            asyncio.create_task(global_hunter_task(context))
            await update.message.reply_text("📡 تم إطلاق المحرك العالمي.. لن يتوقف الفحص حتى تضغط إيقاف.")
        else:
            GLOBAL_ACTIVE = False
            await update.message.reply_text(f"🛑 تم إيقاف المحرك.\nعدد الدومينات الفريدة المفحوصة: {len(checked_cache)}")
        return

    # إدارة المستخدمين (الأدمن فقط)
    if user_id == ADMIN_ID:
        if text == "➕ إضافة مستخدم":
            await update.message.reply_text("أرسل ID المستخدم الجديد:")
            context.user_data['state'] = 'ADD'
        elif text == "➖ حذف مستخدم":
            await update.message.reply_text("أرسل ID المستخدم للحذف:")
            context.user_data['state'] = 'DEL'
        elif context.user_data.get('state'):
            state = context.user_data['state']
            try:
                target = int(text)
                if state == 'ADD': ALLOWED_USERS.add(target)
                else: ALLOWED_USERS.discard(target)
                await update.message.reply_text(f"✅ تم تنفيذ الطلب للـ ID: {target}")
            except: await update.message.reply_text("❌ خطأ في الرقم.")
            context.user_data['state'] = None

if __name__ == "__main__":
    import socket # مطلوب للفحص السريع
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    app.run_polling()
