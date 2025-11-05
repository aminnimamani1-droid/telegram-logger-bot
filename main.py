from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta
import os
import json
from flask import Flask
from threading import Thread

# TOKEN را از Secret محیطی می‌خوانیم
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

LOG_FILE = "logs.json"

# تابع برای گرفتن زمان ایران (UTC+3:30)
def get_iran_time():
    return datetime.utcnow() + timedelta(hours=3, minutes=30)

# تابع برای گرفتن تاریخ امروز به وقت ایران
def get_iran_date():
    return get_iran_time().strftime("%Y-%m-%d")

# بارگذاری اولیه لاگ‌ها از فایل (اگر وجود داشته باشد)
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

# تبدیل ساختار قدیمی (list) به ساختار جدید (dict با تاریخ)
def migrate_old_data():
    global user_logs
    migrated = False
    for user_id in list(user_logs.keys()):
        # اگر داده قدیمی (list) باشد، تبدیل کن
        if isinstance(user_logs[user_id], list):
            old_messages = user_logs[user_id]
            user_logs[user_id] = {}
            # همه پیام‌های قدیمی رو به تاریخ امروز منتقل کن
            today = get_iran_date()
            user_logs[user_id][today] = old_messages
            migrated = True
    if migrated:
        save_logs(user_logs)
        print("داده‌های قدیمی به فرمت جدید تبدیل شدند.")

# اجرای migration
migrate_old_data()

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(  # type: ignore
        "سلام! پیام هاتو بفرست تا با زمان (وقت ایران) ثبت کنم.\n"
        "برای دیدن پیام‌های امروز /show رو بزن.\n"
        "هر روز بعد از 12 شب، لیست جدیدی شروع میشه!"
    )

# ذخیره پیام‌ها با زمان و تاریخ ایران
async def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user  # type: ignore
    user_id = str(user.id)  # type: ignore
    text = update.message.text  # type: ignore
    
    iran_time = get_iran_time()
    date_str = iran_time.strftime("%Y-%m-%d")  # تاریخ ایران
    time_str = iran_time.strftime("%H:%M:%S")  # ساعت ایران
    
    # ساختار: {user_id: {date: [messages]}}
    if user_id not in user_logs:
        user_logs[user_id] = {}
    
    # اگر داده قدیمی (list) باشد، تبدیل کن و داده‌های قدیمی رو حفظ کن
    if isinstance(user_logs[user_id], list):
        old_messages = user_logs[user_id]
        user_logs[user_id] = {date_str: old_messages}
    
    if date_str not in user_logs[user_id]:
        user_logs[user_id][date_str] = []
    
    entry = f"ساعت {time_str} : {text}"
    user_logs[user_id][date_str].append(entry)
    save_logs(user_logs)
    
    # نمایش پیام با تاریخ شمسی (میلادی)
    await update.message.reply_text(f"📅 {date_str}\n{entry}")  # type: ignore

# نمایش پیام‌های امروز فقط
async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user  # type: ignore
    user_id = str(user.id)  # type: ignore
    today = get_iran_date()  # تاریخ امروز به وقت ایران
    
    # اگر کاربر داده دارد، چک کن که داده قدیمی (list) نباشد
    if user_id in user_logs:
        if isinstance(user_logs[user_id], list):
            old_messages = user_logs[user_id]
            user_logs[user_id] = {today: old_messages}
            save_logs(user_logs)
    
    if user_id in user_logs and today in user_logs[user_id] and user_logs[user_id][today]:
        messages = user_logs[user_id][today]
        header = f"📅 پیام‌های امروز ({today}):\n" + "="*30 + "\n\n"
        message = header + "\n".join(messages)
        
        # اگر پیام خیلی طولانی بود، در چند پیام بفرست
        MAX_CHARS = 4000
        for i in range(0, len(message), MAX_CHARS):
            await update.message.reply_text(message[i:i+MAX_CHARS])  # type: ignore
    else:
        await update.message.reply_text(f"هیچ پیامی برای امروز ({today}) ثبت نشده است.")  # type: ignore

# =================== Keep Alive با Flask ===================
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# =================== اجرای Bot ===================
if __name__ == "__main__":
    if not TOKEN:
        print("خطا: توکن تلگرام یافت نشد. لطفا Secret با کلید TELEGRAM_BOT_TOKEN را تنظیم کنید.")
        exit(1)

    keep_alive()  # سرور نگه‌دارنده را روشن کن

    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("show", show_logs))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_message))

    print("Bot running...")
    bot_app.run_polling()
