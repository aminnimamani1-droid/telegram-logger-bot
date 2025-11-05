from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from datetime import datetime, timedelta
import os
import json

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

LOG_FILE = "logs.json"

def get_iran_time():
    return datetime.utcnow() + timedelta(hours=3, minutes=30)

def get_iran_date():
    return get_iran_time().strftime("%Y-%m-%d")

def load_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_logs(data):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

user_logs = load_logs()

# Migration داده‌های قدیمی
for user_id in list(user_logs.keys()):
    if isinstance(user_logs[user_id], list):
        user_logs[user_id] = {get_iran_date(): user_logs[user_id]}
save_logs(user_logs)

def start(update, context):
    update.message.reply_text(
        "سلام! پیام هاتو بفرست تا ثبت کنم.\nبرای دیدن پیام‌های امروز /show رو بزن."
    )

def log_message(update, context):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    date_str = get_iran_date()
    time_str = get_iran_time().strftime("%H:%M:%S")

    if user_id not in user_logs:
        user_logs[user_id] = {}
    if date_str not in user_logs[user_id]:
        user_logs[user_id][date_str] = []

    user_logs[user_id][date_str].append(f"ساعت {time_str} : {text}")
    save_logs(user_logs)
    update.message.reply_text(f"📅 {date_str}\nساعت {time_str} : {text}")

def show_logs(update, context):
    user_id = str(update.message.from_user.id)
    today = get_iran_date()
    if user_id in user_logs and today in user_logs[user_id]:
        messages = user_logs[user_id][today]
        msg = "📅 پیام‌های امروز:\n" + "\n".join(messages)
        update.message.reply_text(msg)
    else:
        update.message.reply_text(f"هیچ پیامی برای امروز ثبت نشده است.")

if not TOKEN:
    print("❌ توکن پیدا نشد.")
    exit(1)

updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("show", show_logs))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, log_message))

print("✅ Bot running ...")
updater.start_polling()
updater.idle()
