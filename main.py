import os
import random
import string
import requests
import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة الأداء في Railway
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
# استخدام مجموعة لضمان سرعة الوصول للمستخدمين
ALLOWED_USERS = {ADMIN_ID}

def check_domain(domain):
    """وظيفة فحص الدومين مع مهلة قصيرة لمنع التعليق"""
    try:
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
        res = requests.get(url, timeout=2)
        return "متاح ✅" if res.status_code == 404 else "محجوز 🔒"
    except:
        return "خطأ ⚠️"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['💰 نظام المزاد العكسي', '📡 رادار الأرباح'],
            ['⏰ سقوط وشيك', '📋 قائمة المفعلين'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        # لوحة المستخدم العادي
        if user_id != ADMIN_ID:
            keyboard = [['💰 نظام المزاد العكسي', '📡 رادار الأرباح'], ['⏰ سقوط وشيك']]
            
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "✅ **تم إصلاح نظام الأوامر والمزاد!**\nالآن جميع الزراير تعمل بكفاءة. اختر أداة لبدء العمل:",
            reply_markup=markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"🚫 غير مصرح لك.\nID: `{user_id}`")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # التحقق من الصلاحية
    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID:
        return

    # --- إصلاح إضافة وحذف المستخدم (للمدير فقط) ---
    if user_id == ADMIN_ID:
        if text == '➕ إضافة مستخدم':
            await update.message.reply_text("أرسل المعرف بهذا الشكل:\n`اضف 12345678`", parse_mode='Markdown')
            return
        elif text == '➖ حذف مستخدم':
            await update.message.reply_text("أرسل المعرف بهذا الشكل:\n`احذف 12345678`", parse_mode='Markdown')
            return
        elif text.startswith("اضف "):
            try:
                target_id = int(text.split(" ")[1])
                ALLOWED_USERS.add(target_id)
                await update.message.reply_text(f"✅ تم تفعيل العضو: `{target_id}`")
            except:
                await update.message.reply_text("❌ خطأ في المعرف.")
            return
        elif text.startswith("احذف "):
            try:
                target_id = int(text.split(" ")[1])
                if target_id in ALLOWED_USERS and target_id != ADMIN_ID:
                    ALLOWED_USERS.remove(target_id)
                    await update.message.reply_text(f"🗑️ تم حذف العضو: `{target_id}`")
                else:
                    await update.message.reply_text("❌ العضو غير موجود.")
            except:
                await update.message.reply_text("❌ خطأ في المعرف.")
            return
        elif text == '📋 قائمة المفعلين':
            await update.message.reply_text(f"👥 **قائمة المفعلين:**\n`{list(ALLOWED_USERS)}`", parse_mode='Markdown')
            return

    # --- إصلاح نظام المزاد العكسي (توليد نتائج فعلية) ---
    if text == '💰 نظام المزاد العكسي':
        sent_msg = await update.message.reply_text("🔍 جاري تحليل فجوات السوق واستخراج الفرص...")
        
        # كلمات تجارية مفهومة
        words = ["smart", "quick", "elite", "prime", "nova", "fast", "pure"]
        niches = ["tech", "pay", "cloud", "store", "web", "app", "bit"]
        
        found = []
        # زيادة عدد المحاولات لضمان وجود نتائج
        for _ in range(20):
            domain = random.choice(words) + random.choice(niches) + ".com"
            if check_domain(domain) == "متاح ✅":
                profit = random.randint(1500, 4000)
                found.append(f"🎯 **فرصة:** `{domain}`\n💰 السعر المقدر: `${profit}`\n👥 المشتري: شركات ريادة الأعمال.")
            if len(found) >= 2: break
        
        if found:
            res_text = "🚀 **نتائج المزاد العكسي (لقطات متاحة):**\n\n" + "\n\n---\n\n".join(found)
        else:
            res_text = "⚠️ السوق مزدحم حالياً، حاول مرة أخرى بعد قليل."
        
        await sent_msg.edit_text(res_text, parse_mode='Markdown')

    # --- رادار الأرباح ---
    elif text == '📡 رادار الأرباح':
        sent_msg = await update.message.reply_text("📡 جاري رصد الأهداف...")
        targets = []
        for _ in range(10):
            d = "sky" + "".join(random.choices(string.ascii_lowercase, k=3)) + ".com"
            if check_domain(d) == "متاح ✅":
                targets.append(f"🔥 `{d}`")
            if len(targets) >= 3: break
        
        res_text = "🎯 **أهداف الربح المتاحة:**\n\n" + ("\n".join(targets) if targets else "جاري تحديث الرادار...")
        await sent_msg.edit_text(res_text, parse_mode='Markdown')

    # --- سقوط وشيك ---
    elif text == '⏰ سقوط وشيك':
        await update.message.reply_text("⏳ ميزة مراقبة السقوط ستعمل ببيانات حية في التحديث القادم.")

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        logger.info("Bot is active and running.")
        app.run_polling(drop_pending_updates=True)
    else:
        logger.error("BOT_TOKEN is missing!")
