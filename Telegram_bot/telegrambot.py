import os
import requests
import telegram
from bs4 import BeautifulSoup
import schedule
import asyncio
import time
import json
from threading import Thread
import logging
import traceback
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import ReplyKeyboardMarkup

# Загружаем переменные окружения из файла .env
load_dotenv()

# Токен бота и ID чата
TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

# Настройка логирования
LOGFILE = 'bot_log.txt'
logging.basicConfig(filename=LOGFILE, level=logging.INFO, format='%(asctime)s - %(message)s')

# Параметры публикации и время проверки
publications_settings = {'articles_per_day': 10}
check_interval_minutes = 5  # Интервал проверки в минутах
cleanup_limit = 50  # Лимит статей для очистки по умолчанию
cleanup_limit_file = 'cleanup_limit.json'  # Файл для сохранения лимита
articles_file = 'articles.json'  # Файл для хранения статей

# Создаем экземпляр бота
bot = telegram.Bot(token=TOKEN)


# Функция для логирования сообщений
def log_message(message):
    logging.info(message)



# Функция для загрузки сохранённых статей
def load_articles():
    if os.path.exists(articles_file):
        with open(articles_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'articles': []}


# Функция для сохранения статей
def save_articles(articles):
    with open(articles_file, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)


# Функция для загрузки лимита статей для очистки
def load_cleanup_limit():
    if os.path.exists(cleanup_limit_file):
        with open(cleanup_limit_file, 'r', encoding='utf-8') as f:
            return json.load(f).get('limit', 50)
    return 50  # Лимит по умолчанию


# Функция для сохранения лимита статей для очистки
def save_cleanup_limit(limit):
    with open(cleanup_limit_file, 'w', encoding='utf-8') as f:
        json.dump({'limit': limit}, f, ensure_ascii=False, indent=4)


# Функция для проверки уникальности нумерации
def is_unique_numbering(articles):
    """Проверяет, что каждая статья имеет уникальный номер в начале заголовка."""
    seen_numbers = set()
    for article in articles['articles']:
        try:
            num = int(article['title'].split('. ', 1)[0])  # Извлекаем номер
            if num in seen_numbers:
                return False
            seen_numbers.add(num)
        except (ValueError, IndexError):
            return False  # Номер отсутствует или некорректный формат
    return True


# Функция для добавления статей с уникальной нумерацией
def add_articles(new_articles):
    articles = load_articles()
    current_count = len(articles['articles'])

    # Проверяем, чтобы не было конфликтов в нумерации
    for i, article in enumerate(new_articles):
        article['title'] = f"{current_count + i + 1}. {article['title']}"
        articles['articles'].append(article)

    if not is_unique_numbering(articles):  # Перенумеровываем, если есть конфликты
        renumber_articles(articles)
    else:
        save_articles(articles)


# Функция для пересчёта нумерации статей
def renumber_articles(articles):
    """Перенумеровывает статьи, обеспечивая уникальную нумерацию."""
    for i, article in enumerate(articles['articles']):
        # Удаляем предыдущий номер, если он есть
        title_without_number = article['title'].split(". ", 1)[-1]
        article['title'] = f"{i + 1}. {title_without_number}"
    save_articles(articles)


# Функция для удаления старых статей по лимиту
def clean_up_articles():
    articles = load_articles()
    limit = load_cleanup_limit()  # Загружаем лимит
    if len(articles['articles']) > limit:
        articles['articles'] = articles['articles'][-limit:]  # Убираем лишние статьи
        renumber_articles(articles)  # Перенумеровываем оставшиеся статьи
        log_message(f"Удалены старые статьи. Оставлено {len(articles['articles'])} статей.")


# Функция для ручного удаления статей по заголовку
async def delete_article(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    title_to_delete = ' '.join(context.args)  # Аргументы после команды — заголовок
    articles = load_articles()

    # Фильтруем статьи, которые не совпадают с заголовком (без нумерации)
    new_articles = [article for article in articles['articles'] if
                    article['title'].split(". ", 1)[-1] != title_to_delete]

    if len(new_articles) == len(articles['articles']):
        await update.message.reply_text(f"Статья с заголовком '{title_to_delete}' не найдена.")
    else:
        save_articles({'articles': new_articles})
        renumber_articles({'articles': new_articles})  # Перенумеровываем оставшиеся статьи
        await update.message.reply_text(f"Статья '{title_to_delete}' успешно удалена.")
        log_message(f"Удалена статья: {title_to_delete}")


# Асинхронная функция для скрапинга статей с Habr (пример для Python)
async def scrape_habr():
    materials = {'articles': []}
    habr_url = 'https://habr.com/ru/search/?q=python&target_type=posts&order=relevance'
    try:
        response = requests.get(habr_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article')

        for article in articles[:publications_settings['articles_per_day']]:
            title = article.find('h2').text
            url = 'https://habr.com' + article.find('a')['href']
            license_info = 'Creative Commons'
            materials['articles'].append({'title': title, 'url': url, 'license': license_info})
        add_articles(materials['articles'])  # Добавляем статьи с нумерацией
    except requests.RequestException as e:
        log_message(f'Ошибка при запросе статей с Habr: {e}\n{traceback.format_exc()}')
    return materials


# Универсальная функция для скрапинга статей из заданного URL
async def scrape_habr_hub(hub_url):
    materials = {'articles': []}
    try:
        response = requests.get(hub_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article')

        for article in articles[:publications_settings['articles_per_day']]:
            title = article.find('h2').text
            url = 'https://habr.com' + article.find('a')['href']
            license_info = 'Creative Commons'
            materials['articles'].append({'title': title, 'url': url, 'license': license_info})
        add_articles(materials['articles'])  # Добавляем статьи с нумерацией
    except requests.RequestException as e:
        log_message(f'Ошибка при запросе статей с Habr: {e}\n{traceback.format_exc()}')
    return materials


# Асинхронная функция для публикации материалов в Telegram
async def publish_materials():
    materials = await scrape_habr()
    published_count = 0
    for material in materials['articles']:
        message = f"<b>Статья:</b> {material['title']}\n" \
                  f"<b>Ссылка:</b> <a href='{material['url']}'>Читать здесь</a>"
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
        log_message(f'Опубликовано: {material["title"]}')
        published_count += 1
        await asyncio.sleep(2)
    return published_count


# Планировщик для запуска публикаций и очистки статей раз в неделю
def schedule_publications():
    schedule.every(check_interval_minutes).minutes.do(lambda: asyncio.run(publish_materials()))
    schedule.every().sunday.at("00:00").do(clean_up_articles)  # Очистка каждое воскресенье
    while True:
        schedule.run_pending()
        time.sleep(1)


# Команда /start для вывода меню и автоматического запуска парсинга
async def start(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["/run_parser", "/delete_article"],  # Первая строка кнопок
        ["/set_cleanup_limit", "/set_schedule"],  # Вторая строка кнопок
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Запуск парсера и публикации статей...", reply_markup=reply_markup)
    published_count = await publish_materials()  # Автоматический парсинг и публикация
    await update.message.reply_text(
        f"Здравствуйте! Я бот для публикации статей с Habr.\n"
        f"Опубликовано {published_count} новых статей.\n"
        "Команды:\n"
        "/run_parser - запустить парсер статей вручную\n"
        "/delete_article <заголовок> - удалить статью по заголовку\n"
        "/set_cleanup_limit <число> - установить количество статей для хранения\n"
        "/set_schedule - установить расписание парсинга",
        reply_markup=reply_markup
    )


# Команда для установки лимита статей, которые нужно оставить
async def set_cleanup_limit(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        limit = int(context.args[0])
        save_cleanup_limit(limit)
        await update.message.reply_text(f"Лимит статей для хранения установлен на {limit}.")
    except (ValueError, IndexError):
        await update.message.reply_text("Пожалуйста, укажите корректное число для лимита статей.")


# Команда /run_parser для ручного запуска парсера
async def run_parser(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    published_count = await publish_materials()
    await update.message.reply_text(f"Парсер был запущен вручную, опубликовано {published_count} статей.")


# Команда /set_schedule для установки расписания
async def set_schedule(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Проверка статей с Habr будет происходить каждые {check_interval_minutes} минут.")


# Запуск бота и планировщика в отдельном потоке
def run_bot():
    bot_thread = Thread(target=schedule_publications)
    bot_thread.start()


# Основная функция для запуска бота
if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("run_parser", run_parser))
    application.add_handler(CommandHandler("delete_article", delete_article))
    application.add_handler(CommandHandler("set_cleanup_limit", set_cleanup_limit))
    application.add_handler(CommandHandler("set_schedule", set_schedule))
    # Запуск бота
    run_bot()
    application.run_polling()
