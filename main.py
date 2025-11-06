from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta
import os
import json
import nest_asyncio
import asyncio

# رفع مشکل event loop در Render / Python 3.13
nest_asyncio.apply()

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

LOG_FILE = "logs.json"

# زمان ایران
def get_iran_time():
    return datetime.utcnow() + timedelta(hours=3, minutes=30)

def get_iran_date():
    return get_iran_time().strftime("%Y-%m-%d")

# مدیریت فایل لاگ‌ها
def load_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_logs(data):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

user_logs = load_logs()

# مایگریشن داده‌های قدیمی
for user_id in list(user_logs.keys()):
    if isinstance(user_logs[user_id], list):
        user_logs[user_id] = {get_iran_date(): user_logs[user_id]}
save_logs(user_logs)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! پیام‌هاتو بفرست تا ثبت کنم.\nبرای دیدن پیام‌های امروز /show رو بزن."
    )

# ثبت پیام
async def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text(f"📅 {date_str}\nساعت {time_str} : {text}")

# /show
async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    today = get_iran_date()
    if user_id in user_logs and today in user_logs[user_id]:
        messages = user_logs[user_id][today]
        msg = "📅 پیام‌های امروز:\n" + "\n".join(messages)
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("هیچ پیامی برای امروز ثبت نشده است.")

# اجرای اصلی
async def main():
    if not TOKEN:
        print("❌ توکن پیدا نشد.")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("show", show_logs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_message))

    print("✅ Bot is running ...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
