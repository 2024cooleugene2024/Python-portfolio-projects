import os
import requests
import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from bs4 import BeautifulSoup
import schedule
import time
from threading import Thread
import logging
import traceback
from datetime import datetime, timedelta

# Бот токен и ID канала и админа
TOKEN = '7699074411:AAHlsR_ZOlW9rPMwAzZIpTPIk4x_1vzsK3w'
CHAT_ID = 'Community_Python'
ADMIN_CHAT_ID = '@cooleugene2012'

# Настраиваем логирование
LOG_FILE = 'bot_log.txt'
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Настройки количества публикаций и времени
publications_settings = {
    'videos_per_day': 3,
    'articles_per_day': 3,
    'books_per_day': 1
}

schedule_settings = {
    'time': '09:00',  # Время публикации по умолчанию
    'paused': False,  # Флаг приостановки публикаций
    'days': ['Monday', 'Wednesday', 'Friday'],  # Дни публикаций по умолчанию
    'delete_after_days': 7,  # Количество дней, через которые публикации будут удаляться
    'repeat_interval_hours': 24  # Интервал повторных публикаций в часах
}

last_publication_date = None  # Дата последней успешной публикации
published_materials = {}  # Хранение опубликованных материалов для последующего удаления

# Создаем экземпляр бота
bot = telegram.Bot(token=TOKEN)

# Хранение материалов для ручной проверки
pending_materials = {}

# Функция для проверки лицензий
def check_license(material_type, license_info):
    if material_type == 'video':
        return license_info == 'creativeCommon'
    elif material_type in ['article', 'book']:
        return 'creativecommons' in license_info.lower() or 'mit' in license_info.lower() or 'apache' in license_info.lower()
    return False

# Основная функция для скрапинга сайтов с обработкой ошибок и проверкой лицензий
def scrape_python_materials():
    materials = {'videos': [], 'articles': [], 'books': []}
    youtube_api_key = 'AIzaSyAe3h7vlN7I4SiAQVPnqXUk_52HTmH0lSI'  # Замените на ваш API ключ
    youtube_search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults={publications_settings['videos_per_day']}&q=python&key={youtube_api_key}"

    try:
        response = requests.get(youtube_search_url)
        response.raise_for_status()
        videos = response.json().get('items', [])
        for video in videos:
            video_data = {
                'title': video['snippet']['title'],
                'url': f"https://www.youtube.com/watch?v={video['id']['videoId']}",
                'license': video['snippet'].get('license', 'unknown')
            }
            if check_license('video', video_data['license']):
                materials['videos'].append(video_data)
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе видео: {e}\n{traceback.format_exc()}")

    medium_url = "https://medium.com/tag/python"
    try:
        response = requests.get(medium_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('h3')
        for article in articles[:publications_settings['articles_per_day']]:
            article_data = {
                'title': article.text,
                'url': article.find_parent('a')['href'],
                'license': 'Creative Commons'
            }
            if check_license('article', article_data['license']):
                materials['articles'].append(article_data)
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе статей с Medium: {e}\n{traceback.format_exc()}")

    book_url = "https://codelibrary.info/books/python"  # Замените на реальный URL
    try:
        response = requests.get(book_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        books = soup.find_all('div', class_='book')
        for book in books[:publications_settings['books_per_day']]:
            book_data = {
                'title': book.find('h2').text,
                'url': book.find('a')['href'],
                'license': 'Creative Commons'
            }
            if check_license('book', book_data['license']):
                materials['books'].append(book_data)
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе книг: {e}\n{traceback.format_exc()}")

    return materials

# Функция для отправки материалов админу на проверку
def send_materials_for_approval(materials):
    global pending_materials
    message = "Найдены материалы по Python, ожидающие вашей проверки:\n\n"
    pending_materials = materials

    message += "Видео:\n"
    for i, video in enumerate(materials['videos'], 1):
        message += f"{i}. {video['title']}: {video['url']} (Лицензия: {video['license']})\n"

    message += "\nСтатьи:\n"
    for i, article in enumerate(materials['articles'], 1):
        message += f"{i}. {article['title']}: {article['url']} (Лицензия: {article['license']})\n"

    message += "\nКниги:\n"
    for i, book in enumerate(materials['books'], 1):
        message += f"{i}. {book['title']}: {book['url']} (Лицензия: {book['license']})\n"

    try:
        bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)
        bot.send_message(chat_id=ADMIN_CHAT_ID, text="Используйте /approve для публикации или /reject для отклонения.")
        logging.info("Материалы отправлены админу на проверку.")
    except telegram.error.TelegramError as e:
        logging.error(f"Ошибка отправки сообщения админу: {e}\n{traceback.format_exc()}")

# Функция для публикации материалов
def post_to_telegram():
    global pending_materials, last_publication_date, published_materials
    materials = pending_materials
    message = "Новые материалы по Python:\n\n"

    message += "Видео:\n"
    for video in materials['videos']:
        message += f"{video['title']}: {video['url']} (Лицензия: {video['license']})\n"

    message += "\nСтатьи:\n"
    for article in materials['articles']:
        message += f"{article['title']}: {article['url']} (Лицензия: {article['license']})\n"

    message += "\nКниги:\n"
    for book in materials['books']:
        message += f"{book['title']}: {book['url']} (Лицензия: {book['license']})\n"

    try:
        bot.send_message(chat_id=CHAT_ID, text=message)
        logging.info("Материалы опубликованы в Telegram.")
        last_publication_date = datetime.now()  # Обновляем дату последней публикации
        published_materials[last_publication_date] = materials  # Сохраняем опубликованные материалы с датой публикации
    except telegram.error.TelegramError as e:
        logging.error(f"Ошибка отправки сообщения в Telegram: {e}\n{traceback.format_exc()}")

# Команда для одобрения публикации
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Материалы одобрены и будут опубликованы.")
    logging.info("Материалы одобрены администратором.")
    post_to_telegram()

# Команда для отклонения публикации
async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global pending_materials
    pending_materials = {}
    await update.message.reply_text("Материалы отклонены и не будут опубликованы.")
    logging.info("Материалы отклонены администратором.")

# Команда для получения лог-файла
async def get_log_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(LOG_FILE, 'rb') as log_file:
            await bot.send_document(chat_id=ADMIN_CHAT_ID, document=log_file)
        logging.info("Лог-файл отправлен админу.")
    except Exception as e:
        logging.error(f"Ошибка при отправке лог-файла: {e}\n{traceback.format_exc()}")

# Команда для изменения количества публикаций
async def set_publications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global publications_settings
    try:
        args = context.args
        publications_settings['videos_per_day'] = int(args[0])
        publications_settings['articles_per_day'] = int(args[1])
        publications_settings['books_per_day'] = int(args[2])
        await update.message.reply_text(
            f"Настройки публикаций обновлены:\nВидео: {publications_settings['videos_per_day']}, Статьи: {publications_settings['articles_per_day']}, Книги: {publications_settings['books_per_day']}")
        logging.info(f"Обновлены настройки публикаций: {publications_settings}")
    except (IndexError, ValueError):
        await update.message.reply_text("Пожалуйста, укажите три числа для видео, статей и книг.")

# Команда для установки времени публикаций
async def set_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global schedule_settings
    try:
        schedule_settings['time'] = context.args[0]
        await update.message.reply_text(f"Время публикации обновлено на {schedule_settings['time']}.")
        logging.info(f"Время публикации обновлено на {schedule_settings['time']}.")
    except IndexError:
        await update.message.reply_text("Пожалуйста, укажите время в формате HH:MM.")

# Функция для отчета о публикациях и удалениях
async def report_publications_and_deletions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_time = datetime.now()
    message = "Отчёт о публикациях и удалённых материалах:\n\n"

    if published_materials:
        message += "Опубликованные материалы:\n"
        for pub_date, materials in published_materials.items():
            message += f"\nПубликации от {pub_date.strftime('%Y-%m-%d %H:%M:%S')}:\n"
            message += "Видео:\n"
            for video in materials['videos']:
                message += f"{video['title']}: {video['url']} (Лицензия: {video['license']})\n"
            message += "Статьи:\n"
            for article in materials['articles']:
                message += f"{article['title']}: {article['url']} (Лицензия: {article['license']})\n"
            message += "Книги:\n"
            for book in materials['books']:
                message += f"{book['title']}: {book['url']} (Лицензия: {book['license']})\n"
    else:
        message += "Опубликованных материалов нет.\n"

    message += "\nУдалённые материалы:\n"
    for pub_date in list(published_materials.keys()):
        if current_time - pub_date > timedelta(days=schedule_settings['delete_after_days']):
            materials = published_materials[pub_date]
            message += f"\nМатериалы от {pub_date.strftime('%Y-%m-%d %H:%M:%S')}:\n"
            # Здесь добавьте логику для добавления информации об удалённых видео, статьях и книгах

    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)
        logging.info("Отчёт о публикациях и удалениях отправлен админу.")
    except telegram.error.TelegramError as e:
        logging.error(f"Ошибка при отправке отчёта админу: {e}\n{traceback.format_exc()}")

# Функция для выполнения задач по расписанию
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Основная функция запуска бота и расписания
async def main():
    # Настраиваем расписание для выполнения функции скрапинга
    schedule.every().day.at(schedule_settings['time']).do(lambda: send_materials_for_approval(scrape_python_materials()))
    Thread(target=run_schedule).start()  # Запуск расписания в отдельном потоке

    app = ApplicationBuilder().token(TOKEN).build()

    # Обработчики команд
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("reject", reject))
    app.add_handler(CommandHandler("get_log", get_log_file))
    app.add_handler(CommandHandler("set_publications", set_publications))
    app.add_handler(CommandHandler("set_schedule", set_schedule))
    app.add_handler(CommandHandler("report", report_publications_and_deletions))

    await app.run_polling()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())