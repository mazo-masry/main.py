import os
import requests
from bs4 import BeautifulSoup
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة Railway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

# جلسة العمل
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        kb = [['🔐 تسجيل دخول مباشر']]
        await update.message.reply_text(
            "🛠 **لوحة تحكم الأدمن**\nاضغط للبدء في ربط الحساب بدون كابتشا.",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
    else:
        await update.message.reply_text("🌟 قناص الدومينات جاهز للعمل.")

async def handle_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id != ADMIN_ID: return

    # 1. طلب البيانات
    if text == '🔐 تسجيل دخول مباشر':
        await update.message.reply_text("👤 أرسل اليوزر والباسورد بمسافة واحدة:\nمثال: `cicada2252 password123`")
        context.user_data['state'] = 'WAIT_CREDS'
        return

    # 2. تنفيذ الدخول المباشر
    if state == 'WAIT_CREDS':
        creds = text.split(" ")
        if len(creds) < 2:
            await update.message.reply_text("⚠️ خطأ! يرجى إرسال اليوزر والباسورد وبينهما مسافة.")
            return
        
        u, p = creds[0], creds[1]
        msg = await update.message.reply_text("⏳ جاري محاولة تسجيل الدخول المباشر...")
        
        try:
            # محاكاة إرسال الفورم (Form Submission)
            login_url = "https://www.expireddomains.net/login/"
            login_data = {
                'login': u,
                'password': p,
                'autologin': '1',
                'redirect_to': '/domains/expiredcom/' # التوجه للنتائج فوراً
            }
            
            # إرسال طلب الدخول
            response = session.post(login_url, data=login_data, timeout=20)
            
            # فحص النجاح (الموقع يظهر كلمة Logout عند النجاح)
            if "Logout" in response.text or "Member Area" in response.text:
                await msg.edit_text(f"✅ **تم تسجيل الدخول بنجاح!**\n\nحساب `{u}` مرتبك الآن بالبوت.")
                context.user_data['state'] = 'LOGGED_IN'
            else:
                # في حال فشل الدخول، قد يكون الموقع طلب كابتشا مخفية
                if "captcha" in response.text.lower():
                    await msg.edit_text("❌ فشل الدخول: الموقع يطلب كابتشا للسيرفر بالرغم من عدم ظهورها لك في المتصفح.")
                else:
                    await msg.edit_text("❌ فشل تسجيل الدخول: تأكد من صحة اليوزر والباسورد.")
                context.user_data['state'] = None
                
        except Exception as e:
            await msg.edit_text(f"❌ خطأ فني: {str(e)}")
        return

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login))
    print("البوت يعمل بنظام الدخول المباشر...")
    app.run_polling(drop_pending_updates=True)
