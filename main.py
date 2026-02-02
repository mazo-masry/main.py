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

# تخزين المفاتيح
user_keys = {}

def generate_easy_name():
    """توليد أسماء براندات حقيقية وسهلة النطق"""
    vowels = "aeiou"
    consonants = "bcdfghjklmnpqrstvwxyz"
    prefixes = ["nova", "sky", "zen", "flex", "core", "vibe", "swift", "peak", "glow", "flux"]
    suffixes = ["ly", "ify", "io", "lab", "hub", "net", "zone", "base"]
    
    structure = random.choice([1, 2])
    if structure == 1:
        return random.choice(prefixes) + random.choice(suffixes) + ".com"
    else:
        # توليد كلمة متناغمة (ساكن-متحرك-ساكن-متحرك)
        name = "".join([random.choice(consonants), random.choice(vowels), random.choice(consonants), random.choice(vowels)])
        return name + random.choice(["ly", "ix", "o"]) + ".com"

def check_domain_status(domain, api_key=None, secret_key=None):
    """فحص الدومين عبر GoDaddy API أو RDAP كبديل"""
    if api_key and secret_key:
        try:
            url = f"https://api.godaddy.com/v1/domains/available?domain={domain}"
            headers = {"Authorization": f"sso-key {api_key}:{secret_key}"}
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                return "متاح ✅" if data.get('available') else "محجوز 🔒"
        except:
            pass
    
    # البديل في حال فشل API أو ACCESS DENIED
    try:
        res = requests.get(f"https://rdap.verisign.com/com/v1/domain/{domain}", timeout=5)
        return "محجوز 🔒" if res.status_code == 200 else "متاح ✅"
    except:
        return "خطأ فحص ⚠️"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in ALLOWED_USERS or user_id == ADMIN_ID:
        keyboard = [['📅 مراقبة انتهاء دومينات جودادي'], ['🔍 توليد وفحص 50 دومين (GoDaddy)'], ['➕ إضافة مستخدم', '➖ حذف مستخدم']]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("🚀 **بوت صيد الدومينات جاهز!**\n\nاضغط على الزر للبدء. إذا واجهت 'Access Denied'، تأكد أن مفاتيحك من نوع **Production**.", reply_markup=markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(f"🚫 غير مصرح لك.\nID: `{user_id}`")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # --- إدارة إدخال المفاتيح ---
    if text in ['🔍 توليد وفحص 50 دومين (GoDaddy)', '📅 مراقبة انتهاء دومينات جودادي'] and user_id not in user_keys:
        await update.message.reply_text("🔑 أرسل الـ **API Key** أولاً:")
        context.user_data['state'] = 'WAIT_API'
        context.user_data['next_action'] = text
        return

    if state == 'WAIT_API':
        context.user_data['tmp_api'] = text
        await update.message.reply_text("✅ تمام، الآن أرسل الـ **Secret Key**:")
        context.user_data['state'] = 'WAIT_SECRET'
        return

    if state == 'WAIT_SECRET':
        user_keys[user_id] = {'key': context.user_data['tmp_api'], 'secret': text}
        context.user_data['state'] = None
        await update.message.reply_text("🚀 تم حفظ المفاتيح! اضغط على الزر مرة أخرى لبدء الفحص.")
        return

    # --- العمليات الأساسية ---
    if text == '🔍 توليد وفحص 50 دومين (GoDaddy)':
        msg = await update.message.reply_text("⏳ جاري توليد 50 اسماً وفحصهم (قد يستغرق ذلك دقيقة)...")
        keys = user_keys.get(user_id, {})
        
        found = []
        for _ in range(50):
            d = generate_easy_name()
            status = check_domain_status(d, keys.get('key'), keys.get('secret'))
            if status == "متاح ✅":
                found.append(f"✅ `{d}`")
            if len(found) >= 15: break # عرض أول 15 متاح لتجنب الرسائل الطويلة
            
        report = "🎯 **نتائج الفحص الذكي:**\n\n" + ("\n".join(found) if found else "لم أجد متاح حالياً، حاول مرة أخرى.")
        await msg.edit_text(report, parse_mode='Markdown')

    elif text == '📅 مراقبة انتهاء دومينات جودادي':
        keys = user_keys.get(user_id, {})
        headers = {"Authorization": f"sso-key {keys.get('key')}:{keys.get('secret')}"}
        try:
            res = requests.get("https://api.godaddy.com/v1/domains?statuses=ACTIVE", headers=headers, timeout=10)
            if res.status_code == 200:
                domains = res.json()
                report = "📅 **مواعيد الانتهاء الحالية:**\n\n"
                for d in domains[:10]:
                    report += f"🌐 `{d['domain']}`\n🗓 ينتهي في: `{d['expires'][:10]}`\n\n"
                await update.message.reply_text(report, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ فشل الجلب من جودادي. سيتم الفحص العام قريباً.")
        except:
            await update.message.reply_text("⚠️ خطأ في الاتصال.")

    # --- إدارة المستخدمين ---
    elif text == '➕ إضافة مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل: `اضف 12345`")
    elif text.startswith("اضف "):
        new_id = int(text.split(" ")[1])
        ALLOWED_USERS.add(new_id)
        await update.message.reply_text(f"✅ تم تفعيل {new_id}")
    elif text == '➖ حذف مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل: `احذف 12345`")
    elif text.startswith("احذف "):
        del_id = int(text.split(" ")[1])
        if del_id in ALLOWED_USERS: ALLOWED_USERS.remove(del_id)
        await update.message.reply_text(f"🗑 تم حذف {del_id}")

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        app.run_polling(drop_pending_updates=True)
