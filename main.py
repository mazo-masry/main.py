import os
import requests
from bs4 import BeautifulSoup
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة أداء البوت على Railway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# الإعدادات (تأكد من ضبط BOT_TOKEN في متغيرات Railway)
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780  # معرف الأدمن الخاص بك

# إنشاء جلسة (Session) للحفاظ على اتصال مستمر
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بداية التفاعل مع البوت"""
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        kb = [['🔑 ابدأ تسجيل الدخول']]
        await update.message.reply_text(
            "🛠 **لوحة تحكم الأدمن**\nاضغط على الزر أدناه للبدء في ربط حسابك بالموقع.",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )

async def handle_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id != ADMIN_ID: return

    # 1. طلب بيانات الحساب
    if text == '🔑 ابدأ تسجيل الدخول':
        await update.message.reply_text(
            "👤 يرجى إرسال **اسم المستخدم** و **كلمة المرور** مفصولين بمسافة.\n"
            "مثال: `cicada2252 myPassword123`"
        )
        context.user_data['state'] = 'WAIT_CREDS'
        return

    # 2. جلب صفحة الدخول وصورة الكابتشا
    if state == 'WAIT_CREDS':
        try:
            creds = text.split(" ")
            if len(creds) < 2:
                await update.message.reply_text("⚠️ تنسيق خاطئ! أرسل اليوزر والباسورد وبينهم مسافة.")
                return
            
            context.user_data['u'], context.user_data['p'] = creds[0], creds[1]
            
            # جلب صفحة اللوجن للحصول على الكابتشا
            response = session.get("https://www.expireddomains.net/login/", timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            captcha_tag = soup.find('img', {'alt': 'captcha'})
            
            if captcha_tag:
                captcha_url = "https://www.expireddomains.net" + captcha_tag['src']
                await update.message.reply_photo(photo=captcha_url, caption="🖼 أرسل كود التحقق (Captcha) الموضح في الصورة:")
                context.user_data['state'] = 'WAIT_CAPTCHA'
            else:
                await update.message.reply_text("❌ لم أتمكن من العثور على صورة الكابتشا. حاول مجدداً.")
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في الاتصال: {e}")
        return

    # 3. محاولة تسجيل الدخول وإبلاغك بالنتيجة
    if state == 'WAIT_CAPTCHA':
        login_data = {
            'login': context.user_data['u'],
            'password': context.user_data['p'],
            'captcha': text,
            'autologin': '1'
        }
        
        try:
            # إرسال بيانات الدخول
            response = session.post("https://www.expireddomains.net/login/", data=login_data, timeout=15)
            
            # التحقق من نجاح تسجيل الدخول (وجود كلمة Logout يعني أننا بالداخل)
            if "Logout" in response.text:
                await update.message.reply_text(
                    "✅ **نجح تسجيل الدخول!**\n"
                    "تم ربط البوت بحسابك بنجاح والجلسة الآن نشطة."
                )
                context.user_data['state'] = 'LOGGED_IN'
            else:
                await update.message.reply_text(
                    "❌ **فشل تسجيل الدخول!**\n"
                    "السبب المحتمل: كود الكابتشا خاطئ أو بيانات الحساب غير صحيحة."
                )
                context.user_data['state'] = None
        except Exception as e:
            await update.message.reply_text(f"❌ حدث خطأ غير متوقع: {e}")
        return

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login))
    
    print("البوت يعمل الآن ومستعد لتسجيل الدخول...")
    app.run_polling(drop_pending_updates=True)
