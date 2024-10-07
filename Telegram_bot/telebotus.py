import telebot
import requests
import nltk
import os
import threading
import time
import schedule
from nltk.tokenize import word_tokenize

nltk.download('punkt')

# Correctly fetch the environment variable
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
if TELEGRAM_API_TOKEN is None or WEATHER_API_KEY is None or NEWS_API_KEY is None:
    raise ValueError(
        "One or more environment variables are not set."
        " Please set TELEGRAM_API_TOKEN, WEATHER_API_KEY, and NEWS_API_KEY environment variables."
    )

bot = telebot.TeleBot(TELEGRAM_API_TOKEN)
news_cache = ""
news_cache_lock = threading.Lock()


# Function to fetch news
def fetch_news():
    global news_cache
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        articles = data.get('articles', [])
        with news_cache_lock:
            news_cache = "\n".join([f"{article['title']}: {article['url']}" for article in articles[:5]])
    except requests.exceptions.RequestException as e:
        update_news_cache(f"Request error: {e}")
    except Exception as e:
        update_news_cache(f"Error fetching news: {e}")


def update_news_cache(message):
    global news_cache
    with news_cache_lock:
        news_cache = message


# Weather command
@bot.message_handler(commands=['weather'])
def send_weather(message):
    try:
        city = extract_city_from_message(message.text.lower())
        if city is None:
            bot.reply_to(message, "Specify the city, for example: /weather Moscow")
            return
        weather_data = get_weather(city)
        bot.reply_to(message, weather_data)
    except Exception as e:
        bot.reply_to(message, "Something went wrong while fetching the weather data.")
        print(f"Error: {e}")


def extract_city_from_message(text):
    parts = text.split()
    return parts[1] if len(parts) >= 2 else None


def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get('cod') == 200:
            temp = data['main']['temp']
            description = data['weather'][0]['description']
            return f"Weather in {city}: {temp}°C, {description}"
        return "City not found."
    except requests.exceptions.RequestException as e:
        return f"Request error: {e}"


# Exchange rates command
@bot.message_handler(commands=['rates'])
def send_rates(message):
    rates = get_exchange_rates()
    bot.reply_to(message, rates)


def get_exchange_rates():
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        rates = data.get('rates', {})
        return f"USD to EUR: {rates.get('EUR', 'N/A')}, USD to RUB: {rates.get('RUB', 'N/A')}"
    except requests.exceptions.RequestException as e:
        return f"Request error: {e}"


# News command
@bot.message_handler(commands=['news'])
def send_news(message):
    with news_cache_lock:
        bot.reply_to(message, news_cache)


# Natural language processing
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    response = respond_to_message(message.text.lower())
    bot.reply_to(message, response)


def respond_to_message(text):
    tokens = word_tokenize(text)
    if 'weather' in tokens:
        return "Use the /weather command for weather information."
    elif 'rates' in tokens:
        return "Use the /rates command for exchange rates."
    elif 'news' in tokens:
        return "Use the /news command for latest news."
    return "I don't understand your request."


# Schedule the news fetching every 5 minutes
def schedule_news_updates():
    schedule.every(5).minutes.do(fetch_news)
    while True:
        schedule.run_pending()
        time.sleep(1)


# Start threading for scheduled tasks
news_thread = threading.Thread(target=schedule_news_updates)
news_thread.start()

# Bot polling
if __name__ == "__main__":
    bot.polling()