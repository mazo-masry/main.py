import os
import random
import requests
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة أداء Railway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

# رابط الحصول على المفاتيح (للتذكير)
GODADDY_KEYS_URL = "https://developer.godaddy.com/keys"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['🔍 فحص شامل (جميع الامتدادات)'],
            ['📅 مراقبة انتهاء الدومينات الحقيقية'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"🎯 **مرحباً بك في بوت جودادي المحدث.**\n\n"
            f"للحسابات الجديدة، تأكد من إنشاء مفاتيح من نوع **Production**.\n"
            f"رابط المفاتيح: {GODADDY_KEYS_URL}",
            reply_markup=markup, parse_mode='Markdown'
        )

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # --- 1. الفحص الشامل ---
    if text == '🔍 فحص شامل (جميع الامتدادات)':
        await update.message.reply_text("🔑 من فضلك أرسل الـ **API Key**:")
        context.user_data['state'] = 'WAIT_KEY'
        return

    if state == 'WAIT_KEY':
        context.user_data['tmp_key'] = text
        await update.message.reply_text("✅ الآن أرسل الـ **Secret Key**:")
        context.user_data['state'] = 'WAIT_SECRET'
        return

    if state == 'WAIT_SECRET':
        api_key = context.user_data['tmp_key']
        secret_key = text
        context.user_data['state'] = None
        msg = await update.message.reply_text("⏳ جاري الفحص الحقيقي عبر GoDaddy API...")

        # توليد اسم عشوائي للفحص
        base_name = f"brand{random.randint(100, 999)}vibe"
        tlds = [".com", ".net", ".org", ".info", ".xyz"]
        domains = [base_name + tld for tld in tlds]
        
        headers = {"Authorization": f"sso-key {api_key}:{secret_key}", "Accept": "application/json"}
        try:
            url = "https://api.godaddy.com/v1/domains/available"
            res = requests.post(url, json=domains, headers=headers, timeout=15)
            
            if res.status_code == 200:
                results = res.json().get('domains', [])
                report = f"🎯 **نتائج الفحص لـ `{base_name}`:**\n\n"
                for item in results:
                    status = "✅ متاح" if item['available'] else "🔒 محجوز"
                    report += f"{status} | `{item['domain']}`\n"
                await msg.edit_text(report, parse_mode='Markdown')
            elif res.status_code == 403:
                await msg.edit_text("❌ **خطأ 403 (Access Denied):**\nحساب جودادي الخاص بك لا يملك صلاحية استخدام الـ API حالياً. (غالباً تحتاج لشحن رصيد أو شراء دومين أولاً).")
            else:
                await msg.edit_text(f"⚠️ خطأ من جودادي: `{res.status_code}`\nتأكد من صحة المفاتيح.")
        except Exception as e:
            await msg.edit_text(f"❌ حدث خطأ في الاتصال: {str(e)}")
        return

    # --- 2. زر مراقبة الانتهاء ---
    elif text == '📅 مراقبة انتهاء الدومينات الحقيقية':
        if 'tmp_key' not in context.user_data:
            await update.message.reply_text("⚠️ يرجى إدخال المفاتيح عبر زر الفحص أولاً.")
            return
        
        headers = {"Authorization": f"sso-key {context.user_data['tmp_key']}:{context.user_data.get('tmp_secret','')}"}
        try:
            res = requests.get("https://api.godaddy.com/v1/domains?statuses=ACTIVE", headers=headers, timeout=15)
            if res.status_code == 200:
                data = res.json()
                if not data:
                    await update.message.reply_text("📭 لا توجد دومينات مسجلة في هذا الحساب.")
                    return
                report = "📅 **تواريخ انتهاء الدومينات:**\n\n"
                for d in data[:5]:
                    report += f"🌐 `{d['domain']}`\n⌛ ينتهي: `{d['expires'].split('T')[0]}`\n\n"
                await update.message.reply_text(report, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ لم أتمكن من جلب الدومينات. تأكد من صلاحية الحساب.")
        except:
            await update.message.reply_text("❌ خطأ تقني في الجلب.")

    # --- 3. إدارة المستخدمين ---
    elif text.startswith("اضف ") and user_id == ADMIN_ID:
        try:
            new_id = int(text.split(" ")[1])
            ALLOWED_USERS.add(new_id)
            await update.message.reply_text(f"✅ تم تفعيل العضو: `{new_id}`")
        except: pass
    elif text.startswith("احذف ") and user_id == ADMIN_ID:
        try:
            del_id = int(text.split(" ")[1])
            if del_id in ALLOWED_USERS: ALLOWED_USERS.remove(del_id)
            await update.message.reply_text(f"🗑 تم حذف العضو: `{del_id}`")
        except: pass

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        app.run_polling()
