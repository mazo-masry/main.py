import os
import requests
from bs4 import BeautifulSoup
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبةRailway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

# كائن الجلسة للحفاظ على تسجيل الدخول دائماً
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        kb = [['🔑 تسجيل الدخول للموقع'], ['📊 فحص حالة الجلسة']]
        msg = "🛠 **لوحة تحكم الأدمن**\nابدأ بربط حسابك لسحب البيانات للزبائن."
    else:
        kb = [['🆕 Expired .com', '⏳ Pending Delete']]
        msg = "🌟 **قناص الدومينات**\nاختر القسم المطلوب لجلب النتائج من حساب الأدمن الموثق."
    
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode='Markdown')

async def handle_admin_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id != ADMIN_ID: return

    # 1. تفعيل وضع تسجيل الدخول
    if text == '🔑 تسجيل الدخول للموقع':
        await update.message.reply_text("👤 أرسل اليوزر والباسورد بمسافة واحدة بينهم:\n(مثال: `myuser mypassword`)")
        context.user_data['state'] = 'WAIT_CREDS'
        return

    # 2. معالجة اليوزر والباسورد وجلب الكابتشا
    if state == 'WAIT_CREDS':
        parts = text.split(" ")
        if len(parts) < 2:
            await update.message.reply_text("⚠️ خطأ! أرسل اليوزر ثم مسافة ثم الباسورد.\nمثال: `cicada2252 pass123`")
            return
        
        context.user_data['u'], context.user_data['p'] = parts[0], parts[1]
        
        try:
            resp = session.get("https://member.expireddomains.net/login/", timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            captcha_tag = soup.find('img', {'alt': 'captcha'})
            
            if captcha_tag:
                captcha_url = "https://member.expireddomains.net" + captcha_tag['src']
                await update.message.reply_photo(photo=captcha_url, caption="🖼 أرسل كود التحقق (Captcha) الظاهر في الصورة:")
                context.user_data['state'] = 'WAIT_CAPTCHA'
            else:
                await update.message.reply_text("❌ لم يتم العثور على الكابتشا. جرب مرة أخرى.")
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في الاتصال: {e}")
        return

    # 3. إرسال الكابتشا وإتمام الدخول
    if state == 'WAIT_CAPTCHA':
        login_data = {
            'login': context.user_data['u'],
            'password': context.user_data['p'],
            'captcha': text,
            'autologin': '1'
        }
        try:
            resp = session.post("https://member.expireddomains.net/login/", data=login_data, timeout=15)
            if "Logout" in resp.text:
                await update.message.reply_text("✅ **تم تسجيل الدخول بنجاح!**\nالجلسة نشطة الآن والحساب مرتبط بالبوت.")
                context.user_data['state'] = 'LOGGED_IN'
            else:
                await update.message.reply_text("❌ فشل الدخول. ربما الكود خاطئ أو الحساب محظور.")
                context.user_data['state'] = None
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ أثناء الدخول: {e}")
        return

async def fetch_for_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ['🆕 Expired .com', '⏳ Pending Delete']: return

    endpoint = "expiredcom" if "Expired" in text else "pendingdelete"
    msg = await update.message.reply_text("⏳ جاري سحب أحدث 10 نتائج من حساب الأدمن...")
    
    try:
        url = f"https://member.expireddomains.net/domains/{endpoint}/"
        resp = session.get(url, timeout=15)
        
        if "Login" in resp.text:
            await msg.edit_text("⚠️ حساب الأدمن غير متصل حالياً. يرجى إبلاغ الأدمن لتسجيل الدخول.")
            return

        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table', {'class': 'listing'})
        if not table:
            await msg.edit_text("⚠️ لا توجد نتائج حالياً في هذا القسم.")
            return

        rows = table.find_all('tr')[1:11]
        report = f"🎯 **نتائج قسم {text}:**\n\n"
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 5:
                domain = cols[0].get_text(strip=True)
                bl = cols[1].get_text(strip=True) # الروابط الخلفية
                status = cols[3].get_text(strip=True) # الحالة/التاريخ
                report += f"🌐 `{domain}`\n🔗 BL: {bl} | 📅 {status}\n\n"
        
        await msg.edit_text(report, parse_mode='Markdown')
    except Exception as e:
        await msg.edit_text(f"❌ خطأ أثناء السحب: {e}")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    
    # توزيع المهام
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Chat(ADMIN_ID) & (filters.Regex('🔑') | filters.TEXT), handle_admin_login))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fetch_for_users))
    
    print("Bot is alive on Railway...")
    app.run_polling(drop_pending_updates=True)
