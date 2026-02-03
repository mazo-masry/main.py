import os
import requests
from bs4 import BeautifulSoup
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

# الكوكي الخاص بك تم دمجه هنا
MY_COOKIE = "PHPSESSID=gnLJ2C YEKFs-aYk; WicaUhziByzwOTq7rZNyoVsTP=21.2pjQwd05vkkSBnWlH02hfVb; 4w9NAlmhgvr7EMykMSe-5gG1uT2MxLYxT9Vc5kEbWCOC=M0q3ArfR8LDRpkA5QD"

# قائمة المستخدمين المسموح لهم (يمكنك إضافة IDs هنا)
ALLOWED_USERS = {ADMIN_ID} 

# دالة جلب البيانات
def get_expired_domains(endpoint, limit=10):
    url = f"https://www.expireddomains.net/domains/{endpoint}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': MY_COOKIE,
        'Referer': 'https://www.expireddomains.net/'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if "Login" in response.text:
            return "❌ انتهت صلاحية الجلسة (الكوكي). يرجى تحديثه من المتصفح."
            
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'listing'})
        if not table: return "⚠️ لا توجد بيانات حالياً في هذا القسم."

        rows = table.find_all('tr')[1:limit+1]
        results = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 5:
                results.append({
                    "domain": cols[0].get_text(strip=True),
                    "bl": cols[1].get_text(strip=True),   # Backlinks
                    "dp": cols[2].get_text(strip=True),   # Domain Pop
                    "status": cols[3].get_text(strip=True) # Date/Status
                })
        return results
    except Exception as e:
        return f"❌ خطأ: {str(e)}"

# --- معالجة الأوامر ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        kb = [
            ['🆕 جلب .com', '🌐 جلب .net'],
            ['⏳ قريباً (Pending)', '➕ إضافة مستخدم'],
            ['➖ حذف مستخدم', '📊 قائمة المستخدمين']
        ]
        msg = "👑 **مرحباً أيها الأدمن**\nالكوكي مربوط وجاهز. تحكم في المستخدمين أو اسحب الدومينات الآن."
    elif user_id in ALLOWED_USERS:
        kb = [['🆕 جلب .com', '🌐 جلب .net'], ['⏳ قريباً (Pending)']]
        msg = "🌟 **مرحباً بك في الخدمة المميزة**\nيمكنك استخراج الدومينات المحذوفة حالياً."
    else:
        await update.message.reply_text("🚫 نعتذر، أنت غير مسجل في الخدمة. تواصل مع الأدمن.")
        return

    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # --- إدارة المستخدمين (للأدمن فقط) ---
    if user_id == ADMIN_ID:
        if text == '➕ إضافة مستخدم':
            await update.message.reply_text("أرسل ID المستخدم المراد إضافته:")
            context.user_data['action'] = 'ADD'
            return
        elif text == '➖ حذف مستخدم':
            await update.message.reply_text("أرسل ID المستخدم المراد حذفه:")
            context.user_data['action'] = 'DEL'
            return
        elif text == '📊 قائمة المستخدمين':
            await update.message.reply_text(f"قائمة المصرح لهم: `{list(ALLOWED_USERS)}`", parse_mode='Markdown')
            return

        if context.user_data.get('action') == 'ADD':
            try:
                new_id = int(text)
                ALLOWED_USERS.add(new_id)
                await update.message.reply_text(f"✅ تم إضافة {new_id} بنجاح.")
            except: await update.message.reply_text("❌ يرجى إرسال ID صحيح (أرقام فقط).")
            context.user_data['action'] = None
            return

    # --- جلب الدومينات ---
    if user_id in ALLOWED_USERS:
        endpoint = ""
        if text == '🆕 جلب .com': endpoint = "expiredcom"
        elif text == '🌐 جلب .net': endpoint = "expirednet"
        elif text == '⏳ قريباً (Pending)': endpoint = "pendingdelete"

        if endpoint:
            m = await update.message.reply_text("⏳ جاري سحب البيانات من الحساب...")
            data = get_expired_domains(endpoint)
            
            if isinstance(data, str):
                await m.edit_text(data)
            else:
                res = f"🎯 **أحدث 10 نتائج ({text}):**\n\n"
                for item in data:
                    res += f"🌐 `{item['domain']}`\n🔗 BL: `{item['bl']}` | 🏗️ DP: `{item['dp']}` | 📅 `{item['status']}`\n\n"
                await m.edit_text(res, parse_mode='Markdown')

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    print("Bot Started...")
    app.run_polling()
