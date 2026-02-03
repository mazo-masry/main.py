import os
import requests
from bs4 import BeautifulSoup
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمتابعة الأداء على Railway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

# كائن الجلسة للحفاظ على تسجيل الدخول
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        kb = [['🔑 تسجيل الدخول للموقع'], ['➕ إضافة مستخدم', '➖ حذف مستخدم']]
        msg = "🛠 **لوحة تحكم الأدمن**\nابدأ بربط حسابك لسحب البيانات للزبائن."
    else:
        kb = [['🆕 Expired .com', '⏳ Pending Delete']]
        msg = "🌟 **قناص الدومينات**\nاختر القسم المطلوب لجلب النتائج من حساب الأدمن."
    
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_login_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id != ADMIN_ID: return

    # 1. طلب بيانات الدخول
    if text == '🔑 تسجيل الدخول للموقع':
        await update.message.reply_text("👤 أرسل اليوزر والباسورد بمسافة:\n(مثال: `username password`)")
        context.user_data['state'] = 'WAIT_CREDS'
        return

    # 2. إرسال البيانات وجلب الكابتشا
    if state == 'WAIT_CREDS':
        try:
            u, p = text.split(" ")
            context.user_data['u'], context.user_data['p'] = u, p
            
            # محاولة فتح صفحة اللوجن لجلب الكوكيز الأولية وصورة الكابتشا
            resp = session.get("https://member.expireddomains.net/login/")
            soup = BeautifulSoup(resp.text, 'html.parser')
            captcha_img = soup.find('img', {'alt': 'captcha'})['src']
            
            # إرسال رابط الكابتشا أو الصورة (الموقع يوفرها كرابط)
            full_captcha_url = "https://member.expireddomains.net" + captcha_img
            await update.message.reply_photo(photo=full_captcha_url, caption="🖼 أرسل كود التحقق (Captcha) الظاهر في الصورة:")
            context.user_data['state'] = 'WAIT_CAPTCHA'
        except Exception as e:
            await update.message.reply_text(f"❌ فشل جلب الكابتشا: {e}")
        return

    # 3. إكمال الدخول
    if state == 'WAIT_CAPTCHA':
        login_data = {
            'login': context.user_data['u'],
            'password': context.user_data['p'],
            'captcha': text,
            'autologin': '1'
        }
        resp = session.post("https://member.expireddomains.net/login/", data=login_data)
        
        if "Logout" in resp.text:
            await update.message.reply_text("✅ **تم تسجيل الدخول بنجاح!**\nالجلسة نشطة الآن لخدمة الزبائن.")
            context.user_data['state'] = 'LOGGED_IN'
        else:
            await update.message.reply_text("❌ فشل الدخول. تأكد من البيانات والكود.")
            context.user_data['state'] = None
        return

async def fetch_for_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    endpoint = "expiredcom" if "Expired" in text else "pendingdelete"
    
    msg = await update.message.reply_text("⏳ جاري سحب أحدث 10 نتائج من حساب الأدمن...")
    
    try:
        url = f"https://member.expireddomains.net/domains/{endpoint}/"
        resp = session.get(url)
        
        if "Login" in resp.text:
            await msg.edit_text("⚠️ حساب الأدمن غير متصل. يرجى إبلاغ الإدارة.")
            return

        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table', {'class': 'listing'})
        rows = table.find_all('tr')[1:11]
        
        report = f"🎯 **نتائج قسم {endpoint}:**\n\n"
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 5:
                domain = cols[0].get_text(strip=True)
                bl = cols[1].get_text(strip=True)
                report += f"🌐 `{domain}`\n🔗 BL: {bl}\n\n"
        
        await msg.edit_text(report, parse_mode='Markdown')
    except Exception as e:
        await msg.edit_text(f"❌ خطأ أثناء جلب البيانات: {e}")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex('🔑 تسجيل الدخول للموقع') | filters.TEXT & filters.Chat(ADMIN_ID), handle_login_process))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fetch_for_users))
    app.run_polling(drop_pending_updates=True)
