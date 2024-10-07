import json
import os
import time
from tkinter import *
from tkinter import messagebox, ttk
from tkinter.filedialog import asksaveasfile

import requests

# Файл для хранения курсов валют (для кэширования)
CACHE_FILE = "currency_cache.json"

# Интервалы обновления курсов (в секундах)
UPDATE_INTERVALS = {
    "30 минут": 1800,
    "1 час": 3600,
    "6 часов": 21600,
    "12 часов": 43200,
    "24 часа": 86400
}


# Функция проверки сети
def check_network():
    """
    :rtype: bool
    :return: Returns True if a successful connection is made to "https://www.google.com" within the timeout period.
    Otherwise, returns False if a ConnectionError occurs.
    """
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except requests.ConnectionError:
        return False


# Функция для кэширования данных о курсах валют
def cache_exchange_rates(data: dict):
    """
    :param data: A dictionary containing exchange rate data where keys are currency codes and values are exchange rates.
    :return: None.
    This function writes the exchange rate data to a cache file named CACHE_FILE in JSON format.
    Along with a timestamp of when the data was cached.
    """
    with open(CACHE_FILE, "w") as f:
        json.dump({"rates": data, "timestamp": time.time()}, f)


# Функция для загрузки кэшированных данных
def load_cached_rates():
    """
    Load exchange rates from a cached file if it exists and is still valid.

    :return: Cached exchange rates if available and valid, otherwise None.
    """
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            cached_data = json.load(f)
            if time.time() - cached_data["timestamp"] < selected_update_interval.get():
                return cached_data["rates"]
    return None


# Функция для получения курсов валют (с кэшированием и оффлайн-режимом)
def get_exchange_rates(from_currency: str):
    """
    :param from_currency: The base currency for which to retrieve exchange rates.
    :return: A dictionary of exchange rates with currency codes as keys and rates as values, or None if an error occurs.
    """
    cached_rates = load_cached_rates()
    if cached_rates:
        return cached_rates
    if check_network():
        exchange_rate_api_url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        try:
            response = requests.get(exchange_rate_api_url)
            response.raise_for_status()
            data = response.json()
            cache_exchange_rates(data["rates"])
            return data["rates"]
        except requests.RequestException as e:
            messagebox.showerror("Ошибка сети", f"Ошибка при обращении к API: {e}")
            return None
    else:
        messagebox.showerror("Ошибка сети", "Нет подключения к сети, используем кэшированные данные.")
        return cached_rates


# Функция конвертации валюты
def convert_currency():
    """
    Converts an amount from one currency to another based on exchange rates obtained from an external service.
    Handles various error scenarios including non-numeric input and unsuccessful retrieval of exchange rates.
    Displays the conversion result and updates the conversion history.

    :return: None
    """
    from_currency = from_currency_combobox.get()
    to_currency = to_currency_combobox.get()
    try:
        amount = float(amount_entry.get())
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной.")
    except ValueError as ve:
        messagebox.showerror("Ошибка", f"Введите корректную сумму. {ve}")
        return

    rates = get_exchange_rates(from_currency)
    if rates and to_currency in rates:
        exchange_rate = rates[to_currency]
        result = amount * exchange_rate
        result_label.config(text=f"Результат: {amount:.2f} {from_currency} = {result:.2f} {to_currency}")
        add_to_history(amount, from_currency, to_currency, result)
    else:
        messagebox.showerror("Ошибка", "Не удалось получить курс валют.")


# Добавление конверсии в историю
def add_to_history(amount, from_currency, to_currency, result):
    """
    :param amount: The amount of currency to be converted.
    :param from_currency: The original currency code of the amount.
    :param to_currency: The target currency code for the conversion.
    :param result: The result of the currency conversion.
    :return: None
    """
    conversion = f"{amount:.2f} {from_currency} = {result:.2f} {to_currency}"
    history_listbox.insert(END, conversion)


# Сохранение истории в файл
def save_history():
    """
    Opens a save file dialog, allowing the user to save the contents of a ListBox widget to a text file.

    The function prompts the user with a file save dialog to choose where to save the contents of the history_listbox.
    If the user selects a file, the function retrieves the contents of the ListBox.
    Joins the items with a newline character, and writes the resulting string to the selected file.
    The file is then closed.

    :return: None
    """
    save_file = asksaveasfile(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if save_file:
        history = history_listbox.get(0, END)
        save_file.write("\n".join(history))
        save_file.close()


# Обновление курса валют по отношению к базовой валюте (USD)
def update_exchange_rates(rates_label=None):
    """
    :param rates_label: A tkinter label widget to display error messages if the exchange rates cannot be fetched.
    :return: None. The function updates the displayed exchange rates in the GUI.
    """
    rates = get_exchange_rates("USD")
    if rates:
        rates_display.delete(*rates_display.get_children())
        for currency, rate in rates.items():
            rates_display.insert("", "end", values=(currency, f"{rate:.2f}"))
    else:
        rates_label.config(text="Ошибка получения курсов.")


# Интерфейс программы
root = Tk()
root.title("Конвертер валют с кэшированием")
root.geometry("430x690")
root.resizable(False, False)

# Список валют
currencies = ["USD", "EUR", "RUB", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY"]

# Поля ввода
Label(root, text="Из валюты:").pack(pady=5)
from_currency_combobox = ttk.Combobox(root, values=currencies)
from_currency_combobox.pack(pady=5)
from_currency_combobox.current(0)  # USD по умолчанию

Label(root, text="В валюту:").pack(pady=5)
to_currency_combobox = ttk.Combobox(root, values=currencies)
to_currency_combobox.pack(pady=5)
to_currency_combobox.current(1)  # EUR по умолчанию

Label(root, text="Сумма для конвертации:").pack(pady=5)
amount_entry = Entry(root)
amount_entry.pack(pady=5)

# Кнопка для конвертации
convert_button = Button(root, text="Конвертировать", command=convert_currency)
convert_button.pack(pady=5)

# Результат конвертации
result_label = Label(root)
result_label.pack(pady=5)

# История конверсий
Label(root, text="История конверсий:").pack(pady=5)
history_listbox = Listbox(root, height=5)
history_listbox.pack(pady=5)

# Кнопка для сохранения истории
save_button = Button(root, text="Сохранить историю", command=save_history)
save_button.pack(pady=5)

# Выбор интервала обновления курсов
Label(root, text="Интервал обновления курсов:").pack(pady=5)
selected_update_interval = IntVar(value=UPDATE_INTERVALS["1 час"])
update_interval_combobox = ttk.Combobox(root, values=list(UPDATE_INTERVALS.keys()))
update_interval_combobox.pack(pady=5)
update_interval_combobox.current(1)  # По умолчанию "1 час"

# Таблица для отображения курсов валют
Label(root, text="Курсы валют относительно USD:").pack(pady=10)
columns = ("Валюта", "Курс")
rates_display = ttk.Treeview(root, columns=columns, show="headings", height=6)
for col in columns:
    rates_display.heading(col, text=col)
rates_display.pack(pady=10)

# Обновление курсов валют
update_exchange_rates()

# Запуск программы
root.mainloop()
