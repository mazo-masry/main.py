import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(level=logging.INFO)

# الإعدادات
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

# إعداد متصفح سيلينيوم (Chrome Headless)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = None # سيتم تشغيله عند طلب الأدمن

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        kb = [['🔑 تسجيل الدخول للموقع'], ['🔍 فحص حالة الحساب']]
        msg = "🛠 **لوحة تحكم الأدمن**\nاضغط على الزر للبدء في ربط حسابك بالموقع."
    else:
        kb = [['🆕 Expired .com', '⏳ Pending Delete']]
        msg = "🌟 **مرحباً بك في قناص الدومينات**\nسيتم جلب النتائج من حساب الأدمن الموثق."
    
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global driver
    user_id = update.effective_user.id
    text = update.message.text

    if user_id != ADMIN_ID: return

    if text == '🔑 تسجيل الدخول للموقع':
        await update.message.reply_text("👤 أرسل الآن: **اليوزر نيم** و **الباسورد** مفصولين بمسافة\nمثال: `myuser mypass123`", parse_mode='Markdown')
        context.user_data['state'] = 'WAIT_CREDS'

    elif context.user_data.get('state') == 'WAIT_CREDS':
        try:
            u, p = text.split(" ")
            context.user_data['u'], context.user_data['p'] = u, p
            
            # تشغيل المتصفح والدخول لصفحة اللوجن
            driver = webdriver.Chrome(options=chrome_options)
            driver.get("https://member.expireddomains.net/login/")
            
            driver.find_element(By.ID, "inputLogin").send_keys(u)
            driver.find_element(By.ID, "inputPassword").send_keys(p)
            
            # أخذ لقطة شاشة لكود التحقق (Captcha) وإرسالها للأدمن
            driver.save_screenshot("captcha.png")
            await update.message.reply_photo(photo=open("captcha.png", "rb"), caption="🖼 أرسل كود التحقق (Captcha) الظاهر في الصورة:")
            context.user_data['state'] = 'WAIT_CAPTCHA'
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ: {e}")

    elif context.user_data.get('state') == 'WAIT_CAPTCHA':
        try:
            captcha_code = text
            driver.find_element(By.NAME, "captcha").send_keys(captcha_code)
            driver.find_element(By.TAG_NAME, "button").click() # زر Login
            
            time.sleep(3) # انتظار التحميل
            if "login" not in driver.current_url.lower():
                await update.message.reply_text("✅ **تم تسجيل الدخول بنجاح!**\nالجلسة الآن نشطة وسيقوم البوت بسحب البيانات للزبائن.")
                context.user_data['state'] = 'LOGGED_IN'
            else:
                await update.message.reply_text("❌ فشل تسجيل الدخول. ربما الكود خاطئ.")
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ: {e}")

# --- وظيفة سحب الدومينات للزبائن ---
async def fetch_for_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global driver
    if not driver:
        await update.message.reply_text("⚠️ البوت غير متصل بحساب الأدمن حالياً.")
        return

    msg = await update.message.reply_text("⏳ جاري جلب أحدث 10 دومينات من الحساب...")
    
    try:
        # التوجه لصفحة الـ Expired .com
        driver.get("https://member.expireddomains.net/domains/expiredcom/")
        time.sleep(2)
        
        # استخراج البيانات من الجدول
        rows = driver.find_elements(By.CSS_SELECTOR, ".listing tr")[1:11]
        report = "🎯 **أحدث الدومينات المتاحة للشراء:**\n\n"
        
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) > 5:
                domain = cols[0].text
                bl = cols[1].text # Backlinks
                status = cols[3].text
                report += f"🌐 `{domain}`\n🔗 BL: {bl} | 📅 {status}\n\n"
        
        await msg.edit_text(report, parse_mode='Markdown')
    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ أثناء السحب: {e}")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex('🔑 تسجيل الدخول للموقع') | filters.Regex('🆕 Expired .com'), handle_admin if ADMIN_ID else fetch_for_users))
    # إضافة معالج عام للرسائل النصية للحالات (States)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin))
    app.run_polling()
