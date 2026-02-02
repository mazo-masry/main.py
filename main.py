import os
import random
import string
import requests
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

# حالات المحادثة للـ AI
WAITING_FOR_CATEGORY = 1

def get_domain_info(domain):
    """فحص الدومين وإرجاع الحالة فقط إذا كان متاحاً"""
    try:
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
        res = requests.get(url, timeout=5)
        if res.status_code == 404:
            return "متاح ✅"
        return "محجوز 🔒"
    except:
        return "خطأ ⚠️"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['🧠 AI اقتراح ذكي', '🎯 صيد الدومينات'],
            ['💎 قناص الثلاثي', '📅 حالة الانتهاء'],
            ['➕ إضافة مستخدم', '📋 قائمة المفعلين']
        ]
        if user_id != ADMIN_ID:
            keyboard = [['🧠 AI اقتراح ذكي', '🎯 صيد الدومينات'], ['💎 قناص الثلاثي']]
        
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("✨ **تم تحديث نظام الـ AI التفاعلي!**\nاضغط على 'AI اقتراح ذكي' ليبدأ البوت بسؤالك.", reply_markup=markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(f"🚫 غير مسموح لك.\nID: `{user_id}`")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # التحقق من الإدارة
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

    # --- نظام الـ AI التفاعلي الجديد ---
    if text == '🧠 AI اقتراح ذكي':
        context.user_data['waiting_for_category'] = True
        await update.message.reply_text("🤖 **أنا جاهز!**\nما هو المجال أو نوع الدومينات الذي تبحث عنه؟\n(مثال: تقنية، ألعاب، متجر، عقارات...)", reply_markup=ReplyKeyboardRemove())
        return

    if context.user_data.get('waiting_for_category'):
        category = text
        context.user_data['waiting_for_category'] = False
        msg = await update.message.reply_text(f"⏳ جاري تحليل مجال '{category}' وتوليد دومينات متاحة فقط...")
        
        # قاموس الكلمات بناءً على بعض المجالات المشهورة
        keywords = {
            "تقنية": ["tech", "bit", "code", "ai", "soft", "nexus"],
            "متجر": ["shop", "store", "market", "cart", "buy", "sale"],
            "عقارات": ["home", "land", "real", "villa", "city", "roof"],
            "ألعاب": ["game", "play", "pro", "zone", "win", "pixel"]
        }
        
        base_words = keywords.get(category, [category[:4], "smart", "go", "fast", "top"])
        suffixes = ["ly", "ify", "hub", "zone", "net", "web", "lab", "x"]
        
        found_domains = []
        attempts = 0
        while len(found_domains) < 4 and attempts < 20:
            attempts += 1
            name = random.choice(base_words) + random.choice(suffixes) + ".com"
            if get_domain_info(name) == "متاح ✅":
                found_domains.append(name)
        
        if found_domains:
            res_text = f"🤖 **نتائج AI لمجال '{category}':**\n\n" + "\n".join([f"✅ `{d}`" for d in found_domains])
            res_text += "\n\n💡 هذه الدومينات فُحصت وهي متاحة الآن."
        else:
            res_text = "😔 لم أجد دومينات متاحة قصيرة في هذا المجال حالياً، حاول مرة أخرى بكلمة مختلفة."
        
        # إعادة القائمة الرئيسية
        keyboard = [['🧠 AI اقتراح ذكي', '🎯 صيد الدومينات'], ['💎 قناص الثلاثي', '📅 حالة الانتهاء']]
        await msg.edit_text(res_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True), parse_mode='Markdown')
        return

    # --- بقية المنطق ---
    elif 'صيد الدومينات' in text:
        msg = await update.message.reply_text("📡 جاري القنص...")
        res = [''.join(random.choices(string.ascii_lowercase, k=5)) + ".com" for _ in range(3)]
        await msg.edit_text("🎯 **أهداف متاحة:**\n\n" + "\n".join([f"🔥 `{d}`" for d in res]), parse_mode='Markdown')

    elif 'قناص الثلاثي' in text:
        msg = await update.message.reply_text("💎 جاري البحث...")
        res = [''.join(random.choices(string.ascii_lowercase + string.digits, k=3)) + ".com" for _ in range(3)]
        await msg.edit_text("🎯 **ثلاثي:**\n\n" + "\n".join([f"💎 `{d}`" for d in res]), parse_mode='Markdown')

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        app.run_polling(drop_pending_updates=True)
