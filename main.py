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

# إنشاء جلسة عمل للحفاظ على الاتصال بين الخطوات
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
    'Referer': 'https://www.expireddomains.net/login/'
})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        kb = [['🔐 بدء تسجيل الدخول']]
        await update.message.reply_text("👑 **لوحة تحكم الأدمن**\nاضغط للبدء في عملية تسجيل الدخول بنظام كود الإيميل.", 
                                       reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id != ADMIN_ID: return

    # الخطوة 1: طلب اليوزر والباسورد
    if text == '🔐 بدء تسجيل الدخول':
        await update.message.reply_text("👤 أرسل **اليوزر** و **الباسورد** بمسافة واحدة بينهما:")
        context.user_data['state'] = 'WAIT_CREDS'
        return

    # الخطوة 2: إرسال البيانات وانتظار الموقع ليرسل الكود للإيميل
    if state == 'WAIT_CREDS':
        creds = text.split(" ")
        if len(creds) < 2:
            await update.message.reply_text("⚠️ خطأ! أرسل اليوزر والباسورد وبينهما مسافة.")
            return
        
        u, p = creds[0], creds[1]
        m = await update.message.reply_text(f"⏳ جاري إرسال البيانات لـ {u}...\nيرجى مراقبة إيميلك الآن.")
        
        try:
            login_url = "https://www.expireddomains.net/login/"
            # استخراج أي رموز خفية (CSRF Tokens) إذا وجدت
            res = session.get(login_url)
            
            payload = {
                'login': u,
                'password': p,
                'autologin': '1',
                'redirect_to': '/login/logincheck/'
            }
            
            response = session.post(login_url, data=payload, timeout=20)
            
            # التحقق إذا كان الموقع يطلب كود الإيميل
            if "verification" in response.text.lower() or "logincheck" in response.url:
                await m.edit_text("📧 **تم إرسال الكود إلى إيميلك!**\nمن فضلك أرسل الكود هنا الآن:")
                context.user_data['state'] = 'WAIT_CODE'
            elif "Logout" in response.text:
                await m.edit_text("✅ نجح تسجيل الدخول مباشرة بدون كود!")
                context.user_data['state'] = 'LOGGED_IN'
            else:
                await m.edit_text("❌ فشل الدخول. تأكد من صحة البيانات أو وجود كابتشا.")
                context.user_data['state'] = None
        except Exception as e:
            await m.edit_text(f"❌ خطأ: {str(e)}")
        return

    # الخطوة 3: استقبال كود الإيميل وإرساله للموقع
    if state == 'WAIT_CODE':
        m = await update.message.reply_text(f"⏳ جاري تأكيد الكود: {text}")
        try:
            check_url = "https://www.expireddomains.net/login/logincheck/"
            verify_payload = {'code': text} # اسم الحقل 'code' قد يتغير حسب برمجة الموقع
            
            final_res = session.post(check_url, data=verify_payload, timeout=20)
            
            if "Logout" in final_res.text or "Member Area" in final_res.text:
                await m.edit_text("✅ **مبروك! تم تسجيل الدخول بنجاح.**\nيمكنك الآن استخدام أزرار جلب الدومينات.")
                context.user_data['state'] = 'LOGGED_IN'
            else:
                await m.edit_text("❌ الكود غير صحيح أو انتهت صلاحيته. حاول مجدداً.")
                context.user_data['state'] = None
        except Exception as e:
            await m.edit_text(f"❌ خطأ أثناء التأكيد: {str(e)}")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login))
    app.run_polling()
