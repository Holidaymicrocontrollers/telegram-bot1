from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CallbackQueryHandler, CallbackContext, CommandHandler
import schedule
import time
import threading
import datetime
import csv
import os
import matplotlib.pyplot as plt
from keep_alive import keep_alive

BOT_TOKEN = '7819786503:AAF5CiALnyVswMxHn51DB2eIJ8taMyLQKPY'
USER_CHAT_ID = 472659403  # твой chat_id

bot = Bot(token=BOT_TOKEN)
log = {}

# ========== ЛОГИ ==========
def log_action(name: str, status: str):
    now = datetime.datetime.now()
    filename = "activity_log.csv"
    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Дата", "Время", "Действие", "Статус"])
        writer.writerow([now.date(), now.time().strftime("%H:%M:%S"), name, status])

# ========== НАПОМИНАНИЯ ==========
def send_morning_message():
    keyboard = [
        [InlineKeyboardButton("✅ Выпил!", callback_data='morning_done')],
        [InlineKeyboardButton("⏭ Пропустить", callback_data='morning_skip')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=USER_CHAT_ID, text="🌅 Выпей стакан воды на тощак!", reply_markup=reply_markup)
    log['morning'] = None
    threading.Timer(600, check_morning_response).start()

def send_evening_message():
    keyboard = [
        [InlineKeyboardButton("✅ Почистил!", callback_data='evening_done')],
        [InlineKeyboardButton("⏭ Пропустить", callback_data='evening_skip')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=USER_CHAT_ID, text="🌙 Почисть зубы перед сном!", reply_markup=reply_markup)
    log['evening'] = None
    threading.Timer(600, check_evening_response).start()

def send_lunch_message():
    keyboard = [
        [InlineKeyboardButton("✅ Пообедал!", callback_data='lunch_done')],
        [InlineKeyboardButton("⏭ Пропустить", callback_data='lunch_skip')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=USER_CHAT_ID, text="🍽 Время обеда!", reply_markup=reply_markup)

def send_sleep_message():
    keyboard = [
        [InlineKeyboardButton("✅ Лёг спать", callback_data='sleep_done')],
        [InlineKeyboardButton("⏭ Пропустить", callback_data='sleep_skip')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=USER_CHAT_ID, text="🛏 Пора ложиться спать!", reply_markup=reply_markup)

def send_end_shift_message():
    keyboard = [
        [InlineKeyboardButton("✅ Закончил смену", callback_data='shift_done')],
        [InlineKeyboardButton("⏭ Пропустить", callback_data='shift_skip')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=USER_CHAT_ID, text="🏁 Смена закончена! Подведи итоги.", reply_markup=reply_markup)

# ========== ПРОВЕРКА НЕОТВЕЧЕННЫХ ==========
def check_morning_response():
    if log.get('morning') is None:
        bot.send_message(chat_id=USER_CHAT_ID, text="⏰ Ты не нажал «✅ Выпил!» — не забудь выпить воду!")

def check_evening_response():
    if log.get('evening') is None:
        bot.send_message(chat_id=USER_CHAT_ID, text="🪥 Напоминание: ты не нажал «✅ Почистил!»")

# ========== ОБРАБОТКА КНОПОК ==========
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    now = datetime.datetime.now().strftime("%H:%M:%S")
    data = query.data

    actions = {
        'morning_done': ("Утреннее напоминание", "выполнил"),
        'morning_skip': ("Утреннее напоминание", "пропустил"),
        'evening_done': ("Вечернее напоминание", "выполнил"),
        'evening_skip': ("Вечернее напоминание", "пропустил"),
        'lunch_done': ("Обед", "выполнил"),
        'lunch_skip': ("Обед", "пропустил"),
        'sleep_done': ("Сон", "выполнил"),
        'sleep_skip': ("Сон", "пропустил"),
        'shift_done': ("Конец смены", "выполнил"),
        'shift_skip': ("Конец смены", "пропустил"),
    }

    if data in actions:
        name, status = actions[data]
        log_action(name, status)
        query.edit_message_reply_markup(reply_markup=None)
        bot.send_message(chat_id=USER_CHAT_ID, text=f"📌 {name}: {status}")

# ========== СТАТИСТИКА ==========
def generate_statistics():
    filename = "activity_log.csv"
    if not os.path.exists(filename):
        return None
    import pandas as pd
    df = pd.read_csv(filename)
    if df.empty:
        return None
    summary = df.groupby(["Действие", "Статус"]).size().unstack(fill_value=0)
    plt.figure(figsize=(10, 6))
    summary.plot(kind="bar", stacked=True, colormap="Set2")
    plt.title("Статистика активности")
    plt.xlabel("Действие")
    plt.ylabel("Количество")
    plt.xticks(rotation=30)
    plt.tight_layout()
    path = "statistics.png"
    plt.savefig(path)
    return path

# ========== КОМАНДЫ ==========
def test_command(update: Update, context: CallbackContext):
    send_morning_message()
    send_evening_message()
    send_lunch_message()
    send_sleep_message()
    send_end_shift_message()

def log_command(update: Update, context: CallbackContext):
    if os.path.isfile("activity_log.csv"):
        with open("activity_log.csv", "rb") as f:
            bot.send_document(chat_id=update.effective_chat.id, document=f)
    else:
        bot.send_message(chat_id=update.effective_chat.id, text="Лог пуст.")

def stats_command(update: Update, context: CallbackContext):
    path = generate_statistics()
    if path:
        with open(path, "rb") as img:
            bot.send_photo(chat_id=update.effective_chat.id, photo=img)
    else:
        bot.send_message(chat_id=update.effective_chat.id, text="Недостаточно данных для статистики.")

# ========== РАСПИСАНИЕ ==========
schedule.every().day.at("07:15").do(send_morning_message)
schedule.every().day.at("21:30").do(send_evening_message)
schedule.every().day.at("22:00").do(send_sleep_message)
schedule.every().day.at("17:00").do(send_end_shift_message)
for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
    getattr(schedule.every(), day).at("11:15").do(send_lunch_message)

# ========== ЗАПУСК ==========
keep_alive()

# ========== РАСПИСАНИЕ ВРЕМЕНИ (UTC, т.к. Replit) ==========
schedule.every().day.at("01:15").do(send_morning_message)      # 07:15 по Алматы
schedule.every().monday.at("05:15").do(send_lunch_reminder)     # 11:15 по Алматы
schedule.every().tuesday.at("05:15").do(send_lunch_reminder)
schedule.every().wednesday.at("05:15").do(send_lunch_reminder)
schedule.every().thursday.at("05:15").do(send_lunch_reminder)
schedule.every().friday.at("05:15").do(send_lunch_reminder)
schedule.every().day.at("11:00").do(send_end_of_shift_reminder) # 17:00 по Алматы
schedule.every().day.at("15:30").do(send_evening_message)       # 21:30 по Алматы
schedule.every().day.at("16:00").do(send_sleep_reminder)        # 22:00 по Алматы

# Проверка ответов (отложенная через 10 мин)
schedule.every().day.at("01:25").do(check_morning_response)     # Проверка воды
schedule.every().day.at("15:40").do(check_evening_response)     # Проверка чистки

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(10)

threading.Thread(target=run_scheduler).start()

updater = Updater(token=BOT_TOKEN, use_context=True)
updater.dispatcher.add_handler(CallbackQueryHandler(button_handler))
updater.dispatcher.add_handler(CommandHandler(["test"], test_command))
updater.dispatcher.add_handler(CommandHandler(["log"], log_command))
updater.dispatcher.add_handler(CommandHandler(["stats"], stats_command))
updater.start_polling()
