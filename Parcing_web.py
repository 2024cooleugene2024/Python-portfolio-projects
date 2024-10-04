# This script uses Selenium to scrape job vacancy data from a specified website.
# It initializes a headless Chrome browser, navigates through paginated job listings,
# extracts job titles, company names, and salaries, and saves the collected data
# into CSV and JSON formats. The script can be customized for different websites
# by modifying the parsing logic and the base URL.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import json

# Настройка драйвера для Chrome
def get_driver():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Запуск браузера в фоновом режиме
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# Функция для парсинга одной страницы
def parse_page(driver):
    data = []
    # Пример поиска элементов на странице (нужно адаптировать под конкретный сайт)
    items = driver.find_elements(By.CLASS_NAME, 'vacancy-item')
    for item in items:
        title = item.find_element(By.TAG_NAME, 'h2').text.strip()
        company = item.find_element(By.CLASS_NAME, 'company-name').text.strip()
        salary = item.find_element(By.CLASS_NAME, 'salary').text.strip() if item.find_elements(By.CLASS_NAME, 'salary') else 'Не указана'
        data.append({
            'title': title,
            'company': company,
            'salary': salary
        })
    return data

# Функция для обработки пагинации
def get_all_pages(base_url, max_pages=5):
    driver = get_driver()
    all_data = []
    try:
        for page in range(1, max_pages + 1):
            url = f"{base_url}?page={page}"
            driver.get(url)
            time.sleep(2)  # Задержка для загрузки страницы
            page_data = parse_page(driver)
            all_data.extend(page_data)
            # Пример нажатия на кнопку для перехода на следующую страницу (если пагинация на кнопках)
            next_button = driver.find_elements(By.CLASS_NAME, 'next-page')
            if next_button:
                next_button[0].click()
                time.sleep(2)  # Задержка на случай анимации
            else:
                break
    finally:
        driver.quit()
    return all_data

# Функция для сохранения данных в CSV
def save_to_csv(data, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        # noinspection PyTypeChecker
        writer = csv.DictWriter(f, fieldnames=['title', 'company', 'salary'])
        writer.writeheader()
        writer.writerows(data)

# Функция для сохранения данных в JSON
def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        # noinspection PyTypeChecker
        json.dump(data, f, ensure_ascii=False, indent=4)

# Основная функция
def main():
    base_url = 'https://example.com/vacancies'  # Замените на реальный сайт
    data = get_all_pages(base_url, max_pages=5)
    # Сохранение данных
    save_to_csv(data, 'vacancies_selenium.csv')
    save_to_json(data, 'vacancies_selenium.json')

if __name__ == "__main__":
    main()