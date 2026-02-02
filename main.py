import os
import random
import requests
import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

# تخزين مفاتيح API مؤقتاً في الذاكرة (يفضل استخدام قاعدة بيانات في الإنتاج)
user_keys = {} 

# مقاطع لتوليد أسماء سهلة النطق
VOWELS = "aeiou"
CONSONANTS = "bcdfghjklmnpqrstvwxyz"

def generate_brandable_name():
    """توليد اسم سهل النطق (مزيج من مقاطع مفهومة)"""
    parts = ["nova", "sky", "zen", "flex", "core", "vibe", "swift", "peak", "glow", "flux"]
    endings = ["ly", "ify", "io", "lab", "hub", "net", "zone", "base"]
    return random.choice(parts) + random.choice(endings) + ".com"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['📅 مراقبة انتهاء دومينات جودادي'],
            ['🔍 توليد وفحص 50 دومين (GoDaddy)'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "⚙️ **أهلاً بك في نظام GoDaddy المتطور.**\n\nللبدء، سأحتاج لمفاتيح API الخاصة بك للفحص الحقيقي.",
            reply_markup=markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"🚫 غير مصرح لك.\nID: `{user_id}`")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # --- نظام طلب المفاتيح ---
    if text == '🔍 توليد وفحص 50 دومين (GoDaddy)' or text == '📅 مراقبة انتهاء دومينات جودادي':
        if user_id not in user_keys:
            await update.message.reply_text(
                "🔗 **كيف تحصل على المفاتيح؟**\n1. ادخل على [GoDaddy Developer Portal](https://developer.godaddy.com/keys)\n2. قم بإنشاء مفتاح (Production).\n\n**الآن أرسل الـ API Key أولاً:**",
                disable_web_page_preview=True
            )
            context.user_data['state'] = 'WAITING_API_KEY'
            context.user_data['action'] = text
            return
    
    if state == 'WAITING_API_KEY':
        context.user_data['api_key'] = text
        await update.message.reply_text("✅ تم الاستلام. الآن أرسل الـ **Secret Key**:")
        context.user_data['state'] = 'WAITING_SECRET_KEY'
        return

    if state == 'WAITING_SECRET_KEY':
        user_keys[user_id] = {
            'api_key': context.user_data['api_key'],
            'secret_key': text
        }
        context.user_data['state'] = None
        await update.message.reply_text("🚀 ممتاز! المفاتيح جاهزة. اضغط على الزر مرة أخرى لبدء العملية.")
        return

    # --- 1. توليد وفحص 50 دومين عبر جودادي ---
    if text == '🔍 توليد وفحص 50 دومين (GoDaddy)':
        keys = user_keys.get(user_id)
        msg = await update.message.reply_text("🔄 جاري توليد 50 اسماً وفحصها عبر API جودادي...")
        
        domains_to_check = [generate_brandable_name() for _ in range(50)]
        headers = {
            "Authorization": f"sso-key {keys['api_key']}:{keys['secret_key']}",
            "Accept": "application/json"
        }
        
        results = []
        # فحص جودادي يسمح بكتل برمجية (Bulk Check)
        try:
            url = "https://api.godaddy.com/v1/domains/available"
            response = requests.post(url, json=domains_to_check, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json().get('domains', [])
                for item in data:
                    if item['available']:
                        results.append(f"✅ `{item['domain']}` - ${item['price']/1000000:.2f}")
            else:
                await msg.edit_text(f"❌ خطأ من جودادي: {response.text}")
                return
        except Exception as e:
            await msg.edit_text(f"❌ حدث خطأ في الاتصال: {str(e)}")
            return

        report = "🎯 **نتائج الفحص (متاح):**\n\n" + ("\n".join(results[:15]) if results else "لم أجد دومينات متاحة في هذه الدفعة.")
        await msg.edit_text(report, parse_mode='Markdown')

    # --- 2. مراقبة الانتهاء (Expirations) ---
    elif text == '📅 مراقبة انتهاء دومينات جودادي':
        keys = user_keys.get(user_id)
        headers = {"Authorization": f"sso-key {keys['api_key']}:{keys['secret_key']}"}
        msg = await update.message.reply_text("⏳ جاري جلب قائمة الدومينات القريبة من الانتهاء...")
        
        try:
            url = "https://api.godaddy.com/v1/domains?statuses=ACTIVE"
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                domains = res.json()
                report = "📅 **مواعيد الانتهاء:**\n\n"
                for d in domains[:10]:
                    report += f"🌐 `{d['domain']}`\n🗓 ينتهي في: `{d['expires'][:10]}`\n\n"
                await msg.edit_text(report, parse_mode='Markdown')
            else:
                await msg.edit_text("❌ لم أتمكن من جلب البيانات. تأكد من صحة المفاتيح.")
        except:
            await msg.edit_text("❌ حدث خطأ.")

    # --- إدارة المستخدمين ---
    elif text == '➕ إضافة مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل: `اضف ID`")
    elif text == '➖ حذف مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل: `احذف ID`")
    elif text.startswith("اضف "):
        new_id = int(text.split(" ")[1])
        ALLOWED_USERS.add(new_id)
        await update.message.reply_text(f"✅ تم تفعيل {new_id}")
    elif text.startswith("احذف "):
        del_id = int(text.split(" ")[1])
        ALLOWED_USERS.remove(del_id)
        await update.message.reply_text(f"🗑 تم حذف {del_id}")

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        app.run_polling(drop_pending_updates=True)
