import os
import requests
from bs4 import BeautifulSoup
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

# تخزين الكوكي في الذاكرة
SESSION_DATA = {"cookie": "PHPSESSID=gnLJ2C... (سيتم تحديثه)"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        kb = [['🔄 تفعيل الربط بالكوكي'], ['🆕 جلب 10 دومينات (.com)']]
        msg = "👑 **لوحة تحكم الأدمن**\nتم تجهيز البوت للعمل بنظام الجلسة (Cookie)."
    else:
        kb = [['🆕 Expired .com', '⏳ Pending Delete']]
        msg = "🌟 **مرحباً بك في بوت قناص الدومينات**\nسيتم جلب البيانات الحصرية من حساب الأدمن الموثق."
    
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID: return

    if update.message.text == '🔄 تفعيل الربط بالكوكي':
        await update.message.reply_text("📥 أرسل الكوكي الآن (الذي يبدأ بـ PHPSESSID):")
        context.user_data['state'] = 'WAIT_COOKIE'
        return

    if context.user_data.get('state') == 'WAIT_COOKIE':
        SESSION_DATA["cookie"] = update.message.text.strip()
        context.user_data['state'] = None
        await update.message.reply_text("✅ **تم الربط بنجاح!** البوت الآن يتصفح الموقع بصفتك الأدمن.")
        return

async def fetch_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ['🆕 Expired .com', '⏳ Pending Delete', '🆕 جلب 10 دومينات (.com)']:
        return

    msg = await update.message.reply_text("⏳ جاري استخراج البيانات من الحساب الشخصي...")
    
    # تحديد الرابط بناءً على اختيار المستخدم
    endpoint = "expiredcom" if ".com" in text else "pendingdelete"
    url = f"https://www.expireddomains.net/domains/{endpoint}/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Cookie': SESSION_DATA["cookie"],
        'Referer': 'https://www.expireddomains.net/'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        # التحقق إذا كان الكوكي لا يزال صالحاً
        if "Login" in response.text:
            await msg.edit_text("❌ انتهت صلاحية الكوكي. اطلب من الأدمن تحديثه.")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'listing'})
        
        if not table:
            await msg.edit_text("⚠️ لم أجد دومينات في هذا القسم حالياً.")
            return

        rows = table.find_all('tr')[1:11] # جلب أول 10 دومينات
        report = f"🎯 **أحدث 10 دومينات ({endpoint}):**\n\n"
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 5:
                domain = cols[0].get_text(strip=True)
                bl = cols[1].get_text(strip=True)  # الروابط الخلفية
                status = cols[3].get_text(strip=True) # تاريخ الحذف
                report += f"🌐 `{domain}`\n🔗 BL: {bl} | 📅 {status}\n\n"
        
        await msg.edit_text(report, parse_mode='Markdown')

    except Exception as e:
        await msg.edit_text(f"❌ خطأ تقني: {str(e)}")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin if ADMIN_ID else None))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fetch_data))
    app.run_polling()
