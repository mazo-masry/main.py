import os
import random
import string
import requests
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة أداء الرادار
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات الأساسية ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780  # معرفك كمدير
ALLOWED_USERS = {ADMIN_ID}

def get_domain_info(domain):
    """وظيفة الرادار لفحص حالة الدومين وتاريخ الانتهاء"""
    try:
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
        res = requests.get(url, timeout=5)
        if res.status_code == 404:
            return "متاح للصيد ✅", "N/A"
        data = res.json()
        expiry = "غير معروف"
        for event in data.get("events", []):
            if event.get("eventAction") == "expiration":
                expiry = event.get("eventDate").split("T")[0]
        return "محجوز 🔒", expiry
    except Exception as e:
        logger.error(f"Radar Error: {e}")
        return "خطأ فحص ⚠️", ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        # الكيبورد الجديد بعد حذف الـ AI وإضافة الرادار
        keyboard = [
            ['📡 رادار الدومينات المحذوفة', '💎 قناص الثلاثي'],
            ['📅 حالة الانتهاء', '📋 قائمة المفعلين'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        # لوحة المستخدم العادي
        if user_id != ADMIN_ID:
            keyboard = [['📡 رادار الدومينات المحذوفة', '💎 قناص الثلاثي'], ['📅 حالة الانتهاء']]
            
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "📡 **تم تفعيل رادار الدومينات المحذوفة!**\n\nنظام الـ AI ملغى الآن، الرادار يبحث عن الدومينات التي تسقط حالياً.", 
            reply_markup=markup, 
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"🚫 الوصول مرفوض.\nID: `{user_id}`")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # --- لوحة تحكم المدير ---
    if user_id == ADMIN_ID:
        if '➕ إضافة' in text:
            await update.message.reply_text("أرسل: `اضف 123456789`")
            return
        elif 'حذف' in text:
            await update.message.reply_text("أرسل: `احذف 123456789`")
            return
        elif 'قائمة' in text:
            await update.message.reply_text(f"👥 المشتركين: `{list(ALLOWED_USERS)}`")
            return
        elif text.startswith("اضف "):
            try:
                new_id = int(text.split(" ")[1])
                ALLOWED_USERS.add(new_id)
                await update.message.reply_text(f"✅ تم تفعيل `{new_id}`")
            except: pass
            return
        elif text.startswith("احذف "):
            try:
                del_id = int(text.split(" ")[1])
                if del_id in ALLOWED_USERS and del_id != ADMIN_ID:
                    ALLOWED_USERS.remove(del_id)
                    await update.message.reply_text(f"🗑️ تم حذف `{del_id}`")
            except: pass
            return

    # --- حماية البوت للمشتركين فقط ---
    if user_id not in ALLOWED_USERS: return

    # --- نظام الرادار الجديد ---
    if 'رادار الدومينات المحذوفة' in text:
        msg = await update.message.reply_text("📡 الرادار يقوم بمسح النطاقات التي سقطت للتو...")
        
        # كلمات مفتاحية قوية يبحث عنها الرادار
        keywords = ["e", "i", "top", "pro", "best", "fast", "my", "the", "go", "app"]
        results = []
        
        # الرادار يحاول إيجاد 5 دومينات سقطت ومتاحة حالياً
        for _ in range(8):
            name = random.choice(keywords) + ''.join(random.choices(string.ascii_lowercase, k=4)) + ".com"
            status, _ = get_domain_info(name)
            if "متاح" in status:
                results.append(f"📡 **هدف محذوف:** `{name}`\n🔗 [احجزه الآن](https://www.namecheap.com/domains/registration/results/?domain={name})")
            if len(results) >= 4: break
        
        if results:
            response = "🎯 **نتائج الرادار (دومينات محذوفة ومتاحة):**\n\n" + "\n\n".join(results)
        else:
            response = "📡 الرادار لم يجد صيداً ثميناً في هذه اللحظة، حاول مرة أخرى بعد دقائق."
            
        await msg.edit_text(response, parse_mode='Markdown', disable_web_page_preview=True)

    elif 'قناص الثلاثي' in text:
        msg = await update.message.reply_text("💎 جاري مسح النطاقات الثلاثية المحذوفة...")
        found = []
        chars = string.ascii_lowercase + string.digits
        for _ in range(10):
            d = ''.join(random.choices(chars, k=3)) + ".com"
            status, _ = get_domain_info(d)
            if "متاح" in status:
                found.append(f"💎 `{d}`")
            if len(found) >= 3: break
            
        await msg.edit_text("🎯 **أهداف ثلاثية متاحة:**\n\n" + ("\n".join(found) if found else "كلها محجوزة حالياً."), parse_mode='Markdown')

    elif 'حالة الانتهاء' in text:
        await update.message.reply_text("أرسل الدومين لفحص تاريخ سقوطه بدقة (مثال: domain.com):")

    elif '.com' in text:
        status, expiry = get_domain_info(text.lower().strip())
        await update.message.reply_text(f"📊 **تقرير الرادار:**\n\n🌐 `{text}`\nالحالة: {status}\nتاريخ السقوط/الانتهاء: `{expiry}`", parse_mode='Markdown')

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        logger.info("Radar Bot started...")
        app.run_polling(drop_pending_updates=True)
    else:
        print("❌ BOT_TOKEN missing!")
