import os
import requests
from bs4 import BeautifulSoup
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# هيدرز محاكاة للمتصفحات
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # إضافة خيارات المواقع الجديدة
    kb = [['domcop', 'dynadot'], ['dropcatch', '🎯 أقوى الفرص']]
    await update.message.reply_text(
        "🚀 **رادار الدومينات المتعدد**\nاختر الموقع الذي تريد سحب البيانات منه الآن:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def fetch_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    m = await update.message.reply_text(f"📡 جاري الاتصال بـ {text} وسحب البيانات...")
    
    # تحديد الرابط بناءً على اختيار المستخدم
    if text == 'domcop':
        url = "https://www.domcop.com/domains/expired-domains/"
    elif text == 'dynadot':
        url = "https://www.dynadot.com/market/auction/"
    elif text == 'dropcatch':
        url = "https://www.dropcatch.com/listing/endingsoon"
    else:
        url = "https://www.domcop.com/domains/expired-domains-with-backlinks/"

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # استخراج عينة من البيانات (هذا الجزء يحاكي الهيكل البرمجي للجداول في هذه المواقع)
        # سيقوم السكربت بالبحث عن أول جدول متاح وعرض أول 10 نتائج
        table = soup.find('table')
        if not table:
            await m.edit_text(f"⚠️ الموقع {text} يطلب تسجيل دخول حالياً أو حظر الـ IP.")
            return

        rows = table.find_all('tr')[1:11]
        report = f"✨ **أحدث نتائج {text}:**\n\n"
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                domain = cols[0].get_text(strip=True)
                bl = cols[1].get_text(strip=True) if len(cols) > 1 else "N/A"
                report += f"🌐 `{domain}` | 🔗 BL: `{bl}`\n"

        await m.edit_text(report, parse_mode='Markdown')

    except Exception as e:
        await m.edit_text(f"❌ حدث خطأ أثناء السحب من {text}.")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fetch_data))
    app.run_polling()
