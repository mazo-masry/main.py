import os
import requests
from bs4 import BeautifulSoup
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

# جلسة العمل المستمرة
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        kb = [['🔑 تسجيل دخول (خطوتين)']]
        await update.message.reply_text("🛠 **لوحة تحكم الأدمن**\nابدأ عملية الدخول بنظام كود الإيميل.", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    else:
        await update.message.reply_text("🌟 بوت صيد الدومينات جاهز.")

async def handle_login_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id != ADMIN_ID: return

    # 1. طلب اليوزر والباسورد
    if text == '🔑 تسجيل دخول (خطوتين)':
        await update.message.reply_text("👤 أرسل اليوزر والباسورد (بينهما مسافة):")
        context.user_data['state'] = 'WAIT_CREDS'
        return

    # 2. إرسال البيانات وانتظار الموقع ليرسل الإيميل
    if state == 'WAIT_CREDS':
        creds = text.split(" ")
        if len(creds) < 2:
            await update.message.reply_text("⚠️ أرسل اليوزر والباسورد وبينهما مسافة واحدة.")
            return
        
        context.user_data['u'], context.user_data['p'] = creds[0], creds[1]
        msg = await update.message.reply_text("⏳ جاري إرسال البيانات... انتظر وصول الكود لإيميلك.")
        
        try:
            login_data = {'login': creds[0], 'password': creds[1], 'autologin': '1'}
            response = session.post("https://www.expireddomains.net/login/", data=login_data, timeout=20)
            
            # فحص إذا كان الموقع يطلب كود التحقق
            if "verification" in response.text.lower() or "code" in response.text.lower():
                await msg.edit_text("📧 الموقع أرسل كوداً إلى بريدك الإلكتروني.\nأرسل الكود هنا الآن:")
                context.user_data['state'] = 'WAIT_EMAIL_CODE'
            elif "Logout" in response.text:
                await msg.edit_text("✅ تم الدخول مباشرة بدون كود!")
            else:
                await msg.edit_text("❌ فشل الدخول. تأكد من صحة البيانات أو أن الموقع لم يرسل الكود.")
        except Exception as e:
            await msg.edit_text(f"❌ خطأ: {str(e)}")
        return

    # 3. إرسال كود الإيميل وإتمام العملية
    if state == 'WAIT_EMAIL_CODE':
        msg = await update.message.reply_text("⏳ جاري تأكيد الكود...")
        try:
            # هنا نرسل الكود الذي أرسله المستخدم
            verify_data = {'code': text} # اسم الحقل 'code' قد يختلف حسب الموقع
            response = session.post("https://www.expireddomains.net/login/verify/", data=verify_data) # رابط افتراضي للتحقق
            
            if "Logout" in response.text or response.status_code == 200:
                await msg.edit_text("✅ **مبروك! تم تسجيل الدخول وتفعيل الحساب.**")
                context.user_data['state'] = 'LOGGED_IN'
            else:
                await msg.edit_text("❌ الكود غير صحيح أو انتهت صلاحيته.")
        except Exception as e:
            await msg.edit_text(f"❌ خطأ أثناء التأكيد: {str(e)}")
        return

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login_2fa))
    app.run_polling()
