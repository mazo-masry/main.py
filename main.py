import os
import random
import string
import requests
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات لمراقبة الأداء
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 665829780 
ALLOWED_USERS = {ADMIN_ID}

def check_domain(domain):
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
            ['🔥 رادار الكلمات الساخنة', '💎 رادار الدومينات القصيرة'],
            ['📜 فحص العمر الذهبي', '🔔 تنبيه الصياد المخصص'],
            ['📋 قائمة المفعلين', '➕ إضافة', '➖ حذف']
        ]
        if user_id != ADMIN_ID:
            keyboard = [['🔥 رادار الكلمات الساخنة', '💎 رادار الدومينات القصيرة'], ['📜 فحص العمر الذهبي', '🔔 تنبيه الصياد المخصص']]
            
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "🚀 **تم تحديث المنصة بالكامل!**\nتم إضافة الأدوات الجديدة وإصلاح نظام الإدارة. اختر أداة لبدء الاستثمار:",
            reply_markup=markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"🚫 غير مصرح لك.\nID: `{user_id}`")

async def handle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in ALLOWED_USERS and user_id != ADMIN_ID: return

    # --- إدارة المستخدمين (إصلاح شامل) ---
    if user_id == ADMIN_ID:
        if text == '➕ إضافة':
            await update.message.reply_text("أرسل المعرف هكذا: `اضف 123456`", parse_mode='Markdown')
            return
        elif text == '➖ حذف':
            await update.message.reply_text("أرسل المعرف هكذا: `احذف 123456`", parse_mode='Markdown')
            return
        elif text.startswith("اضف "):
            try:
                new_id = int(text.split(" ")[1])
                ALLOWED_USERS.add(new_id)
                await update.message.reply_text(f"✅ تم تفعيل العضو: `{new_id}`")
            except: pass
            return
        elif text.startswith("احذف "):
            try:
                del_id = int(text.split(" ")[1])
                if del_id in ALLOWED_USERS and del_id != ADMIN_ID:
                    ALLOWED_USERS.remove(del_id)
                    await update.message.reply_text(f"🗑️ تم حذف العضو: `{del_id}`")
            except: pass
            return
        elif text == '📋 قائمة المفعلين':
            await update.message.reply_text(f"👥 المفعلين: `{list(ALLOWED_USERS)}`", parse_mode='Markdown')
            return

    # --- 🔥 رادار الكلمات الساخنة ---
    if text == '🔥 رادار الكلمات الساخنة':
        msg = await update.message.reply_text("🔎 جاري رصد كلمات التريند (AI, Tech, Crypto)...")
        hot_words = ["neural", "token", "cyber", "meta", "smart", "chain", "cloud"]
        found = []
        for _ in range(10):
            d = random.choice(hot_words) + random.choice(["hub", "lab", "base", "fix"]) + ".com"
            if check_domain(d) == "متاح ✅":
                found.append(f"🔥 `{d}`")
            if len(found) >= 3: break
        await msg.edit_text("🎯 **دومينات تريند متاحة:**\n\n" + ("\n".join(found) if found else "حاول ثانية.."), parse_mode='Markdown')

    # --- 💎 رادار الدومينات القصيرة ---
    elif text == '💎 رادار الدومينات القصيرة':
        msg = await update.message.reply_text("💎 جاري البحث عن خماسي وسداسي سهل النطق...")
        vowels = "aeiou"
        consonants = "bcdfghjklmnpqrstvwxyz"
        found = []
        for _ in range(20):
            # توليد كلمة سهلة النطق (ساكن-متحرك-ساكن-متحرك)
            d = random.choice(consonants) + random.choice(vowels) + random.choice(consonants) + random.choice(vowels) + ".com"
            if check_domain(d) == "متاح ✅":
                found.append(f"💎 `{d}`")
            if len(found) >= 3: break
        await msg.edit_text("🎯 **دومينات قصيرة سهلة النطق:**\n\n" + ("\n".join(found) if found else "جاري البحث.."), parse_mode='Markdown')

    # --- 📜 فحص العمر الذهبي ---
    elif text == '📜 فحص العمر الذهبي':
        await update.message.reply_text("📜 أرسل اسم الدومين لفحص تاريخ تسجيله الأول (العمر):")

    # --- 🔔 تنبيه الصياد المخصص ---
