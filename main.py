import os
import json
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import threading

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
LOG_FILE = "logs.json"

# ==================== TIME ====================
def get_iran_time():
    return datetime.utcnow() + timedelta(hours=3, minutes=30)

def get_iran_date():
    return get_iran_time().strftime("%Y-%m-%d")

# ==================== LOG FILE ====================
def load_logs():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_logs(data):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

user_logs = load_logs()

# ==================== TELEGRAM BOT ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 **سلام!**\n\n"
        "من پیام‌هات را با تاریخ و ساعت ذخیره می‌کنم.\n\n"
        "📌 فرمان‌ها:\n"
        "• /show پیام‌های امروز\n"
        "• /today خلاصه امروز\n"
        "• /showall همه روزها\n"
        "• فقط پیام بده تا ذخیره کنم\n"
    )
    await update.message.reply_markdown(msg)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_markdown("📘 راهنما: پیام بده تا ذخیره کنم. فرمان‌ها را هم بلدم.")

async def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text
    date_str = get_iran_date()
    time_str = get_iran_time().strftime("%H:%M:%S")

    if user_id not in user_logs:
        user_logs[user_id] = {}
    if date_str not in user_logs[user_id]:
        user_logs[user_id][date_str] = []

    entry = f"ساعت {time_str} : {text}"
    user_logs[user_id][date_str].append(entry)
    save_logs(user_logs)

    await update.message.reply_markdown(f"📝 **ثبت شد:**\n`{entry}`")

async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    today = get_iran_date()

    if user_id not in user_logs or today not in user_logs[user_id]:
        return await update.message.reply_text("📭 امروز هیچ پیامی نداری.")

    msgs = "\n".join(user_logs[user_id][today])
    await update.message.reply_markdown("📅 **پیام‌های امروز:**\n\n" + msgs)

async def today_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    today = get_iran_date()

    if user_id not in user_logs or today not in user_logs[user_id]:
        return await update.message.reply_text("📭 هیچ پیام امروز ثبت نشده.")

    msgs = user_logs[user_id][today]
    summary = (
        "📊 **خلاصه امروز:**\n\n"
        f"📌 تعداد پیام‌ها: {len(msgs)}\n"
        f"⏰ اولین پیام: {msgs[0].split()[1]}\n"
        f"⏰ آخرین پیام: {msgs[-1].split()[1]}"
    )
    await update.message.reply_markdown(summary)

async def show_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id not in user_logs:
        return await update.message.reply_text("هیچ داده‌ای وجود ندارد.")

    dates = list(user_logs[user_id].keys())
    await update.message.reply_markdown("📅 روزهای ذخیره شده:\n\n" + "\n".join("• " + d for d in dates))

# ==================== START BOT ====================

def start_bot():
    bot = ApplicationBuilder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("help", help_cmd))
    bot.add_handler(CommandHandler("show", show_logs))
    bot.add_handler(CommandHandler("today", today_summary))
    bot.add_handler(CommandHandler("showall", show_all))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_message))

    print("🚀 Bot running...")
    bot.run_polling()

# ==================== FLASK KEEP ALIVE ====================

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "🌙 Bot is alive."

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

# ==================== COMBINED START ====================

if __name__ == "__main__":
    if not TOKEN:
        print("❌ توکن در محیط تنظیم نشده.")
        exit(1)

    threading.Thread(target=start_bot).start()
    run_flask()
