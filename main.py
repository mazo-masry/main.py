import os
import random
import string
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات الأساسية ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780  # معرف المدير (أنت)

# قائمة المستخدمين المسموح لهم (تبدأ بك وبـ 100 خانة فارغة اختيارياً)
# في هذه النسخة، سيتم حفظ المضافين في الذاكرة أثناء تشغيل السيرفر
ALLOWED_USERS = {ADMIN_ID}

def generate_random_domain(length):
    return ''.join(random.choices(string.ascii_lowercase, k=length)) + ".com"

def get_domain_info(domain):
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
    except:
        return "خطأ في الفحص ⚠️", ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id == ADMIN_ID:
        keyboard = [
            ['4 حروف', '5 حروف', '3 حروف 💎'],
            ['بحث عن متاح', 'قربت تنتهي ⏰'],
            ['➕ إضافة مستخدم', '➖ حذف مستخدم'],
            ['📋 قائمة المتصلين']
        ]
        msg = "👑 أهلاً بك يا مدير! لوحة التحكم كاملة بين يديك:"
    elif user_id in ALLOWED_USERS:
        keyboard = [['4 حروف', '5 حروف'], ['بحث عن متاح', 'قربت تنتهي ⏰']]
        msg = "🚀 أهلاً بك! جهازك مفعل، اختر من القائمة:"
    else:
        keyboard = []
        msg = f"🚫 الوصول مرفوض.\nتعريفك (ID): `{user_id}`\nأرسله للمدير لتفعيلك."

    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(msg, reply_markup=markup, parse_mode='Markdown')

async def handle_admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id != ADMIN_ID: return False

    if '➕ إضافة' in text:
        await update.message.reply_text("ارسله الآن بصيغة: `اضف 123456789`", parse_mode='Markdown')
        return True
    elif '➖ حذف' in text:
        await update.message.reply_text("ارسله الآن بصيغة: `احذف 123456789`", parse_mode='Markdown')
        return True
    elif 'قائمة' in text:
        users_list = "\n".join([f"👤 `{u}`" for u in ALLOWED_USERS])
        await update.message.reply_text(f"📋 المستخدمين المفعلين حالياً:\n{users_list}", parse_mode='Markdown')
        return True
    
    # تنفيذ أوامر الإضافة والحذف النصية
    if text.startswith("اضف "):
        new_id = int(text.split(" ")[1])
        ALLOWED_USERS.add(new_id)
        await update.message.reply_text(f"✅ تم إضافة `{new_id}` للقائمة البيضاء.", parse_mode='Markdown')
        return True
    elif text.startswith("احذف "):
        del_id = int(text.split(" ")[1])
        if del_id in ALLOWED_USERS and del_id != ADMIN_ID:
            ALLOWED_USERS.remove(del_id)
            await update.message.reply_text(f"🗑️ تم حذف `{del_id}` بنجاح.", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ لا يمكن حذف هذا الرقم.")
        return True
    
    return False

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # أولاً: التحقق من أوامر المدير
    if await handle_admin_actions(update, context): return

    # ثانياً: التحقق من صلاحية المستخدم العادي
    if user_id not in ALLOWED_USERS: return

    msg = await update.message.reply_text("⏳ جاري المعالجة...")
    
    if '3' in text or '4' in text or '5' in text:
        length = 3 if '3' in text else (4 if '4' in text else 5)
        res = []
        for _ in range(5):
            d = generate_random_domain(length)
            buy_link = f"https://www.namecheap.com/domains/registration/results/?domain={d}"
            res.append(f"🌐 `{d}`\n🔗 [شراء]( {buy_link} )")
        await msg.edit_text(f"🔎 مقترحات {length} حروف:\n\n" + "\n".join(res), parse_mode='Markdown', disable_web_page_preview=True)

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
