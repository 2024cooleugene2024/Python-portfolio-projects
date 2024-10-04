import os
import string
import tkinter as tk
from collections import Counter
from tkinter import filedialog, messagebox

import chardet
import docx
import fitz  # PyMuPDF
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

# Скачивание ресурсов NLTK
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('universal_tagset', quiet=True)

# Инициализация ресурсов
STOP_WORDS = set(stopwords.words('russian'))
TRANSLATOR = str.maketrans('', '', string.punctuation)
stemmer = SnowballStemmer("russian")


def clean_text(text):
    text = text.lower()
    return text.translate(TRANSLATOR)


def lemmatize_text(words):
    return [stemmer.stem(word) for word in words]


def remove_stopwords(words):
    return [word for word in words if word not in STOP_WORDS]


def perform_text_analysis(text):
    words = nltk.word_tokenize(text)
    lemmatized_words = lemmatize_text(words)
    filtered_words = remove_stopwords(lemmatized_words)
    word_count = len(filtered_words)
    if word_count == 0:
        longest_word = ""
        shortest_word = ""
    else:
        longest_word = max(filtered_words, key=len)
        shortest_word = min(filtered_words, key=len)
    word_freq = Counter(filtered_words)
    return word_count, word_freq, longest_word, shortest_word


def visualize_word_freq(word_freq):
    most_common_words = word_freq.most_common(10)
    if most_common_words:
        words, counts = zip(*most_common_words)
        plt.bar(words, counts)
        plt.xlabel('Words')
        plt.ylabel('Frequency')
        plt.title('Frequency of Most Popular Words')
        plt.xticks(rotation=45)
        plt.show()
    else:
        messagebox.showinfo("Нет данных для отображения", "Текст пуст или содержит только стоп-слова.")


def display_results(word_count, word_freq, longest_word, shortest_word):
    result_text = f"Word count: {word_count}\n" \
                  f"Longest word: {longest_word}\n" \
                  f"Shortest word: {shortest_word}\n"
    result_window = tk.Toplevel(root)
    result_window.title("Analysis Results")
    result_window.geometry("500x150")
    result_window.resizable(False, False)

    font_size = determine_font_size(result_text)

    result_label = tk.Label(result_window, text=result_text, font=("Helvetica", font_size))
    result_label.pack(expand=True)

    visualize_word_freq(word_freq)


def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    return result['encoding']


def extract_text_from_pdf(filepath):
    document = fitz.open(filepath)
    text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text()
    return text


def select_and_process_file():
    filepath = filedialog.askopenfilename(
        filetypes=[("Text files", "*.txt"), ("Word files", "*.docx"), ("PDF files", "*.pdf")])
    if filepath:
        try:
            if filepath.endswith('.txt'):
                encoding = detect_encoding(filepath)
                with open(filepath, 'r', encoding=encoding) as file:
                    text = file.read()
            elif filepath.endswith('.docx'):
                doc = docx.Document(filepath)
                text = '\n'.join([para.text for para in doc.paragraphs])
            elif filepath.endswith('.pdf'):
                text = extract_text_from_pdf(filepath)
            else:
                raise ValueError('Неподдерживаемый формат файла')

            preprocessed_text = clean_text(text)
            word_count, word_freq, longest_word, shortest_word = perform_text_analysis(preprocessed_text)
            display_results(word_count, word_freq, longest_word, shortest_word)
            save_results(word_count, word_freq, longest_word, shortest_word)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл: {str(e)}")


def save_results(word_count, word_freq, longest_word, shortest_word):
    save_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if save_path:
        try:
            with open(save_path, 'w', encoding='utf-8') as file:
                result_text = f"Word count: {word_count}\n" \
                              f"Longest word: {longest_word}\n" \
                              f"Shortest word: {shortest_word}\n" \
                              f"Word frequencies: {dict(word_freq)}\n"
                file.write(result_text)
            os.startfile(save_path, "print")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")


def determine_font_size(text):
    max_characters = 300
    base_font_size = 10
    if len(text) <= max_characters:
        return base_font_size
    else:
        return max(8, base_font_size - (len(text) - max_characters) // 50)


root = tk.Tk()
root.title("Text Analysis")
root.geometry("500x150")
root.resizable(False, False)

load_button = tk.Button(root, text="Load File", command=select_and_process_file)
load_button.pack(pady=10)

result_label = tk.Label(root, text="")
result_label.pack(pady=10)

root.mainloop()