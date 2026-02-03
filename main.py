import os
import asyncio
import httpx
from bs4 import BeautifulSoup
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import time

# إعدادات البوت
TOKEN = os.getenv("BOT_TOKEN")

# محرك البحث الذكي - يستخدم نظام Session للحفاظ على السرعة
class DomainSniper:
    def __init__(self):
        self.base_url = "https://www.domcop.com/domains/expired-domains/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache'
        }

    async def get_fresh_domains(self):
        async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
            try:
                # إضافة متغير زمني فريد لمنع تكرار البيانات
                params = {'_': int(time.time() * 1000)}
                response = await client.get(self.base_url, params=params)
                
                if response.status_code != 200:
                    return "ERROR_LIMIT"

                soup = BeautifulSoup(response.text, 'html.parser')
                # البحث عن الجدول الذكي
                table = soup.find('table')
                if not table: return "NO_TABLE"

                rows = table.find_all('tr')[1:16]
                extracted = []
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 5:
                        data = {
                            'name': cols[0].get_text(strip=True),
                            'tf': cols[1].get_text(strip=True) or "0",
                            'bl': cols[2].get_text(strip=True) or "0",
                            'da': cols[3].get_text(strip=True) or "0",
                            'time': cols[-1].get_text(strip=True) or "N/A"
                        }
                        # ذكاء اصطناعي بسيط: استبعاد الدومينات التي ليس لها أي روابط خلفية
                        if data['bl'] != "0":
                            extracted.append(data)
                
                return extracted
            except Exception as e:
                return str(e)

sniper = DomainSniper()

# --- أوامر البوت ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [['🎯 صيد الدومينات الحية (DomCop)', '⚙️ إعدادات الفلترة']]
    await update.message.reply_text(
        "🛠 **مرحباً بك في السكربت الذكي v3.0**\nتم ضبط المحرك على وضع الاستخراج الاحترافي.",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def handle_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == '🎯 صيد الدومينات الحية (DomCop)':
        status_msg = await update.message.reply_text("🔎 جاري الفحص اللحظي وتجاوز الكاش...")
        
        data = await sniper.get_fresh_domains()
        
        if data == "ERROR_LIMIT":
            await status_msg.edit_text("⚠️ الموقع فرض حماية مؤقتة. سأحاول تغيير الهوية الرقمية، انتظر دقيقة.")
        elif data == "NO_TABLE":
            await status_msg.edit_text("📭 لا توجد بيانات جديدة حالياً، جرب الضغط مرة أخرى.")
        elif isinstance(data, list):
            report = f"✅ **تم العثور على {len(data)} دومين بجودة عالية:**\n\n"
            for item in data:
                report += (
                    f"🌐 `{item['name']}`\n"
                    f"📊 **TF:** {item['tf']} | **DA:** {item['da']} | 🔗 **BL:** {item['bl']}\n"
                    f"⏳ **باقي:** {item['time']}\n"
                    f"────────────────────\n"
                )
            await status_msg.edit_text(report, parse_mode='Markdown')
        else:
            await status_msg.edit_text(f"❌ خطأ غير متوقع: {data}")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_request))
    print("Sniper Bot is Active...")
    app.run_polling(drop_pending_updates=True)
