import os
import requests
from bs4 import BeautifulSoup
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- الإعدادات الأساسية ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

# الكوكي الثابت (تم تصحيحه بناءً على بياناتك)
FIXED_COOKIE = (
    "PHPSESSID=gnLJ2C YEKFs-aYk; "
    "WicaUhzLByzwOTq7rZNyoVSTP=ZL2pjQwd05vkkSBnWIH02hfVb; "
    "4w9NAlmhgvr7EMykMSe-5gG1uT2MxLYxT9Vc5kEbWCOC=M0q3ArfR8LDRpkA5QD"
)

# قائمة المستخدمين المسموح لهم
ALLOWED_USERS = {ADMIN_ID}

# دالة الاستخراج الشاملة بـ Headers المتصفح الخاص بك
def fetch_all_domains(endpoint):
    url = f"https://www.expireddomains.net/domains/{endpoint}/"
    headers = {
        'authority': 'member.expireddomains.net',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'cookie': FIXED_COOKIE,
        'sec-ch-ua': '"Chromium";v="144", "Google Chrome";v="144", "Not(A:Brand";v="8"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-site',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if "Login" in response.text: return "EXPIRED"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'listing'})
        if not table: return "EMPTY"

        rows = table.find_all('tr')[1:] # استخراج كل الدومينات المتاحة في الصفحة
        results = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 5:
                results.append({
                    "domain": cols[0].get_text(strip=True),
                    "bl": cols[1].get_text(strip=True),
                    "dp": cols[2].get_text(strip=True),
                    "status": cols[3].get_text(strip=True)
                })
        return results
    except Exception as e:
        return f"ERROR: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        kb = [['🔍 استخراج شامل .com', '🌐 استخراج شامل .net'], ['⏳ قريباً (Pending)', '👥 إدارة الأعضاء']]
        msg = "👑 **لوحة تحكم القناص**\nتم تحديث البصمة الرقمية لتطابق Chrome 144."
    elif user_id in ALLOWED_USERS:
        kb = [['🔍 استخراج شامل .com', '🌐 استخراج شامل .net']]
        msg = "🌟 **مرحباً بك**\nيمكنك الآن سحب كافة الدومينات."
    else:
        await update.message.reply_text("🚫 الوصول مرفوض.")
        return
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id == ADMIN_ID:
        if text == '👥 إدارة الأعضاء':
            kb = [['➕ إضافة عضو', '➖ حذف عضو'], ['🔙 رجوع']]
            await update.message.reply_text("اختر الإجراء:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return
        if text == '➕ إضافة عضو':
            await update.message.reply_text("أرسل الـ ID الجديد:")
            context.user_data['state'] = 'ADD'
            return
        if state == 'ADD':
            try:
                ALLOWED_USERS.add(int(text))
                await update.message.reply_text(f"✅ تم تفعيل {text}")
            except: pass
            context.user_data['state'] = None
            return

    if user_id in ALLOWED_USERS:
        endpoint = ""
        if '.com' in text: endpoint = "expiredcom"
        elif '.net' in text: endpoint = "expirednet"
        elif 'Pending' in text: endpoint = "pendingdelete"

        if endpoint:
            wait = await update.message.reply_text("🔄 جاري سحب القائمة بالكامل...")
            data = fetch_all_domains(endpoint)

            if data == "EXPIRED":
                await wait.edit_text("❌ الجلسة انتهت. حدث الكوكي من المتصفح.")
            elif data == "EMPTY":
                await wait.edit_text("⚠️ لا توجد نتائج حالياً.")
            elif isinstance(data, list):
                report = f"✅ **تم العثور على {len(data)} دومين:**\n\n"
                for i, item in enumerate(data, 1):
                    line = f"{i}- `{item['domain']}` (BL: {item['bl']} | DP: {item['dp']})\n"
                    if len(report) + len(line) > 3900:
                        await update.message.reply_text(report, parse_mode='Markdown')
                        report = ""
                    report += line
                await update.message.reply_text(report, parse_mode='Markdown')
                await wait.delete()

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    app.run_polling()
