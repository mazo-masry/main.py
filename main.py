import os
import requests
from bs4 import BeautifulSoup
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمتابعة البوت على Railway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

# مخزن الجلسة (سيتم تحديثه عبر البوت)
SESSION_DATA = {"cookie": ""}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        kb = [['⚙️ تحديث الكوكي (الربط)'], ['🆕 فحص أحدث 10 دومينات']]
        msg = "🛠 **لوحة تحكم الأدمن**\nقم بإرسال الكوكي المستخرج من المتصفح لتفعيل البوت."
    else:
        kb = [['🆕 Expired .com']]
        msg = "🌟 **قناص الدومينات**\nاستخدم القائمة بالأسفل لجلب النتائج."
    
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id != ADMIN_ID: return

    if text == '⚙️ تحديث الكوكي (الربط)':
        await update.message.reply_text("📥 أرسل نص الكوكي الطويل الذي نسخته من المتصفح الآن:")
        context.user_data['state'] = 'WAIT_COOKIE'
        return

    if context.user_data.get('state') == 'WAIT_COOKIE':
        # تنظيف النص من كلمة 'cookie:' إذا نُسخت بالخطأ
        clean_cookie = text.replace("cookie: ", "").strip()
        SESSION_DATA["cookie"] = clean_cookie
        context.user_data['state'] = None
        await update.message.reply_text("✅ **تم الربط بنجاح!**\nالبوت الآن مسجل دخول باسم حسابك ويمكنه جلب البيانات.")
        return

async def fetch_domains(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not SESSION_DATA["cookie"]:
        await update.message.reply_text("⚠️ يجب على الأدمن تحديث الكوكي أولاً.")
        return

    msg = await update.message.reply_text("⏳ جاري سحب البيانات من حسابك الشخصي...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': SESSION_DATA["cookie"],
            'Referer': 'https://www.expireddomains.net/'
        }
        # جلب دومينات .com المنتهية
        url = "https://www.expireddomains.net/domains/expiredcom/"
        resp = requests.get(url, headers=headers, timeout=15)
        
        if "Login" in resp.text:
            await msg.edit_text("❌ فشل الاتصال: الكوكي غير صحيح أو انتهت صلاحيته. يرجى تحديثه.")
            return

        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table', {'class': 'listing'})
        if not table:
            await msg.edit_text("⚠️ لا توجد نتائج حالياً.")
            return

        rows = table.find_all('tr')[1:11]
        report = "🎯 **أحدث 10 دومينات .com متاحة:**\n\n"
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 5:
                domain = cols[0].get_text(strip=True)
                bl = cols[1].get_text(strip=True)
                dp = cols[2].get_text(strip=True)
                report += f"🌐 `{domain}`\n🔗 BL: {bl} | 🏗️ DP: {dp}\n\n"
        
        await msg.edit_text(report, parse_mode='Markdown')
    except Exception as e:
        await msg.edit_text(f"❌ خطأ فني: {str(e)}")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Chat(ADMIN_ID) & filters.Regex('⚙️|تحديث'), handle_admin))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fetch_domains))
    app.run_polling(drop_pending_updates=True)
