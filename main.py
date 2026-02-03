import os
import random
import socket
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

# قاعدة بيانات المستخدمين
ALLOWED_USERS = {ADMIN_ID}

# قاموس الكلمات لتوليد البراندات (تم إضافة قسم الخليج)
BRAND_DATA = {
    "مصانع": ["Mfg", "Fab", "Ind", "Works", "Tech", "Line", "Forge", "Mill"],
    "مطاعم": ["Tasty", "Bite", "Chef", "Dish", "Eats", "Grill", "Foody", "Kitchen"],
    "ملابس": ["Wear", "Style", "Fit", "Vogue", "Thread", "Apparel", "Fabric"],
    "تعبئة": ["Pack", "Wrap", "Box", "Fill", "Seal", "Flow", "Case"],
    "شحن": ["Ship", "Logix", "Cargo", "Move", "Fast", "Route", "Post"],
    "توصيل": ["Dash", "Drop", "Swift", "Zoom", "Go", "Fetch", "Way"],
    "مستشفيات": ["Med", "Care", "Health", "Cure", "Clinic", "Life", "Heal"],
    "AI": ["AI", "Bot", "Neural", "Mind", "Logic", "Data", "Smart", "IQ"],
    "نجارة": ["Wood", "Craft", "Timber", "Build", "Oak", "Join", "Saw"],
    "الخليج": ["Dubai", "DXB", "Riyadh", "Najd", "Gulf", "Khaleeji", "Emirates", "Saudi", "Capital", "Elite"]
}

EXTENSIONS = [".com", ".net", ".ai", ".io", ".live", ".store", ".tech", ".app", ".ae", ".sa"]

# دالة فحص حقيقية للدومين
def is_domain_available(domain):
    try:
        socket.gethostbyname(domain)
        return False
    except socket.gaierror:
        return True

# دالة توليد الأسماء
def generate_brand(category):
    prefixes = ["Alpha", "Global", "Ultra", "Prime", "Next", "Pro", "Smart", "Ever", "Zen", "Gold", "Royal"]
    base = random.choice(BRAND_DATA.get(category, ["Brand"]))
    suffix = random.choice(BRAND_DATA.get(category, ["Corp"]))
    
    name = random.choice([
        f"{random.choice(prefixes)}{base}",
        f"{base}{suffix}",
        f"{base}{random.randint(10, 99)}"
    ]).lower()
    
    # إذا كان القسم هو الخليج، نزيد احتمالية النطاقات المحلية .ae و .sa
    if category == "الخليج":
        ext = random.choice([".ae", ".sa", ".com", ".net"])
    else:
        ext = random.choice(EXTENSIONS)
    return name + ext

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("🚫 الدخول ممنوع. تواصل مع الأدمن.")
        return

    kb = [
        ["🏢 مصانع", "🍴 مطاعم", "👕 ملابس"],
        ["📦 تعبئة", "🚚 شحن", "🛵 توصيل"],
        ["🏥 مستشفيات", "🤖 AI", "🔨 نجارة"],
        ["🇸🇦 الخليج 🇦🇪"], # الزر الجديد المستهدف للإمارات والسعودية
        ["➕ إضافة مستخدم", "➖ حذف مستخدم"]
    ]
    await update.message.reply_text("🚀 **مرحباً بك في محرك توليد البراندات الذكي**\nاختر القسم لتوليد وفحص 10 دومينات فوراً.", 
                                   reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in ALLOWED_USERS: return

    # إدارة المستخدمين للأدمن
    if user_id == ADMIN_ID:
        if text == "➕ إضافة مستخدم":
            await update.message.reply_text("أرسل ID المستخدم:")
            context.user_data['state'] = 'ADD'
            return
        if text == "➖ حذف مستخدم":
            await update.message.reply_text("أرسل ID المستخدم للحذف:")
            context.user_data['state'] = 'DEL'
            return
        
        state = context.user_data.get('state')
        if state in ['ADD', 'DEL']:
            try:
                target = int(text)
                if state == 'ADD': ALLOWED_USERS.add(target)
                else: ALLOWED_USERS.discard(target)
                await update.message.reply_text(f"✅ تمت العملية لـ {target}")
            except: await update.message.reply_text("❌ خطأ في الـ ID")
            context.user_data['state'] = None
            return

    # معالجة توليد الدومينات
    # استخراج اسم القسم (الخليج أو غيره)
    category = "الخليج" if "الخليج" in text else text.split(" ")[-1]
    
    if category in BRAND_DATA:
        m = await update.message.reply_text(f"🧪 جاري توليد وفحص 10 دومينات لـ {category}...")
        
        results = []
        attempts = 0
        while len(results) < 10 and attempts < 100:
            domain = generate_brand(category)
            if domain not in [r[0] for r in results]:
                status = "✅ متاح" if is_domain_available(domain) else "❌ محجوز"
                results.append((domain, status))
            attempts += 1

        report = f"🎯 **نتائج توليد براندات ({category}):**\n\n"
        for d, s in results:
            report += f"🌐 `{d}` \n  Status: {s}\n\n"
        
        await m.edit_text(report, parse_mode='Markdown')

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    print("AI Brand Generator with Gulf Target Started...")
    app.run_polling()
