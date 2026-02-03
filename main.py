import os
import requests
from bs4 import BeautifulSoup
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة Railway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

# مخزن البيانات في الذاكرة (سيتم تحديثه عبر التليجرام)
STATE = {
    "cookie": "",
    "allowed_users": {ADMIN_ID}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        kb = [['🚀 جلب البيانات الشاملة'], ['⚙️ تحديث الكوكي', '👥 إدارة الأعضاء']]
        msg = "👑 **لوحة تحكم القناص**\nيرجى تحديث الكوكي أولاً لضمان عمل الجلسة من السيرفر."
    elif user_id in STATE["allowed_users"]:
        kb = [['🚀 جلب البيانات الشاملة']]
        msg = "🌟 **مرحباً بك**\nاضغط على الزر لجلب أحدث الدومينات."
    else:
        await update.message.reply_text("🚫 الوصول مرفوض. تواصل مع الأدمن.")
        return
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    current_state = context.user_data.get('state')

    # --- إدارة الأدمن ---
    if user_id == ADMIN_ID:
        if text == '⚙️ تحديث الكوكي':
            await update.message.reply_text("📥 أرسل الكوكي الجديد بالكامل الآن:")
            context.user_data['state'] = 'WAIT_COOKIE'
            return
        
        if current_state == 'WAIT_COOKIE':
            STATE["cookie"] = text.strip()
            context.user_data['state'] = None
            await update.message.reply_text("✅ تم تحديث الكوكي في ذاكرة السيرفر. جرب السحب الآن!")
            return

        if text == '👥 إدارة الأعضاء':
            await update.message.reply_text("أرسل ID العضو لإضافته/حذفه:")
            context.user_data['state'] = 'MANAGE_USER'
            return
        
        if current_state == 'MANAGE_USER':
            try:
                uid = int(text)
                if uid in STATE["allowed_users"]:
                    STATE["allowed_users"].remove(uid)
                    await update.message.reply_text(f"🗑 تم حذف {uid}")
                else:
                    STATE["allowed_users"].add(uid)
                    await update.message.reply_text(f"✅ تم إضافة {uid}")
            except: await update.message.reply_text("❌ أرسل أرقام فقط.")
            context.user_data['state'] = None
            return

    # --- جلب البيانات ---
    if text == '🚀 جلب البيانات الشاملة' and user_id in STATE["allowed_users"]:
        if not STATE["cookie"]:
            await update.message.reply_text("⚠️ يرجى من الأدمن تحديث الكوكي أولاً.")
            return

        m = await update.message.reply_text("📡 جاري محاكاة الطلب من سيرفر Railway...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Cookie': STATE["cookie"],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://member.expireddomains.net/domains/combinedexpired/',
            'Connection': 'keep-alive'
        }

        try:
            url = "https://member.expireddomains.net/domains/combinedexpired/"
            response = requests.get(url, headers=headers, timeout=20)
            
            if "Login" in response.text or response.status_code == 403:
                await m.edit_text("❌ رفض الجلسة (Session Rejected).\nالموقع اكتشف اختلاف الـ IP بين جهازك والسيرفر.")
                return

            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'class': 'listing'})
            
            if not table:
                await m.edit_text("⚠️ لم يتم العثور على جدول البيانات. تأكد من إعدادات الفلتر في حسابك.")
                return

            rows = table.find_all('tr')[1:21] # جلب أول 20 دومين
            report = "📊 **نتائج البحث الشامل:**\n\n"
            for row in rows:
                cols = row.find_all('td')
                if len(cols) > 5:
                    domain = cols[0].get_text(strip=True)
                    bl = cols[1].get_text(strip=True)
                    status = cols[-1].get_text(strip=True)
                    report += f"🌐 `{domain}` | 🔗 BL: {bl} | 📝 {status}\n"

            await update.message.reply_text(report, parse_mode='Markdown')
            await m.delete()

        except Exception as e:
            await m.edit_text(f"❌ خطأ اتصال: {str(e)}")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    app.run_polling()
