import os
import requests
from bs4 import BeautifulSoup
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

# الكوكي المحدث بناءً على بياناتك الأخيرة
MY_COOKIE = (
    "PHPSESSID=gnLJ2C YEKFs-aYk; "
    "WicaUhzLByzwOTq7rZNyoVSTP=ZL2pjQwd05vkkSBnWIH02hfVb; "
    "4w9NAlmhgvr7EMykMSe-5gG1uT2MxLYxT9Vc5kEbWCOC=M0q3ArfR8LDRpkA5QD"
)

# قائمة المستخدمين
ALLOWED_USERS = {ADMIN_ID}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in ALLOWED_USERS:
        kb = [['🚀 جلب بيانات الصفحة الشاملة'], ['👥 إضافة مستخدم', '➖ حذف مستخدم']]
        await update.message.reply_text("✅ **متصل بحسابك**\nاضغط على الزر لجلب كل ما يظهر في صفحة Combined Expired.", 
                                       reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    else:
        await update.message.reply_text("🚫 الدخول غير مسموح.")

async def fetch_combined_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS: return

    m = await update.message.reply_text("📡 جاري محاكاة المتصفح وسحب البيانات الشاملة...")
    
    url = "https://member.expireddomains.net/domains/combinedexpired/"
    
    # محاكاة دقيقة لمتصفح Chrome 144 بناءً على بياناتك
    headers = {
        'authority': 'member.expireddomains.net',
        'method': 'GET',
        'path': '/domains/combinedexpired/',
        'scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'cookie': MY_COOKIE,
        'sec-ch-ua': '"Chromium";v="144", "Google Chrome";v="144", "Not(A:Brand";v="8"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=25)
        
        if "Login" in response.text or response.status_code == 403:
            await m.edit_text("❌ الموقع رفض الجلسة. الكوكي انتهى أو يحتاج تحديث من Chrome 144.")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'listing'})
        
        if not table:
            await m.edit_text("⚠️ لم أتمكن من العثور على الجدول. قد تكون الصفحة فارغة أو تم حظر الـ IP.")
            return

        rows = table.find_all('tr')[1:] # تخطي الهيدر
        report = "📊 **البيانات المستخرجة من الصفحة:**\n\n"
        
        for i, row in enumerate(rows, 1):
            cols = row.find_all('td')
            if len(cols) > 5:
                domain = cols[0].get_text(strip=True)
                bl = cols[1].get_text(strip=True) # Backlinks
                aby = cols[3].get_text(strip=True) # Birth Year
                status = cols[-1].get_text(strip=True) # Status
                
                line = f"{i}- `{domain}`\n🔗 BL: {bl} | 📅 Age: {aby} | 📝 {status}\n\n"
                
                if len(report) + len(line) > 4000:
                    await update.message.reply_text(report, parse_mode='Markdown')
                    report = ""
                report += line

        await update.message.reply_text(report, parse_mode='Markdown')
        await m.delete()

    except Exception as e:
        await m.edit_text(f"❌ خطأ فني: {str(e)}")

# إدارة المستخدمين
async def manage_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if update.effective_user.id != ADMIN_ID: return
    
    if "إضافة" in text:
        await update.message.reply_text("أرسل ID المستخدم:")
        context.user_data['action'] = 'add'
    elif "حذف" in text:
        await update.message.reply_text("أرسل ID المستخدم للحذف:")
        context.user_data['action'] = 'del'
    else:
        action = context.user_data.get('action')
        try:
            target_id = int(text)
            if action == 'add': ALLOWED_USERS.add(target_id)
            else: ALLOWED_USERS.discard(target_id)
            await update.message.reply_text(f"✅ تمت العملية لـ {target_id}")
        except: pass
        context.user_data['action'] = None

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex('🚀 جلب بيانات'), fetch_combined_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manage_users))
    app.run_polling()
