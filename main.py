import os
import requests
from bs4 import BeautifulSoup
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")

# هيدرز متقدمة لمحاكاة متصفح حقيقي
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.domcop.com/'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # تغيير اسم الزر كما طلبت
    kb = [['domcop']]
    await update.message.reply_text(
        "🚀 **قناص DomCop الحي**\nاضغط على الزر بالأسفل لجلب أحدث الدومينات المنتهية الآن.",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def fetch_live_domcop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = await update.message.reply_text("🔎 جاري فحص DomCop وسحب أحدث القوائم...")
    
    # رابط الصفحة التي تحتوي على الدومينات المنتهية (Expired)
    url = "https://www.domcop.com/domains/expired-domains/"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # البحث عن جدول الدومينات (الوسم المعتاد في DomCop هو جدول بمعرف معين)
        table = soup.find('table', {'id': 'expired-domains-table'}) or soup.find('table')
        
        if not table:
            await m.edit_text("⚠️ لم أتمكن من سحب الجدول حالياً. قد يكون الموقع قام بتحديث حمايته أو الصفحة فارغة.")
            return

        rows = table.find_all('tr')[1:11] # جلب أول 10 صفوف حقيقية
        
        if not rows:
            await m.edit_text("📭 لا توجد دومينات جديدة معروضة حالياً.")
            return

        report = "🎯 **أحدث الدومينات المستخرجة من DomCop:**\n\n"
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 5:
                # استخراج البيانات بناءً على ترتيب الأعمدة في DomCop
                domain = cols[0].get_text(strip=True)
                tf = cols[1].get_text(strip=True) # Trust Flow
                bl = cols[2].get_text(strip=True) # Backlinks
                da = cols[3].get_text(strip=True) # Domain Authority
                time_left = cols[-1].get_text(strip=True) # الوقت المتبقي

                report += (
                    f"🌐 **Domain:** `{domain}`\n"
                    f"🚀 **TF:** `{tf}` | 📊 **DA:** `{da}`\n"
                    f"🔗 **Backlinks:** `{bl}`\n"
                    f"⏳ **Ends in:** `{time_left}`\n"
                    f"---------------------------\n"
                )

        await m.edit_text(report, parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Error: {e}")
        await m.edit_text("❌ حدث خطأ أثناء الاتصال بالموقع. يرجى المحاولة مرة أخرى لاحقاً.")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text(['domcop']), fetch_live_domcop))
    app.run_polling()
