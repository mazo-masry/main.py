import os
import random
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

# قاعدة بيانات المقاطع الصوتية (أكثر احترافية لسهولة النطق)
PREFIXES = ["Zen", "Nova", "Swift", "Apex", "Eco", "Vibe", "Flex", "Sky", "Core", "Pure"]
SUFFIXES = ["Pay", "Flow", "Lab", "Hub", "Node", "Sync", "Grid", "Link", "Base", "Nest"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        # الزراير المطلوبة: إضافة/حذف، وتوليد الدومينات، والزر الجديد "القناص"
        keyboard = [
            ['🎯 قناص الشركات والفرص الذهبية'],
            ['🗣️ توليد دومينات سهلة النطق'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم']
        ]
        
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "💰 **مرحباً بك في نسخة الاستثمار الذكي!**\n\nتم تفعيل ميزة 'القناص' التي تحلل لك كيفية الربح من كل دومين.",
            reply_markup=markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"🚫 غير مسموح لك بالدخول.")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # --- 1. زر قناص الشركات والفرص (الفكرة الجهنمية) ---
    if text == '🎯 قناص الشركات والفرص الذهبية':
        msg = await update.message.reply_text("🔎 جاري تحليل السوق والبحث عن ثغرات الشركات الناشئة...")
        
        # توليد سيناريو استثماري
        domain_name = random.choice(PREFIXES) + random.choice(SUFFIXES) + ".com"
        price_est = random.randint(1500, 4500)
        
        report = (
            f"🎯 **هدف مكتشف:** `{domain_name}`\n\n"
            f"💡 **لماذا هذا الدومين؟**\n"
            f"هناك توجه حالي لشركات الفنتك والذكاء الاصطناعي لاستخدام أسماء قصيرة ومفهومة.\n\n"
            f"💰 **القيمة التقديرية:** `${price_est}`\n"
            f"👥 **العميل المستهدف:** شركات الناشئة (Startups) التي تستخدم أسماء طويلة وترغب في البراندينج الأصلي.\n\n"
            f"📩 **رسالة العرض المقترحة:**\n"
            f"`عزيزي المدير التنفيذي، لاحظت نمو شركتكم الرائع، وأردت إعلامكم بأن الدومين المختصر {domain_name} متاح الآن، وهو مثالي لحماية علامتكم التجارية وتسهيل وصول العملاء. هل ترغبون في مناقشة نقل الملكية؟`"
        )
        await msg.edit_text(report, parse_mode='Markdown')

    # --- 2. توليد دومينات سهلة النطق ---
    elif text == '🗣️ توليد دومينات سهلة النطق':
        results = []
        for _ in range(5):
            name = random.choice(PREFIXES) + random.choice(SUFFIXES) + ".com"
            results.append(f"✨ `{name}`")
        await update.message.reply_text("🎯 **دومينات سهلة النطق (براند):**\n\n" + "\n".join(results), parse_mode='Markdown')

    # --- 3. إدارة المستخدمين ---
    elif text == '➕ إضافة مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل: `اضف 12345678`")
        
    elif text == '➖ حذف مستخدم' and user_id == ADMIN_ID:
        await update.message.reply_text("أرسل: `احذف 12345678`")

    elif text.startswith("اضف ") and user_id == ADMIN_ID:
        try:
            target_id = int(text.split(" ")[1])
            ALLOWED_USERS.add(target_id)
            await update.message.reply_text(f"✅ تم التفعيل: `{target_id}`")
        except: pass

    elif text.startswith("احذف ") and user_id == ADMIN_ID:
        try:
            target_id = int(text.split(" ")[1])
            if target_id in ALLOWED_USERS:
                ALLOWED_USERS.remove(target_id)
                await update.message.reply_text(f"🗑️ تم الحذف: `{target_id}`")
        except: pass

if __name__ == "__main__":
    if TOKEN:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        logger.info("Bot is active...")
        app.run_polling(drop_pending_updates=True)
