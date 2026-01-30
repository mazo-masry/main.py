import os
import time
import random
import requests
from telegram.ext import Updater, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")

# كلمات مفهومة 5-6 حروف
WORDS = [
    "brand","smart","cloud","quick","media","prime","trust","pixel",
    "fresh","logic","spark","boost","trend","scope","alpha","nexus",
    "vivid","urban","solid","clean","sharp","magic","happy","super"
]

TLDS = ["com"]
CHECK_LIMIT = 50        # عدد الدومينات في كل تشغيل
DELAY = 0.7             # سرعة الفحص (آمن)

def is_domain_available(domain):
    url = f"https://api.domainsdb.info/v1/domains/search?domain={domain}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        return data.get("total", 0) == 0
    except:
        return False

def start(update, context):
    chat_id = update.message.chat_id
    bot = context.bot

    bot.send_message(chat_id, "🚀 بدء توليد وفحص الدومينات...\n")

    used = set()
    count = 0
    available = []

    random.shuffle(WORDS)

    for word in WORDS:
        if count >= CHECK_LIMIT:
            break

        if not (5 <= len(word) <= 6):
            continue

        domain = f"{word}.com"
        if domain in used:
            continue

        used.add(domain)
        count += 1

        bot.send_message(chat_id, f"🔍 فحص: {domain}")
        time.sleep(0.3)

        free = is_domain_available(domain)

        if free:
            bot.send_message(chat_id, f"✅ AVAILABLE: {domain}")
            available.append(domain)
        else:
            bot.send_message(chat_id, f"❌ TAKEN: {domain}")

        time.sleep(DELAY)

    if available:
        bot.send_message(
            chat_id,
            "🎯 الدومينات المتاحة:\n\n" + "\n".join(available)
        )
    else:
        bot.send_message(chat_id, "😕 مفيش ولا دومين متاح المرة دي")

def main():
    print("BOT STARTING...")
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
