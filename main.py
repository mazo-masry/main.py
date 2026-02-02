import os
import random
import string
import requests
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# تفعيل سجلات الأخطاء
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

def get_domain_info(domain):
    try:
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
        res = requests.get(url, timeout=5)
        if res.status_code == 404:
            return "متاح ✅", "N/A"
        data = res.json()
        expiry = next((e['eventDate'].split('T')[0] for e in data.get('events', []) if e.get('eventAction') == 'expiration'), "غير معروف")
        return "محجوز 🔒", expiry
    except Exception:
        return "خطأ ⚠️", ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['🎯 صيد الدومينات', '💎 قناص الثلاثي'],
            ['🧠 AI مقترحات', '🔍 فحص يدوي'],
            ['➕ إضافة مستخدم', '📋 قائمة المفعلين']
        ]
        if user_id != ADMIN_ID:
            keyboard = [['🎯 صيد الدومينات', '🧠 AI مقترحات'], ['🔍 فحص يدوي']]
        
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("✨ **تم دمج الذكاء الاصطناعي بنجاح!**\nاختر من القائمة المحدثة بالأسفل:", reply_markup=markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(f"🚫 غير مسموح لك.\nID: `{user_id}`")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id == ADMIN_ID:
        if '➕ إضافة' in text:
            await update.message.reply_text("أرسل: `اضف 123456789`")
            return
        elif 'قائمة' in text:
            await update.message.reply_text(f"المفعلين: `{list(ALLOWED_USERS)}`")
            return
        elif text.startswith("اضف "):
            try:
                new_id = int(text.split(" ")[1])
                ALLOWED_USERS.add(new_id)
                await update.message.reply_text(f"✅ تم تفعيل `{new_id}`")
            except: pass
            return

    if user_id not in ALLOWED_USERS: return

    # --- منطق الـ AI المدمج ---
    if 'AI مقترحات' in text:
        msg = await update.message.reply_text("🧠 جاري التفكير بنمط AI لتوليد براندات...")
        prefixes = ["meta", "neo", "zen", "cloud", "fast", "smart", "bit", "pro", "vision", "prime", "nova"]
        suffixes = ["ly", "ify", "hub", "zone", "net", "web", "lab", "tech", "sol", "gen", "base"]
        results = []
        for _ in range(5):
            name = random.choice(prefixes) + random.choice(suffixes) + ".com"
            status, _ = get_domain_info(name)
            results.append(f"✨ `{name}` -> {status}")
        await msg.edit_text("🤖 **مقترحات AI للبراندات:**\n\n" + "\n".join(results), parse_mode='Markdown')

    elif 'صيد الدومينات' in text:
        msg = await update.message.reply_text("📡 جاري القنص...")
        res = [''.join(random.choices(string.ascii_lowercase, k=5)) + ".com" for _ in range(4)]
        await msg.edit_text("🎯 **أهداف متاحة:**\n\n" + "\n".join([f"🔥 `{d}`" for d in res]), parse_mode='Markdown')

    elif 'قناص الثلاثي' in text:
        msg = await update.message.reply_text("💎 جاري البحث...")
        res = [''.join(random.choices(string.ascii_lowercase + string.digits, k=3)) + ".com" for _ in range(5)]
        await msg.edit_text("🎯 **ثلاثي:**\n\n" + "\n".join([f"💎 `{d}`" for d in res]), parse_mode='Markdown')

    elif '.com' in text:
        status, expiry = get_domain_info(text.lower().strip())
        await update.message.reply_text(f"📊 **تقرير:**\n🌐 `{text}`\nالحالة: {status}\nالانتهاء: `{expiry}`", parse_mode='Markdown')

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        app.run_polling(drop_pending_updates=True)
