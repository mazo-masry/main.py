import os
import requests
from bs4 import BeautifulSoup
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة Railway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
# تخزين الكوكي في الذاكرة (يفضل مستقبلاً وضعه في Database)
SESSION_DATA = {"cookie": ""}

# دالة السحب المركزية من حسابك
def fetch_domains_from_account(endpoint, limit=10):
    url = f"https://member.expireddomains.net/domains/{endpoint}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': SESSION_DATA["cookie"],
        'Referer': 'https://member.expireddomains.net/'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if "Login" in response.text or response.status_code == 403:
            return "❌ خطأ: جلسة الدخول انتهت. اطلب من الأدمن تحديث الـ Cookie."
            
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'listing'})
        if not table: return "⚠️ لا توجد بيانات حالياً في هذا القسم."

        rows = table.find_all('tr')[1:limit+1]
        results = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 5:
                results.append({
                    "domain": cols[0].get_text(strip=True),
                    "bl": cols[1].get_text(strip=True), # Backlinks
                    "status": cols[3].get_text(strip=True) # تاريخ الحذف أو الحالة
                })
        return results
    except Exception as e:
        return f"❌ خطأ تقني: {str(e)}"

# --- أوامر الأدمن ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        kb = [['⚙️ تحديث جلسة الدخول (Cookie)'], ['📊 معاينة نتائج الحساب']]
        msg = "👑 **لوحة تحكم الأدمن**\nيرجى تحديث الكوكي لضمان عمل البوت للزبائن."
    else:
        kb = [['🆕 أحدث 10 دومينات محذوفة (.com)'], ['⏳ دومينات ستنتهي قريباً']]
        msg = "🌟 **مرحباً بك في بوت قناص الدومينات**\nاختر من القائمة بالأسفل لجلب أحدث النتائج العالمية."
    
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode='Markdown')

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # --- منطق الأدمن لضبط الحساب ---
    if user_id == ADMIN_ID:
        if text == '⚙️ تحديث جلسة الدخول (Cookie)':
            await update.message.reply_text("أرسل الـ Cookie الجديد من المتصفح (Network -> Headers):")
            context.user_data['state'] = 'WAIT_COOKIE'
            return
        
        if context.user_data.get('state') == 'WAIT_COOKIE':
            SESSION_DATA["cookie"] = text
            context.user_data['state'] = None
            await update.message.reply_text("✅ تم تحديث الجلسة بنجاح! البوت الآن جاهز لخدمة الزبائن.")
            return

    # --- منطق المستخدمين (الزبائن) ---
    endpoint = ""
    title = ""
    
    if text == '🆕 أحدث 10 دومينات محذوفة (.com)':
        endpoint = "expiredcom"
        title = "🆕 أحدث دومينات .com المحذوفة"
    elif text == '⏳ دومينات ستنتهي قريباً':
        endpoint = "pendingdelete"
        title = "⏳ دومينات في مرحلة الحذف القريب"

    if endpoint:
        msg = await update.message.reply_text("⏳ جاري جلب البيانات من الحساب الخاص...")
        data = fetch_domains_from_account(endpoint)
        
        if isinstance(data, str): # في حالة وجود خطأ
            await msg.edit_text(data)
        else:
            report = f"🎯 **{title}:**\n\n"
            for item in data:
                report += f"🌐 `{item['domain']}`\n🔗 BL: `{item['bl']}` | 📅 `{item['status']}`\n\n"
            await msg.edit_text(report, parse_mode='Markdown')

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    print("Bot is running on Railway...")
    app.run_polling()
