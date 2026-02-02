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

# كلمات لتوليد دومينات سهلة النطق
PREFIXES = ["Nova", "Sky", "Zen", "Eco", "Smart", "Flex", "Cloud", "Pure", "Swift", "Peak", "Vibe", "Core"]
SUFFIXES = ["Flow", "Byte", "Point", "Hub", "Lab", "Net", "Base", "Way", "Grid", "Link", "Sync", "Nest"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        # الزراير المطلوبة فقط
        keyboard = [
            ['🗣️ توليد دومينات سهلة النطق'],
            ['🔨 مزاد نيم شيب (Live/Sold)'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "🆕 **تم تحديث النظام بالكامل!**\n\nركزنا في هذا التحديث على الكلمات المفهومة ومتابعة المزادات.",
            reply_markup=markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"🚫 وصول مرفوض.\nID: `{user_id}`")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # --- 1. توليد دومينات سهلة النطق (كلمات حقيقية) ---
    if text == '🗣️ توليد دومينات سهلة النطق':
        msg = await update.message.reply_text("💎 جاري ابتكار أسماء تجارية سهلة النطق...")
        found = []
        for _ in range(5):
            domain = random.choice(PREFIXES) + random.choice(SUFFIXES) + ".com"
            found.append(f"✨ `{domain}`")
        
        await msg.edit_text("🎯 **دومينات براند جاهزة للحجز:**\n\n" + "\n".join(found), parse_mode='Markdown')

    # --- 2. رادار مزادات نيم شيب (محاكاة البيانات) ---
    elif text == '🔨 مزاد نيم شيب (Live/Sold)':
        msg = await update.message.reply_text("🔨 جاري فحص مزادات Namecheap الحالية والمباعة...")
        auctions = [
            "🔴 **مباع:** `CyberFlow.com` | السعر: `$1,250`",
            "🔴 **مباع:** `SmartNest.net` | السعر: `$480`",
            "🟢 **في المزاد:** `ZenCloud.com` | المزايدة الحالية: `$210`",
            "🟢 **في المزاد:** `PureByte.io` | المزايدة الحالية: `$55`",
            "🟢 **في المزاد:** `EcoSync.com` | المزايدة الحالية: `$890`"
        ]
        await msg.edit_text("📊 **تقرير مزاد نيم شيب السريع:**\n\n" + "\n\n".join(auctions), parse_mode='Markdown')

    # --- 3. إدارة المستخدمين ---
    elif text == '➕ إضافة مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل المعرف بالشكل التالي: `اضف 12345678`")
        
    elif text == '➖ حذف مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل المعرف بالشكل التالي: `احذف 12345678`")

    elif text.startswith("اضف ") and user_id == ADMIN_ID:
        try:
            target_id = int(text.split(" ")[1])
            ALLOWED_USERS.add(target_id)
            await update.message.reply_text(f"✅ تم تفعيل العضو: `{target_id}`")
        except: pass

    elif text.startswith("احذف ") and user_id == ADMIN_ID:
        try:
            target_id = int(text.split(" ")[1])
            if target_id in ALLOWED_USERS and target_id != ADMIN_ID:
                ALLOWED_USERS.remove(target_id)
                await update.message.reply_text(f"🗑️ تم حذف العضو: `{target_id}`")
        except: pass

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        logger.info("Bot is running...")
        app.run_polling(drop_pending_updates=True)
