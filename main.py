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

# إعداد السجلات للمراقبة في Koyeb Logs
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# الإعدادات
TOKEN = os.getenv("BOT_TOKEN") 
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

# متغيرات التحكم والذاكرة
GLOBAL_ACTIVE = False 
checked_cache = set() # لمنع تكرار فحص نفس الدومينات

# --- فحص التوافر العميق عبر WHOIS ---
async def is_available_whois(domain):
    try:
        loop = asyncio.get_event_loop()
        w = await loop.run_in_executor(None, whois.whois, domain)
        if not w.domain_name or (not w.expiration_date and not w.creation_date):
            return True
        return False
    except:
        return True

# --- محرك القنص العالمي المطور ---
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
                # تحديث الرابط بـ Timestamp لكسر الكاش
                fetch_url = f"{url}?t={time.time()}"
                headers = {'User-Agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) {random.randint(1,99)}'}
                loop = asyncio.get_event_loop()
                r = await loop.run_in_executor(None, lambda: requests.get(fetch_url, headers=headers, timeout=20))
                
                # استخراج الدومينات
                found = re.findall(r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:com|net|org|info|biz|io|co|me)\b', r.text.lower())
                
                # تصفية الدومينات (الجديدة فقط)
                new_domains = [d for d in set(found) if d not in checked_cache]
                random.shuffle(new_domains)

                for domain in new_domains[:50]: # فحص 50 دومين جديد في كل جولة
                    if not GLOBAL_ACTIVE: break
                    
                    checked_cache.add(domain)
                    
                    # استبعاد المواقع الكبرى
                    if any(x in domain for x in ['google', 'facebook', 'apple', 'akamai', 'github', 'microsoft']):
                        continue

                    try:
                        # فحص استجابة سريع
                        await loop.run_in_executor(None, lambda: requests.get(f"http://{domain}", timeout=1.5))
                    except:
                        # الموقع ميت -> فحص WHOIS للتأكد من الملكية
                        if await is_available_whois(domain):
                            msg = f"✨ **صيد عالمي متاح!**\n\n🌐 الدومين: `{domain}`\n📊 إجمالي المفحوص: {len(checked_cache)}"
                            await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode='Markdown')
                    
                    await asyncio.sleep(0.1) 
            except Exception as e:
                logger.error(f"Source Error: {e}")
        
        await asyncio.sleep(20) # استراحة بين الدورات

# --- الدوال الأساسية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS: return

    kb = [
        ["🚀 Global"],
        ["➕ إضافة مستخدم", "➖ حذف مستخدم"]
    ]
    await update.message.reply_text("🌍 **نظام القنص العالمي - Koyeb Edition**\n\nتم تفعيل المحرك الذكي مع خاصية منع التكرار.", 
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
            await update.message.reply_text("📡 تم إطلاق الرادار العالمي.. سأرسل لك النتائج الجديدة فور العثور عليها.")
        else:
            GLOBAL_ACTIVE = False
            await update.message.reply_text(f"🛑 تم إيقاف الرادار.\nإجمالي ما تم فحصه في هذه الجلسة: {len(checked_cache)}")
        return

    # إدارة المستخدمين (Admin Only)
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
                await update.message.reply_text(f"✅ تم التحديث للـ ID: {target}")
            except: await update.message.reply_text("❌ ID غير صحيح")
            context.user_data['state'] = None
            return

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Error: BOT_TOKEN not found in environment variables!")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        print("Bot is LIVE on Koyeb...")
        app.run_polling()
