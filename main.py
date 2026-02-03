import os
import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة أداء Railway من لوحة التحكم (Logs)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- جلب الإعدادات من Variables ---
TOKEN = os.getenv("BOT_TOKEN")
EXPIRED_COOKIE = os.getenv("EXPIRED_COOKIE", "")
ADMIN_ID = 665829780 

# قائمة المستخدمين المسموح لهم (تبدأ بالأدمن)
allowed_users = {ADMIN_ID}

def is_premium_short(domain_name):
    """فلتر ذكي لاستخراج الدومينات الرباعية أو الثلاثية النقية"""
    name = domain_name.split('.')[0]
    # الشروط: 4 حروف أو أقل، حروف فقط (بدون أرقام أو شرطات)
    return len(name) <= 4 and name.isalpha()

async def fetch_expired_data():
    """سحب البيانات من ExpiredDomains وفلترتها"""
    url = "https://www.expireddomains.net/expired-domains/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': EXPIRED_COOKIE
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return "❌ خطأ في الاتصال بالموقع. تأكد من صحة الـ Cookie."
            
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'listing'})
        
        if not table:
            return "⚠️ لم يتم العثور على بيانات. الموقع قد يكون حظر الطلب أو الـ Cookie انتهى."

        rows = table.find_all('tr')[1:]
        report = "💎 **رادار اللقطات القصيرة (Railway Edition):**\n\n"
        found = False
        
        for row in rows[:60]: # فحص أكبر لنتائج أكثر
            cols = row.find_all('td')
            if len(cols) > 0:
                domain = cols[0].get_text(strip=True)
                if is_premium_short(domain):
                    bl = cols[1].get_text(strip=True) # الروابط الخلفية
                    report += f"✅ **لقطة:** `{domain}`\n📊 BL: {bl}\n\n"
                    found = True
        
        return report if found else "🔍 لا توجد أسماء رباعية نقية في الصفحة الأولى حالياً."
    except Exception as e:
        return f"❌ حدث خطأ: {str(e)}"

# --- معالجة الأوامر ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in allowed_users:
        keyboard = [
            ['🎯 صيد النطاقات القصيرة (LLLL)'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "🚀 **البوت يعمل على Railway بنجاح!**\n\n"
            "نظام الصيد التلقائي للأسماء الرباعية والنقية جاهز.",
            reply_markup=markup, parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in allowed_users: return

    # 1. زر الصيد
    if text == '🎯 صيد النطاقات القصيرة (LLLL)':
        msg = await update.message.reply_text("🔎 جاري تحليل البيانات من السجلات العالمية...")
        result = await fetch_expired_data()
        await msg.edit_text(result, parse_mode='Markdown')

    # 2. أزرار الإدارة (إصلاح كامل وعملي)
    elif text == '➕ إضافة مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل المعرف للإضافة: `اضف 12345`", parse_mode='Markdown')
    
    elif text.startswith("اضف ") and user_id == ADMIN_ID:
        try:
            target = int(text.split(" ")[1])
            allowed_users.add(target)
            await update.message.reply_text(f"✅ تم تفعيل: `{target}`")
        except: pass

    elif text == '➖ حذف مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل المعرف للحذف: `احذف 12345`", parse_mode='Markdown')

    elif text.startswith("احذف ") and user_id == ADMIN_ID:
        try:
            target = int(text.split(" ")[1])
            if target in allowed_users and target != ADMIN_ID:
                allowed_users.remove(target)
                await update.message.reply_text(f"🗑 تم حذف: `{target}`")
            else:
                await update.message.reply_text("❌ لم يتم العثور على المستخدم.")
        except: pass

if __name__ == "__main__":
    if not TOKEN:
        print("❌ خطأ: BOT_TOKEN غير موجود في متغيرات Railway!")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        logger.info("Bot started on Railway...")
        app.run_polling(drop_pending_updates=True)
