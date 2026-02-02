import os
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات الأساسية ---
# تأكد من إضافة BOT_TOKEN في Variables على Railway
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 

# القائمة البيضاء (يتم تخزينها في الذاكرة)
ALLOWED_USERS = {ADMIN_ID}

def get_domain_info(domain):
    """وظيفة لفحص حالة الدومين وتاريخ انتهائه"""
    try:
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
        res = requests.get(url, timeout=5)
        if res.status_code == 404:
            return "متاح ✅", "N/A"
        data = res.json()
        expiry = "غير معروف"
        for event in data.get("events", []):
            if event.get("eventAction") == "expiration":
                expiry = event.get("eventDate").split("T")[0]
        return "محجوز 🔒", expiry
    except Exception:
        return "خطأ في الاتصال ⚠️", ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id == ADMIN_ID or user_id in ALLOWED_USERS:
        keyboard = [
            ['🎯 قناص الدومينات', '💎 صيد الثلاثي'],
            ['🔍 فحص يدوي', '📅 حالة الانتهاء'],
            ['➕ إضافة مستخدم', '📋 القائمة البيضاء']
        ]
        # لوحة تحكم المستخدم العادي (بدون صلاحيات الإدارة)
        if user_id != ADMIN_ID:
            keyboard = [['🎯 قناص الدومينات', '💎 صيد الثلاثي'], ['🔍 فحص يدوي']]
            
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("🎯 **مرحباً بك في نظام القنص الاحترافي!**\nاختر هدفك من القائمة بالأسفل:", reply_markup=markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(f"🚫 الوصول مرفوض.\nتعريفك الرقمي (ID): `{user_id}`")

async def handle_admin(update: Update, text: str):
    """إدارة عمليات الإضافة والحذف للمدير فقط"""
    if '➕ إضافة' in text:
        await update.message.reply_text("أرسل المعرف بصيغة: `اضف 123456789`", parse_mode='Markdown')
        return True
    elif 'القائمة' in text:
        await update.message.reply_text(f"👥 المستخدمين المفعلين: `{list(ALLOWED_USERS)}`", parse_mode='Markdown')
        return True
    elif text.startswith("اضف "):
        try:
            new_id = int(text.split(" ")[1])
            ALLOWED_USERS.add(new_id)
            await update.message.reply_text(f"✅ تم تفعيل المستخدم `{new_id}` بنجاح.")
        except: await update.message.reply_text("❌ تأكد من كتابة الرقم بشكل صحيح.")
        return True
    return False

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # التحقق من صلاحيات المدير أولاً
    if user_id == ADMIN_ID:
        if await handle_admin(update, text): return

    # التحقق من صلاحية المستخدم العادي
    if user_id not in ALLOWED_USERS: return

    # --- منطق القناص (الخيارات الجديدة) ---
    if 'قناص الدومينات' in text:
        msg = await update.message.reply_text("📡 جاري البحث عن دومينات ساقطة...")
        # تركيبات دومينات براندات
        prefixes = ["pro", "top", "go", "fast", "my", "i"]
        suffixes = ["tech", "web", "app", "hub", "zone"]
        results = []
        for _ in range(5):
            name = random.choice(prefixes) + random.choice(suffixes) + random.choice(['x', 'z', 'q', '']) + ".com"
            status, _ = get_domain_info(name)
            if "متاح" in status:
                results.append(f"🔥 **لقطة:** `{name}`\n🔗 [قنص الآن](https://www.namecheap.com/domains/registration/results/?domain={name})")
        
        await msg.edit_text("🎯 **أهداف متاحة للصيد الآن:**\n\n" + ("\n\n".join(results) if results else "لم أجد صيداً ثميناً حالياً، حاول مرة أخرى."), parse_mode='Markdown', disable_web_page_preview=True)

    elif 'صيد الثلاثي' in text:
        msg = await update.message.reply_text("💎 جاري البحث عن تركيبات ثلاثية نادرة...")
        chars = string.ascii_lowercase + string.digits
        found = []
        for _ in range(8):
            d = ''.join(random.choices(chars, k=3)) + ".com"
            status, _ = get_domain_info(d)
            if "متاح" in status: found.append(f"💎 `{d}`")
        
        await msg.edit_text("🎯 **دومينات ثلاثية متاحة:**\n\n" + ("\n".join(found) if found else "جميع التركيبات محجوزة حالياً."), parse_mode='Markdown')

    elif 'فحص يدوي' in text:
        await update.message.reply_text("أرسل الدومين الذي تريد فحص تاريخه (مثال: google.com):")

    elif '.com' in text:
        status, expiry = get_domain_info(text.lower().strip())
        await update.message.reply_text(f"📊 **تقرير القناص:**\n\n🌐 الدومين: `{text}`\nحالة التوافر: {status}\nتاريخ الانتهاء: `{expiry}`", parse_mode='Markdown')

if __name__ == "__main__":
    if not TOKEN:
        print("❌ خطأ: لم يتم العثور على BOT_TOKEN!")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        print("🎯 Sniper Bot is online and stable...")
        app.run_polling(drop_pending_updates=True)
    elif 'متاح' in text:
        found = []
        for _ in range(10):
            d = generate_random_domain(5)
            status, _ = get_domain_info(d)
            if "متاح" in status: found.append(d)
            if len(found) >= 3: break
        await msg.edit_text("💎 متاح حالياً:\n\n" + "\n".join(found) if found else "حاول ثانية.")

    elif 'تنتهي' in text:
        d = generate_random_domain(4)
        status, expiry = get_domain_info(d)
        await msg.edit_text(f"⏰ فحص عينة:\n🌐 `{d}`\n📅 ينتهي في: `{expiry}`", parse_mode='Markdown')

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    print("🤖 البوت يعمل مع لوحة تحكم المدير...")
    app.run_polling(drop_pending_updates=True)
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        print("🤖 البوت يعمل الآن...")
        app.run_polling(drop_pending_updates=True)
    else:
        print("❌ خطأ: BOT_TOKEN غير موجود")
        await msg.edit_text(f"📊 النتائج لـ `{d}`:\nالحالة: {status}\nانتهاء: {expiry}", parse_mode='Markdown')

if __name__ == "__main__":
    if not TOKEN:
        print("❌ خطأ: BOT_TOKEN مفقود في Railway Variables!")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
        print("🤖 البوت يعمل الآن بدون كراش...")
        app.run_polling(drop_pending_updates=True)
    if '3 حروف 💎' in text or '4 حروف' in text or '5 حروف' in text:
        length = 3 if '3 حروف' in text else (4 if '4 حروف' in text else 5)
        res = []
        chars = string.ascii_lowercase + (string.digits if length == 3 else '') # 3 حروف يمكن أن تحتوي على أرقام
        for _ in range(5):
            d = ''.join(random.choices(chars, k=length)) + ".com"
            status, _ = get_domain_info(d)
            buy_link = f"https://www.namecheap.com/domains/registration/results/?domain={d}"
            res.append(f"🌐 `{d}` -> {status}\n🔗 [شراء]({buy_link})")
        await msg.edit_text(f"🔎 مقترحات {length} حروف:\n\n" + "\n\n".join(res), 
                           parse_mode='Markdown', disable_web_page_preview=True)

    elif 'متاح' in text:
        found = []
        for _ in range(10):
            d = generate_random_domain(5)
            status, _ = get_domain_info(d)
            if "متاح" in status: found.append(d)
            if len(found) >= 3: break
        await msg.edit_text("💎 دومينات متاحة حالياً:\n\n" + "\n".join(found) if found else "حاول ثانية.")

    elif 'تنتهي' in text:
        expiring = []
        for _ in range(3):
            d = generate_random_domain(4)
            status, expiry = get_domain_info(d)
            if "محجوز" in status:
                expiring.append(f"⏰ `{d}`\n📅 ينتهي في: `{expiry}`")
        await msg.edit_text("🔔 دومينات قربت تنتهي:\n\n" + "\n\n".join(expiring) if expiring else "لم أجد عينات حالياً.")

    elif 'AI اقتراحات 🧠' in text:
        # قائمة بالبادئات واللاحقات الشائعة للعلامات التجارية
        prefixes = ["meta", "zen", "cloud", "fast", "smart", "sky", "bit", "neo", "pro", "vision", "prime"]
        suffixes = ["ly", "ify", "hub", "zone", "net", "web", "lab", "tech", "sol", "gen"]
        mid_parts = ["core", "edge", "max", "x", "path", "link", "up"]

        ai_suggestions = []
        for _ in range(7): # نولد 7 اقتراحات
            pattern = random.randint(1, 3) # نختار نمط عشوائي
            if pattern == 1: # prefix + suffix
                name = random.choice(prefixes) + random.choice(suffixes)
            elif pattern == 2: # prefix + mid_part
                name = random.choice(prefixes) + random.choice(mid_parts)
            else: # simple combination
                name = random.choice(prefixes) + ''.join(random.choices(string.ascii_lowercase, k=random.randint(2,3)))

            d = name.lower() + ".com"
            status, _ = get_domain_info(d)
            buy_link = f"https://www.namecheap.com/domains/registration/results/?domain={d}"
            ai_suggestions.append(f"✨ `{d}` -> {status}\n🔗 [اشترِ]( {buy_link} )")
            
        await msg.edit_text("🧠 اقتراحات ذكية (AI-Powered Brandable Domains):\n\n" + "\n\n".join(ai_suggestions), 
                           parse_mode='Markdown', disable_web_page_preview=True)
    
    else:
        await msg.edit_text("يرجى اختيار أمر من القائمة بالأسفل.")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    
    print("🤖 البوت يعمل الآن بنجاح مع لوحة تحكم المدير واقتراحات الـ AI...")
    app.run_polling(drop_pending_updates=True)
    elif 'متاح' in text:
        found = []
        for _ in range(10):
            d = generate_random_domain(5)
            status, _ = get_domain_info(d)
            if "متاح" in status: found.append(d)
            if len(found) >= 3: break
        await msg.edit_text("💎 متاح حالياً:\n\n" + "\n".join(found) if found else "حاول ثانية.")

    elif 'تنتهي' in text:
        d = generate_random_domain(4)
        status, expiry = get_domain_info(d)
        await msg.edit_text(f"⏰ فحص عينة:\n🌐 `{d}`\n📅 ينتهي في: `{expiry}`", parse_mode='Markdown')

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_logic))
    print("🤖 البوت يعمل مع لوحة تحكم المدير...")
    app.run_polling(drop_pending_updates=True)
