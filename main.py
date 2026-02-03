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

# مخزن الجلسة (سيتم حفظ الكوكي هنا برمجياً)
SESSION_DATA = {"cookie": ""}
# قائمة المستخدمين المسموح لهم
ALLOWED_USERS = {ADMIN_ID}

def fetch_data(endpoint, cookie):
    url = f"https://www.expireddomains.net/domains/{endpoint}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': cookie,
        'Referer': 'https://www.expireddomains.net/'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if "Login" in response.text:
            return "EXPIRED"
            
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'listing'})
        if not table: return "EMPTY"

        rows = table.find_all('tr')[1:11]
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
    except: return "ERROR"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        kb = [
            ['🆕 جلب .com', '🌐 جلب .net'],
            ['⏳ قريباً (Pending)', '⚙️ تحديث الجلسة (الكوكي)'],
            ['➕ إضافة مستخدم', '📊 قائمة المستخدمين']
        ]
        msg = "👑 **لوحة تحكم الأدمن**\nجاهز لجلب البيانات. إذا توقف البوت، قم بتحديث الكوكي."
    elif user_id in ALLOWED_USERS:
        kb = [['🆕 جلب .com', '🌐 جلب .net'], ['⏳ قريباً (Pending)']]
        msg = "🌟 **مرحباً بك**\nيمكنك البحث عن الدومينات الآن."
    else:
        await update.message.reply_text("🚫 غير مصرح لك. تواصل مع الأدمن.")
        return
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    # --- إدارة الكوكي والمستخدمين (للأدمن) ---
    if user_id == ADMIN_ID:
        if text == '⚙️ تحديث الجلسة (الكوكي)':
            await update.message.reply_text("📥 أرسل الكوكي الجديد من المتصفح الآن:")
            context.user_data['state'] = 'WAIT_COOKIE'
            return
        if state == 'WAIT_COOKIE':
            SESSION_DATA["cookie"] = text.strip()
            context.user_data['state'] = None
            await update.message.reply_text("✅ تم تحديث الجلسة بنجاح! جرب السحب الآن.")
            return
        if text == '➕ إضافة مستخدم':
            await update.message.reply_text("أرسل ID المستخدم:")
            context.user_data['state'] = 'ADD_USER'
            return
        if state == 'ADD_USER':
            try:
                ALLOWED_USERS.add(int(text))
                await update.message.reply_text(f"✅ تم إضافة {text}")
            except: await update.message.reply_text("❌ ID خطأ")
            context.user_data['state'] = None
            return

    # --- جلب الدومينات ---
    if user_id in ALLOWED_USERS:
        endpoint = ""
        if text == '🆕 جلب .com': endpoint = "expiredcom"
        elif text == '🌐 جلب .net': endpoint = "expirednet"
        elif text == '⏳ قريباً (Pending)': endpoint = "pendingdelete"

        if endpoint:
            if not SESSION_DATA["cookie"]:
                await update.message.reply_text("⚠️ الأدمن لم يقم بضبط الكوكي بعد.")
                return
            
            m = await update.message.reply_text("⏳ جاري سحب البيانات...")
            data = fetch_data(endpoint, SESSION_DATA["cookie"])

            if data == "EXPIRED":
                await m.edit_text("❌ انتهت صلاحية الكوكي. يرجى من الأدمن تحديثه.")
            elif data == "EMPTY" or data == "ERROR":
                await m.edit_text("⚠️ فشل جلب البيانات. تأكد من الكوكي أو الموقع.")
            else:
                res = f"🎯 **أحدث 10 نتائج ({text}):**\n\n"
                for item in data:
                    res += f"🌐 `{item['domain']}`\n🔗 BL: `{item['bl']}` | 📅 `{item['status']}`\n\n"
                await m.edit_text(res, parse_mode='Markdown')

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    app.run_polling()
