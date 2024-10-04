import json
import os
import time
import requests
from tkinter import *
from tkinter import messagebox, ttk
from tkinter.filedialog import asksaveasfile

# File for storing currency rates (for caching)
CACHE_FILE = "currency_cache.json"

# Update intervals in seconds
UPDATE_INTERVALS = {
    "30 minutes": 1800,
    "1 hour": 3600,
    "6 hours": 21600,
    "12 hours": 43200,
    "24 hours": 86400
}

# Network check function
def check_network():
    """
    Returns True if a successful connection is made to "https://www.google.com" within the timeout period.
    Otherwise, returns False if a ConnectionError occurs.
    """
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except requests.ConnectionError:
        return False

# Function to cache exchange rate data
# noinspection PyTypeChecker
def cache_exchange_rates(data: dict):
    """
    Writes the exchange rate data to a cache file named CACHE_FILE in JSON format
    along with a timestamp of when the data was cached.
    """
    with open(CACHE_FILE, "w") as f:
        json.dump({"rates": data, "timestamp": time.time()}, f)

# Function to load cached data
def load_cached_rates():
    """
    Load exchange rates from a cached file if it exists and is still valid.
    Returns cached exchange rates if available and valid, otherwise None.
    """
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            cached_data = json.load(f)
            if time.time() - cached_data["timestamp"] < selected_update_interval.get():
                return cached_data["rates"]
    return None

# Function to get exchange rates (with caching and offline mode)
def get_exchange_rates(from_currency: str):
    """
    Retrieves exchange rates with caching and network checks.
    Returns a dictionary of exchange rates or None if an error occurs.
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
            messagebox.showerror("Network Error", f"Error accessing API: {e}")
            return None
    else:
        messagebox.showerror("Network Error", "No network connection, using cached data.")
        return cached_rates

# Currency conversion function
def convert_currency():
    """
    Converts an amount from one currency to another based on exchange rates obtained from an external service.
    Displays the conversion result and updates the conversion history.
    """
    from_currency = from_currency_combobox.get()
    to_currency = to_currency_combobox.get()
    try:
        amount = float(amount_entry.get())
        if amount <= 0:
            raise ValueError("Amount must be positive.")
    except ValueError as ve:
        messagebox.showerror("Error", f"Please enter a valid amount. {ve}")
        return
    rates = get_exchange_rates(from_currency)
    if rates and to_currency in rates:
        exchange_rate = rates[to_currency]
        result = amount * exchange_rate
        result_label.config(text=f"Result: {amount:.2f} {from_currency} = {result:.2f} {to_currency}")
        add_to_history(amount, from_currency, to_currency, result)
    else:
        messagebox.showerror("Error", "Failed to retrieve exchange rate.")

# Adding conversion to history
def add_to_history(amount, from_currency, to_currency, result):
    """
    Records the currency conversion in the history list.
    """
    conversion = f"{amount:.2f} {from_currency} = {result:.2f} {to_currency}"
    history_listbox.insert(END, conversion)

# Saving history to a file
def save_history():
    """
    Opens a save file dialog, allowing the user to save the contents of the ListBox widget to a text file.
    """
    save_file = asksaveasfile(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if save_file:
        history = history_listbox.get(0, END)
        save_file.write("\n".join(history))
        save_file.close()

# Update exchange rates relative to the base currency (USD)
def update_exchange_rates():
    """
    Updates the displayed exchange rates in the GUI.
    """
    rates = get_exchange_rates("USD")
    if rates:
        rates_display.delete(*rates_display.get_children())
        for currency, rate in rates.items():
            rates_display.insert("", "end", values=(currency, f"{rate:.2f}"))
    else:
        messagebox.showerror("Error", "Failed to retrieve exchange rates.")

# Program interface
root = Tk()
root.title("Currency Converter with Caching")
root.geometry("430x690")
root.resizable(False, False)

# Background image (depending on the selected currency)
currency_label = Label(root)
currency_label.pack(side=TOP, fill=BOTH, expand=True)

# Currency list
currencies = ["USD", "EUR", "RUB", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY"]

# Input fields
Label(root, text="From Currency:").pack(pady=5)
from_currency_combobox = ttk.Combobox(root, values=currencies)
from_currency_combobox.pack(pady=5)
from_currency_combobox.current(0)  # USD by default
Label(root, text="To Currency:").pack(pady=5)
to_currency_combobox = ttk.Combobox(root, values=currencies)
to_currency_combobox.pack(pady=5)
to_currency_combobox.current(1)  # EUR by default
Label(root, text="Amount to Convert:").pack(pady=5)
amount_entry = Entry(root)
amount_entry.pack(pady=5)

# Convert button
convert_button = Button(root, text="Convert", command=convert_currency)
convert_button.pack(pady=10)

# Conversion result
result_label = Label(root)
result_label.pack(pady=10)

# Conversion history
Label(root, text="Conversion History:").pack(pady=5)
history_listbox = Listbox(root, height=5)
history_listbox.pack(pady=5)

# Save history button
save_button = Button(root, text="Save History", command=save_history)
save_button.pack(pady=5)

# Update interval selection
Label(root, text="Update Interval:").pack(pady=5)
selected_update_interval = IntVar(value=UPDATE_INTERVALS["1 hour"])
update_interval_combobox = ttk.Combobox(root, values=list(UPDATE_INTERVALS.keys()))
update_interval_combobox.pack(pady=5)
update_interval_combobox.current(1)  # Default "1 hour"

# Table for displaying exchange rates
Label(root, text="Exchange Rates relative to USD:").pack(pady=10)
columns = ("Currency", "Rate")
rates_display = ttk.Treeview(root, columns=columns, show="headings", height=6)
for col in columns:
    rates_display.heading(col, text=col)
rates_display.pack(pady=10)

# Update exchange rates
update_exchange_rates()

# Run the program
root.mainloop()
