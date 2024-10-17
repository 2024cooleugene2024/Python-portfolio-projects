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
import asyncio

# Bot token and channel IDs
TOKEN = '7699074411:AAHlsR_ZOlW9rPMwAzZIpTPIk4x_1vzsK3w'  # Replace with your bot token
CHAT_ID = 'Community_Python'
ADMIN_CHAT_ID = '@cooleugene2012'

# Logging setup
LOG_FILE = 'bot_log.txt'
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Publication settings
publications_settings = {
    'videos_per_day': 3,
    'articles_per_day': 3,
    'books_per_day': 1
}

schedule_settings = {
    'time': '09:00',
    'paused': False,
    'days': ['Monday', 'Wednesday', 'Friday'],
    'delete_after_days': 7,
    'repeat_interval_hours': 24
}

last_publication_date = None
published_materials = {}

# Create bot instance
bot = telegram.Bot(token=TOKEN)

# Storage for materials pending approval
pending_materials = {}


# Function to check licenses
def check_license(material_type, license_info):
    if material_type == 'video':
        return license_info == 'creativeCommon'
    elif material_type in ['article', 'book']:
        return 'creativecommons' in license_info.lower() or 'mit' in license_info.lower() or 'apache' in license_info.lower()
    return False


# Main function for scraping sites with error handling and license checks
def scrape_python_materials():
    materials = {'videos': [], 'articles': [], 'books': []}
    youtube_api_key = 'YOUR_YOUTUBE_API_KEY_HERE'  # Replace with your API key
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
        logging.error(f"Error fetching videos: {e}\n{traceback.format_exc()}")

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
        logging.error(f"Error fetching articles from Medium: {e}\n{traceback.format_exc()}")

    book_url = "https://codelibrary.info/books/python"  # Replace with the actual URL
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
        logging.error(f"Error fetching books: {e}\n{traceback.format_exc()}")

    return materials


# Function to send materials for approval
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
        logging.error(f"Error sending message to admin: {e}\n{traceback.format_exc()}")


# Function to publish materials
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
        logging.info("Materials published in Telegram.")
        last_publication_date = datetime.now()
        published_materials[last_publication_date] = materials
    except telegram.error.TelegramError as e:
        logging.error(f"Error sending message to Telegram: {e}\n{traceback.format_exc()}")


# Command to approve publication
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Материалы одобрены и будут опубликованы.")
    logging.info("Materials approved by admin.")
    post_to_telegram()


# Command to reject publication
async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global pending_materials
    pending_materials = {}
    await update.message.reply_text("Материалы отклонены и не будут опубликованы.")
    logging.info("Materials rejected by admin.")


# Command to get log file
async def get_log_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(LOG_FILE, 'rb') as log_file:
            await bot.send_document(chat_id=ADMIN_CHAT_ID, document=log_file)
        logging.info("Log file sent to admin.")
    except Exception as e:
        logging.error(f"Error sending log file: {e}\n{traceback.format_exc()}")


# Command to change publication settings
async def set_publications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global publications_settings
    try:
        args = context.args
        publications_settings['videos_per_day'] = int(args[0])
        publications_settings['articles_per_day'] = int(args[1])
        publications_settings['books_per_day'] = int(args[2])
        await update.message.reply_text(
            f"Настройки публикации обновлены:\n"
            f"Видео в день: {publications_settings['videos_per_day']}\n"
            f"Статьи в день: {publications_settings['articles_per_day']}\n"
            f"Книги в день: {publications_settings['books_per_day']}"
        )
        logging.info("Publication settings updated.")
    except (IndexError, ValueError):
        await update.message.reply_text("Пожалуйста, укажите количество видео, статей и книг через пробел.")
        logging.error("Error updating publication settings.")


# Function to run scheduled tasks
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


# Schedule tasks
schedule.every().day.at(schedule_settings['time']).do(lambda: send_materials_for_approval(scrape_python_materials()))
schedule.every().day.at(schedule_settings['time']).do(post_to_telegram)

# Start the bot and the schedule thread
if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("reject", reject))
    application.add_handler(CommandHandler("get_log_file", get_log_file))
    application.add_handler(CommandHandler("set_publications", set_publications))

    # Start the bot
    application.run_polling()

    # Start the schedule in a separate thread
    schedule_thread = Thread(target=run_schedule)
    schedule_thread.start()
