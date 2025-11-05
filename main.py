from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta
import os
import json
import asyncio

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

LOG_FILE = "logs.json"

def get_iran_time():
    return datetime.utcnow() + timedelta(hours=3, minutes=30)

def get_iran_date():
    return get_iran_time().strftime("%Y-%m-%d")

def load_logs():
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_logs(data):
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

user_logs = load_logs()

def migrate_old_data():
    global user_logs
    migrated = False
    for user_id in list(user_logs.keys()):
        if isinstance(user_logs[user_id], list):
            old_messages = user_logs[user_id]
            user_logs[user_id] = {}
            today = get_iran_date()
            user_logs[user_id][today] = old_messages
            migrated = True
    if migrated:
        save_logs(user_logs)
        print("داده‌های قدیمی به فرمت جدید تبدیل شدند.")

migrate_old_data()

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! پیام هاتو بفرست تا ثبت کنم.\n"
        "برای دیدن پیام‌های امروز /show رو بزن."
    )

async def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    iran_time = get_iran_time()
    date_str = iran_time.strftime("%Y-%m-%d")
    time_str = iran_time.strftime("%H:%M:%S")

    if user_id not in user_logs:
        user_logs[user_id] = {}
    if isinstance(user_logs[user_id], list):
        old_messages = user_logs[user_id]
        user_logs[user_id] = {date_str: old_messages}
    if date_str not in user_logs[user_id]:
        user_logs[user_id][date_str] = []

    entry = f"ساعت {time_str} : {text}"
    user_logs[user_id][date_str].append(entry)
    save_logs(user_logs)

    await update.message.reply_text(f"📅 {date_str}\n{entry}")

async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    today = get_iran_date()

    if user_id in user_logs and today in user_logs[user_id] and user_logs[user_id][today]:
        messages = user_logs[user_id][today]
        header = f"📅 پیام‌های امروز ({today}):\n" + "="*30 + "\n\n"
        message = header + "\n".join(messages)
        MAX_CHARS = 4000
        for i in range(0, len(message), MAX_CHARS):
            await update.message.reply_text(message[i:i+MAX_CHARS])
    else:
        await update.message.reply_text(f"هیچ پیامی برای امروز ({today}) ثبت نشده است.")

# Main
async def main():
    if not TOKEN:
        print("❌ خطا: توکن تنظیم نشده.")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("show", show_logs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_message))

    print("✅ Bot running ...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
