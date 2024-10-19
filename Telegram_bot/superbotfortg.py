import os
import requests
import telegram
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext
from bs4 import BeautifulSoup
import schedule
import asyncio
import time
from threading import Thread
import logging
import traceback
from datetime import datetime, timedelta

# Бот токен и ID канала и админа
TOKEN = 'Your token here'
CHAT_ID = 'Your chat id here'
ADMIN_CHAT_ID = 'Your admin chat id'

# Настраиваем логирование
LOG_FILE = 'bot_log.txt'
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Настройки публикаций и времени
publications_settings = {
    'videos_per_day': 3,
    'articles_per_day': 3,
    'books_per_day': 1
}
schedule_settings = {
    'time': '09:00'  # Время публикации по умолчанию
}

# Создаем экземпляр бота
bot = telegram.Bot(token=TOKEN)

# Хранение материалов для ручной проверки
pending_materials = {}


# Функция для проверки лицензий
def check_license(material_type, license_info):
    if material_type == 'video':
        return license_info == 'creativeCommon'
    elif material_type == 'article' or material_type == 'book':
        return 'creativecommons' in license_info.lower() or 'mit' in license_info.lower() or 'apache' in license_info.lower()
    return False


# Основная функция для скрапинга сайтов с обработкой ошибок и проверкой лицензий
def scrape_python_materials():
    materials = {'videos': [], 'articles': [], 'books': []}

    # Пример скрапинга видео с YouTube с использованием YouTube Data API
    youtube_api_key = 'AIzaSyAe3h7vlN7I4SiAQVPnqXUk_52HTmH0lSI'
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

    # Пример скрапинга статей с Medium
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

    # Пример скрапинга репозиториев с GitHub
    github_url = "https://github.com/search?q=python&type=repositories"
    try:
        response = requests.get(github_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        repos = soup.find_all('h3', class_='f4 text-normal')

        for repo in repos[:publications_settings['articles_per_day']]:
            repo_data = {
                'title': repo.text.strip(),
                'url': f"https://github.com{repo.find('a')['href']}",
                'license': 'MIT'
            }
            if check_license('article', repo_data['license']):
                materials['articles'].append(repo_data)
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе репозиториев с GitHub: {e}\n{traceback.format_exc()}")

    # Пример скрапинга книг (условный сайт)
    book_url = "https://codelibrary.info/books/python"
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


# Асинхронная команда для старта бота и отправки меню с кнопками
async def start(update: Update, context: CallbackContext):
    keyboard = [
        ["Получить настройки публикаций", "Изменить количество публикаций"],
        ["Изменить время публикации", "Изменить дни публикаций"],
        ["Лог", "Поиск материалов"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите команду:", reply_markup=reply_markup)


# Асинхронная команда для получения лог-файла
async def get_log_file(update, context):
    try:
        with open(LOG_FILE, 'rb') as log_file:
            await context.bot.send_document(chat_id=ADMIN_CHAT_ID, document=log_file)
        logging.info("Лог-файл отправлен админу.")
    except Exception as e:
        logging.error(f"Ошибка при отправке лог-файла: {e}\n{traceback.format_exc()}")


# Асинхронная команда для изменения количества публикаций
async def set_publications(update, context):
    global publications_settings
    try:
        args = context.args
        publications_settings['videos_per_day'] = int(args[0])
        publications_settings['articles_per_day'] = int(args[1])
        publications_settings['books_per_day'] = int(args[2])
        await update.message.reply_text(
            f"Настройки публикаций обновлены: Видео - {args[0]}, Статьи - {args[1]}, Книги - {args[2]}")
        logging.info(f"Настройки публикаций обновлены: Видео - {args[0]}, Статьи - {args[1]}, Книги - {args[2]}")
    except (IndexError, ValueError):
        await update.message.reply_text(
            "Ошибка: Укажите три числа через пробел (видео, статьи, книги). Пример: /set_publications 3 5 2")


# Асинхронная команда для просмотра текущих настроек публикаций
async def get_publications(update, context):
    current_settings = (
        f"Текущие настройки публикаций:\n"
        f"Видео в сутки: {publications_settings['videos_per_day']}\n"
        f"Статей в сутки: {publications_settings['articles_per_day']}\n"
        f"Книг в сутки: {publications_settings['books_per_day']}\n"
        f"Время публикации: {schedule_settings['time']}\n"
    )
    await update.message.reply_text(current_settings)
    logging.info("Текущие настройки публикаций запрошены.")


# Асинхронная команда для изменения времени публикации
async def set_schedule(update, context):
    global schedule_settings
    try:
        new_time = context.args[0]
        schedule_settings['time'] = new_time
        await update.message.reply_text(f"Время публикации обновлено: {new_time}")
        logging.info(f"Время публикации обновлено: {new_time}")
        # Перезапуск расписания
        schedule.clear()
        setup_schedule()
    except IndexError:
        await update.message.reply_text("Ошибка: Укажите время в формате ЧЧ:ММ. Пример: /set_schedule 14:00")


# Асинхронная команда для поиска материалов
async def get_materials(update, context):
    await update.message.reply_text("Поиск материалов, пожалуйста, подождите...")
    materials = scrape_python_materials()
    if materials['videos'] or materials['articles'] or materials['books']:
        send_materials_for_approval(materials)
        await update.message.reply_text("Материалы отправлены админу на проверку.")
    else:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text="По расписанию не удалось найти новые материалы.")
        logging.info("По расписанию не удалось найти материалы.")


# Функция для отправки материалов админу на проверку
def send_materials_for_approval(materials):
    global pending_materials
    message = "Найдены материалы по Python, ожидающие вашей проверки:\n\n"

    # Сохраняем материалы для проверки
    pending_materials = materials

    # Добавляем видео
    message += "Видео:\n"
    for i, video in enumerate(materials['videos'], 1):
        message += f"{i}. {video['title']}: {video['url']} (Лицензия: {video['license']})\n"

    # Добавляем статьи
    message += "\nСтатьи:\n"
    for i, article in enumerate(materials['articles'], 1):
        message += f"{i}. {article['title']}: {article['url']} (Лицензия: {article['license']})\n"

    # Добавляем книги
    message += "\nКниги:\n"
    for i, book in enumerate(materials['books'], 1):
        message += f"{i}. {book['title']}: {book['url']} (Лицензия: {book['license']})\n"

    # Отправляем сообщение админу
    try:
        bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)
        logging.info("Материалы отправлены админу на проверку.")
    except telegram.error.TelegramError as e:
        logging.error(f"Ошибка отправки сообщения админу: {e}\n{traceback.format_exc()}")


# Функция для настройки расписания
def setup_schedule():
    schedule.every().day.at(schedule_settings['time']).do(asyncio.run, scheduled_task())


# Функция для гибкого управления планировщиком
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


# Основная функция для запуска бота
def main():
    application = Application.builder().token(TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("get_publications", get_publications))
    application.add_handler(CommandHandler("set_publications", set_publications))
    application.add_handler(CommandHandler("set_schedule", set_schedule))
    application.add_handler(CommandHandler("log", get_log_file))
    application.add_handler(CommandHandler("get_materials", get_materials))

    # Запускаем планировщик в отдельном потоке
    schedule_thread = Thread(target=run_schedule)
    schedule_thread.start()

    # Запускаем бота
    application.run_polling()


if __name__ == '__main__':
    main()
