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

# رابط الحصول على المفاتيح
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
            f"🎯 **مرحباً بك في بوت جودادي المتكامل.**\n\n"
            f"يمكنك الحصول على مفاتيح API من هنا:\n{GODADDY_KEYS_URL}\n\n"
            f"استخدم الأزرار بالأسفل للتحكم الكامل.",
            reply_markup=markup, parse_mode='Markdown'
        )

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get('state')

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # --- 1. الفحص الشامل لجميع الامتدادات ---
    if text == '🔍 فحص شامل (جميع الامتدادات)':
        await update.message.reply_text(f"🔑 أرسل الـ **API Key** (يمكنك جلبها من: {GODADDY_KEYS_URL}):")
        context.user_data['state'] = 'WAIT_KEY_ALL'
        return

    if state == 'WAIT_KEY_ALL':
        context.user_data['tmp_key'] = text
        await update.message.reply_text("✅ الآن أرسل الـ **Secret Key**:")
        context.user_data['state'] = 'WAIT_SECRET_ALL'
        return

    if state == 'WAIT_SECRET_ALL':
        api_key = context.user_data['tmp_key']
        secret_key = text
        context.user_data['state'] = None
        msg = await update.message.reply_text("⏳ جاري توليد وفحص دومينات بمختلف الامتدادات...")

        # توليد اسم وفحصه بعدة امتدادات
        base_name = f"brand{random.randint(100, 999)}"
        tlds = [".com", ".net", ".org", ".info", ".xyz", ".me", ".tech"]
        domains = [base_name + tld for tld in tlds]
        
        headers = {"Authorization": f"sso-key {api_key}:{secret_key}"}
        try:
            url = "https://api.godaddy.com/v1/domains/available"
            res = requests.post(url, json=domains, headers=headers, timeout=20)
            if res.status_code == 200:
                results = res.json().get('domains', [])
                report = f"🎯 **نتائج الفحص الشامل لـ `{base_name}`:**\n\n"
                for item in results:
                    status = "✅ متاح" if item['available'] else "🔒 Taken"
                    report += f"{status} | `{item['domain']}`\n"
                await msg.edit_text(report, parse_mode='Markdown')
            else:
                await msg.edit_text("❌ خطأ في المفاتيح أو التصريح من جودادي.")
        except:
            await msg.edit_text("⚠️ حدث خطأ في الاتصال.")
        return

    # --- 2. زر انتهاء الدومين (بيانات حقيقية) ---
    elif text == '📅 مراقبة انتهاء الدومينات الحقيقية':
        if 'tmp_key' not in context.user_data:
            await update.message.reply_text("⚠️ يرجى استخدام زر الفحص أولاً لإدخال المفاتيح.")
            return
        
        msg = await update.message.reply_text("🔎 جاري جلب تواريخ انتهاء الدومينات المرتبطة بحسابك...")
        headers = {"Authorization": f"sso-key {context.user_data['tmp_key']}:{context.user_data.get('tmp_secret','')}"}
        
        try:
            # جلب قائمة الدومينات المملوكة للحساب لمعرفة تاريخ انتهائها
            url = "https://api.godaddy.com/v1/domains?statuses=ACTIVE"
            res = requests.get(url, headers=headers, timeout=20)
            if res.status_code == 200:
                data = res.json()
                if not data:
                    await msg.edit_text("📭 لا توجد دومينات نشطة في هذا الحساب حالياً.")
                    return
                report = "📅 **مواعيد انتهاء دوميناتك:**\n\n"
                for dom in data[:10]: # عرض أول 10 دومينات
                    report += f"🌐 `{dom['domain']}`\n📅 ينتهي في: `{dom['expires'].split('T')[0]}`\n\n"
                await msg.edit_text(report, parse_mode='Markdown')
            else:
                await msg.edit_text("❌ فشل جلب البيانات. تأكد من أن المفاتيح لها صلاحية الوصول للدومينات.")
        except:
            await msg.edit_text("❌ حدث خطأ تقني.")

    # --- 3. إدارة المستخدمين (إضافة وحذف) ---
    elif text == '➕ إضافة مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل المعرف للإضافة هكذا: `اضف 12345`", parse_mode='Markdown')
    elif text == '➖ حذف مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل المعرف للحذف هكذا: `احذف 12345`", parse_mode='Markdown')
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
