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
ADMIN_ID = 665829780  # معرف الأدمن الخاص بك

# الكوكي الثابت الخاص بك (تم تنظيفه ودمجه)
FIXED_COOKIE = (
    "PHPSESSID=gnLJ2C YEKFs-aYk; "
    "WicaUhzLByzwOIq7rZNyoVSTP=2L2pjQwd05vkk5BnWIH02hfVb; "
    "4w9NAlmhgvr7EMykMSe-5gG1uT2MxLYxT9VcSkEbWCDC=M0q3ArfR8LDRpkASQD"
)

# قائمة المستخدمين المسموح لهم (تبدأ بالأدمن)
ALLOWED_USERS = {ADMIN_ID}

# دالة سحب كافة الدومينات المعروضة في الصفحة
def fetch_all_listed_domains(endpoint):
    url = f"https://www.expireddomains.net/domains/{endpoint}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Cookie': FIXED_COOKIE,
        'Referer': 'https://www.expireddomains.net/'
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if "Login" in response.text:
            return "EXPIRED"
            
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'listing'})
        if not table:
            return "EMPTY"

        # سحب كل الصفوف المتاحة (بدون تحديد عدد معين)
        rows = table.find_all('tr')[1:] 
        results = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 5:
                results.append({
                    "domain": cols[0].get_text(strip=True),
                    "bl": cols[1].get_text(strip=True),
                    "status": cols[3].get_text(strip=True)
                })
        return results
    except Exception as e:
        logging.error(f"Error: {e}")
        return "ERROR"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        kb = [
            ['🔍 استخراج كافة الدومينات (.com)', '🌐 استخراج (.net)'],
            ['⏳ قريباً (Pending)', '👥 إدارة المستخدمين']
        ]
        msg = "👑 **لوحة تحكم الأدمن**\nالكوكي مدمج والسكربت جاهز للاستخراج الشامل."
    elif user_id in ALLOWED_USERS:
        kb = [['🔍 استخراج كافة الدومينات (.com)', '🌐 استخراج (.net)']]
        msg = "🌟 **مرحباً بك**\nيمكنك الآن سحب كافة الدومينات المتاحة."
    else:
        await update.message.reply_text("🚫 الدخول ممنوع. تواصل مع الأدمن للوصول.")
        return
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    # --- إدارة المستخدمين (للأدمن فقط) ---
    if user_id == ADMIN_ID:
        if text == '👥 إدارة المستخدمين':
            kb = [['➕ إضافة مستخدم', '➖ حذف مستخدم'], ['🔙 رجوع']]
            await update.message.reply_text("اختر العملية المطلوبة:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return
        
        if text == '➕ إضافة مستخدم':
            await update.message.reply_text("أرسل ID المستخدم الجديد:")
            context.user_data['state'] = 'ADD'
            return
        
        if state == 'ADD':
            try:
                new_id = int(text)
                ALLOWED_USERS.add(new_id)
                await update.message.reply_text(f"✅ تم تفعيل المستخدم {new_id}")
            except: await update.message.reply_text("❌ خطأ! أرسل أرقام الـ ID فقط.")
            context.user_data['state'] = None
            return

        if text == '➖ حذف مستخدم':
            await update.message.reply_text("أرسل ID المستخدم المراد حذفه:")
            context.user_data['state'] = 'DEL'
            return
        
        if state == 'DEL':
            try:
                del_id = int(text)
                ALLOWED_USERS.discard(del_id)
                await update.message.reply_text(f"🗑 تم حذف المستخدم {del_id}")
            except: await update.message.reply_text("❌ خطأ في الـ ID.")
            context.user_data['state'] = None
            return

    # --- استخراج الدومينات ---
    if user_id in ALLOWED_USERS:
        endpoint = ""
        if '(.com)' in text: endpoint = "expiredcom"
        elif '(.net)' in text: endpoint = "expirednet"
        elif 'Pending' in text: endpoint = "pendingdelete"

        if endpoint:
            status_msg = await update.message.reply_text("🔄 جاري سحب كافة الدومينات المتاحة الآن...")
            data = fetch_all_listed_domains(endpoint)

            if data == "EXPIRED":
                await status_msg.edit_text("❌ فشل! الكوكي الثابت لم يعد يعمل أو تم حظره. يرجى استخراج واحد جديد.")
            elif data == "EMPTY" or data == "ERROR":
                await status_msg.edit_text("⚠️ الموقع لم يرجع بيانات. قد يكون هناك حظر مؤقت لـ IP السيرفر.")
            else:
                # تقسيم النتائج لرسائل إذا كانت كثيرة
                report = f"✅ **تم العثور على {len(data)} دومين:**\n\n"
                for i, item in enumerate(data, 1):
                    line = f"{i}- `{item['domain']}` (BL: {item['bl']})\n"
                    if len(report) + len(line) > 4000: # تجنب تجاوز حد رسالة تليجرام
                        await update.message.reply_text(report, parse_mode='Markdown')
                        report = ""
                    report += line
                
                await update.message.reply_text(report, parse_mode='Markdown')
                await status_msg.delete()

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    print("البوت يعمل الآن بنظام الاستخراج الشامل...")
    app.run_polling()
