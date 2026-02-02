import os
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات الأساسية ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780  # معرفك الخاص كمدير

# قائمة المستخدمين المسموح لهم (القائمة البيضاء)
ALLOWED_USERS = {ADMIN_ID}

def get_domain_info(domain):
    """فحص حالة الدومين وتاريخ الانتهاء"""
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
        return "خطأ في الفحص ⚠️", ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in ALLOWED_USERS or user_id == ADMIN_ID:
        keyboard = [
            ['4 حروف', '5 حروف', '3 حروف 💎'],
            ['بحث عن متاح', 'قربت تنتهي ⏰'],
            ['AI اقتراحات 🧠'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم', '📋 قائمة المتصلين']
        ]
        # لوحة التحكم للمستخدم العادي تختلف عن المدير
        if user_id != ADMIN_ID:
            keyboard = [['4 حروف', '5 حروف'], ['بحث عن متاح', 'AI اقتراحات 🧠']]
            
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("🤖 تم إصلاح السكربت! البوت جاهز للعمل الآن:", reply_markup=markup)
    else:
        await update.message.reply_text(f"🚫 الوصول مرفوض.\nتعريفك (ID): `{user_id}`")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # --- إدارة المستخدمين (للمدير فقط) ---
    if user_id == ADMIN_ID:
        if '➕ إضافة' in text:
            await update.message.reply_text("أرسل الأيدي بصيغة: `اضف 123456789`", parse_mode='Markdown')
            return
        elif '➖ حذف' in text:
            await update.message.reply_text("أرسل الأيدي بصيغة: `احذف 123456789`", parse_mode='Markdown')
            return
        elif 'قائمة' in text:
            await update.message.reply_text(f"📋 المفعلين: `{list(ALLOWED_USERS)}`", parse_mode='Markdown')
            return
        elif text.startswith("اضف "):
            try:
                new_id = int(text.split(" ")[1])
                ALLOWED_USERS.add(new_id)
                await update.message.reply_text(f"✅ تم تفعيل `{new_id}`")
            except Exception: await update.message.reply_text("❌ خطأ في الصيغة")
            return
        elif text.startswith("احذف "):
            try:
                del_id = int(text.split(" ")[1])
                if del_id in ALLOWED_USERS and del_id != ADMIN_ID:
                    ALLOWED_USERS.remove(del_id)
                    await update.message.reply_text(f"🗑️ تم حذف `{del_id}`")
            except Exception: await update.message.reply_text("❌ خطأ")
            return

    # --- صلاحيات المستخدمين ---
    if user_id not in ALLOWED_USERS: return

    # --- منطق البحث والذكاء الاصطناعي ---
    if any(x in text for x in ['3', '4', '5']):
        msg = await update.message.reply_text("⏳ جاري توليد المقترحات...")
        length = 3 if '3' in text else (4 if '4' in text else 5)
        res = [''.join(random.choices(string.ascii_lowercase, k=length)) + ".com" for _ in range(5)]
        await msg.edit_text("🔎 مقترحات عشوائية:\n" + "\n".join([f"🌐 `{d}`" for d in res]), parse_mode='Markdown')

    elif 'AI اقتراحات' in text:
        msg = await update.message.reply_text("🧠 جاري التفكير بنمط AI...")
        prefixes = ["meta", "zen", "cloud", "fast", "smart", "sky", "bit", "pro", "vision", "prime"]
        suffixes = ["ly", "ify", "hub", "zone", "net", "web", "lab", "tech", "sol", "gen"]
        ai_res = []
        for _ in range(5):
            name = random.choice(prefixes) + random.choice(suffixes) + ".com"
            status, _ = get_domain_info(name)
            ai_res.append(f"✨ `{name}` -> {status}")
        await msg.edit_text("🤖 مقترحات البراندات (AI):\n\n" + "\n".join(ai_res), parse_mode='Markdown')

    elif 'متاح' in text or 'تنتهي' in text:
        msg = await update.message.reply_text("🔍 فحص سريع...")
        d = ''.join(random.choices(string.ascii_lowercase, k=5)) + ".com"
        status, expiry = get_domain_info(d)
        await msg.edit_text(f"📊 النتائج لـ `{d}`:\nالحالة: {status}\nانتهاء: {expiry}", parse_mode='Markdown')

if __name__ == "__main__":
    if TOKEN:
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
