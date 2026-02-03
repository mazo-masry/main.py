import os
import requests
from bs4 import BeautifulSoup
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# الإعدادات من متغيرات بيئة Railway
TOKEN = os.getenv("BOT_TOKEN")
EXPIRED_COOKIE = os.getenv("EXPIRED_COOKIE") # تأكد من تحديثه من المتصفح
ADMIN_ID = 665829780
allowed_users = {ADMIN_ID}

async def fetch_expired_data():
    url = "https://www.expireddomains.net/expired-domains/"
    
    # هذه الترويسات تجعل الطلب يبدو كأنه من متصفح حقيقي
    headers = {
        'authority': 'www.expireddomains.net',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9,ar;q=0.8',
        'cache-control': 'max-age=0',
        'cookie': EXPIRED_COOKIE,
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        # إذا أعطى الموقع 403 أو 429 فهذا يعني حظر IP أو Cookie
        if response.status_code == 403:
            return "🚫 **خطأ 403:** الموقع اكتشف أنك بوت. يرجى تحديث الـ Cookie من المتصفح الآن."
            
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'listing'})
        
        if not table:
            # محاولة طباعة جزء من الاستجابة في الـ Logs لمعرفة السبب
            logging.warning(f"Response snippet: {response.text[:200]}")
            return "⚠️ لم يظهر الجدول. غالباً تحتاج لتسجيل الدخول في الموقع ونسخ الـ Cookie الجديد."

        rows = table.find_all('tr')[1:]
        report = "💎 **رادار اللقطات القصيرة (محدث):**\n\n"
        found = False
        
        for row in rows[:50]:
            cols = row.find_all('td')
            if len(cols) > 0:
                domain = cols[0].get_text(strip=True)
                # فلتر الأسماء الرباعية النقية
                name_only = domain.split('.')[0]
                if len(name_only) <= 4 and name_only.isalpha():
                    bl = cols[1].get_text(strip=True)
                    report += f"✅ **لقطة:** `{domain}`\n📊 باكلينك: {bl}\n\n"
                    found = True
        
        return report if found else "🔍 لم يتم العثور على لقطات رباعية في هذه الصفحة حالياً."

    except Exception as e:
        return f"❌ خطأ فني: {str(e)}"

# ... (باقي أوامر الإدارة كما هي في السكربت السابق) ...
