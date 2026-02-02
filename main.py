import os
import random
import requests
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

# تخزين مؤقت للمفاتيح في الذاكرة
user_api_data = {}

def generate_50_names():
    prefixes = ["Nova", "Sky", "Zen", "Flex", "Core", "Swift", "Peak", "Glow"]
    suffixes = ["ify", "ly", "hub", "lab", "net", "zone", "base", "vibe"]
    names = []
    for _ in range(50):
        name = random.choice(prefixes).lower() + random.choice(suffixes).lower() + str(random.randint(10, 99)) + ".com"
        names.append(name)
    return names

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['🔍 توليد وفحص 50 دومين (GoDaddy)'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "✅ **بوت فحص جودادي الحقيقي مفعّل.**\nاضغط على الزر لبدء إدخال مفاتيح الـ API الخاصة بك.",
            reply_markup=markup, parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # --- بدء عملية طلب المفاتيح ---
    if text == '🔍 توليد وفحص 50 دومين (GoDaddy)':
        await update.message.reply_text("🔑 من فضلك أرسل الـ **API Key** الخاص بك من جودادي:")
        context.user_data['state'] = 'WAIT_KEY'
        return

    if state == 'WAIT_KEY':
        context.user_data['tmp_key'] = text
        await update.message.reply_text("✅ تمام، الآن أرسل الـ **Secret Key**:")
        context.user_data['state'] = 'WAIT_SECRET'
        return

    if state == 'WAIT_SECRET':
        api_key = context.user_data['tmp_key']
        secret_key = text
        context.user_data['state'] = None
        
        msg = await update.message.reply_text("⏳ جاري توليد 50 اسماً وفحصهم عبر GoDaddy API...")
        
        domains = generate_50_names()
        headers = {
            "Authorization": f"sso-key {api_key}:{secret_key}",
            "Accept": "application/json"
        }
        
        try:
            # استخدام نظام الـ Bulk Check في جودادي لفحص 50 دومين بطلبية واحدة
            url = "https://api.godaddy.com/v1/domains/available"
            response = requests.post(url, json=domains, headers=headers, timeout=20)
            
            if response.status_code == 200:
                results = response.json().get('domains', [])
                report = "🎯 **نتائج الفحص الحقيقي من جودادي:**\n\n"
                
                found_any = False
                for item in results:
                    if item['available']:
                        report += f"✅ متاح | `{item['domain']}`\n"
                        found_any = True
                
                if not found_any:
                    report += "🔒 للأسف، جميع الدومينات الـ 50 محجوزة حالياً."
                
                await msg.edit_text(report, parse_mode='Markdown')
            else:
                await msg.edit_text(f"❌ خطأ في API جودادي: {response.status_code}\nتأكد أن المفاتيح من نوع **Production** وليست Test.")
        except Exception as e:
            await msg.edit_text(f"⚠️ حدث خطأ أثناء الاتصال: {str(e)}")
        return

    # --- إدارة المستخدمين ---
    if text.startswith("اضف ") and user_id == ADMIN_ID:
        try:
            new_id = int(text.split(" ")[1])
            ALLOWED_USERS.add(new_id)
            await update.message.reply_text(f"✅ تم تفعيل العضو: `{new_id}`")
        except: pass

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.run_polling()
