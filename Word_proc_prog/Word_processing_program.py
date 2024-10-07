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

# Downloading NLTK resources
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('universal_tagset', quiet=True)

# Initializing resources
STOP_WORDS = set(stopwords.words('russian'))
TRANSLATOR = str.maketrans('', '', string.punctuation)
stemmer = SnowballStemmer("russian")


def clean_text(text):
    """
    :param text: The input string that needs to be converted to lowercase and cleaned by removing certain characters.
    :return: The cleaned and lowercase version of the input text.
    """
    text = text.lower()
    return text.translate(TRANSLATOR)


def lemmatize_text(words):
    """
    :param words: A list of words to be lemmatized.
    :return: A list of lemmatized words.
    """
    return [stemmer.stem(word) for word in words]


def remove_stopwords(words):
    """
    :param words: List of words to be filtered.
    :return: List of words excluding the stop words.
    """
    return [word for word in words if word not in STOP_WORDS]


def perform_text_analysis(text):
    """
    :param text: A string input that contains the text to be analyzed.
    :return: A tuple containing the word count of the filtered words, a frequency Counter of the filtered words.
    The longest word among the filtered words, and the shortest word among the filtered words.
    """
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
    """
    :param word_freq: A Counter object containing words as keys and their frequencies as values.
    :return: None.
    The function displays a bar chart of the most common words, or a message box if there are no words to display.
    """
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
        messagebox.showinfo("No data to display", "The text is empty or contains only stop words.")


def display_results(word_count, word_freq, longest_word, shortest_word):
    """
    :param word_count: Total number of words identified in the text.
    :param word_freq: Dictionary representing the frequency of each word in the text.
    :param longest_word: The longest word found in the text.
    :param shortest_word: The shortest word found in the text.
    :return: Displays a window showing the word count, longest word, shortest word,
             and visualizes word frequency distribution.
    """
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
    """
    :param file_path: Path to the file whose encoding is to be detected.
    :return: Detected encoding of the file.
    """
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    return result['encoding']


def extract_text_from_pdf(filepath):
    """
    :param filepath: Path to the PDF file from which text needs to be extracted.
    :return: Extracted text from the entire PDF file as a single string.
    """
    document = fitz.open(filepath)
    text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text()
    return text


def select_and_process_file():
    """
    Prompts the user to select a file and processes the selected file based on its type.

    The function supports text files (*.txt), Word files (*.docx), and PDF files (*.pdf).
    It reads the content of the selected file, preprocesses the text.
    Performs text analysis, and displays and saves the results.

    :return: None
    """
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
                raise ValueError('Unsupported file format')

            preprocessed_text = clean_text(text)
            word_count, word_freq, longest_word, shortest_word = perform_text_analysis(preprocessed_text)
            display_results(word_count, word_freq, longest_word, shortest_word)
            save_results(word_count, word_freq, longest_word, shortest_word)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")


def save_results(word_count, word_freq, longest_word, shortest_word):
    """
    :param word_count: Total number of words in the text.
    :param word_freq: Dictionary containing word frequencies.
    :param longest_word: Longest word in the text.
    :param shortest_word: Shortest word in the text.
    :return: None
    """
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
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")


def determine_font_size(text):
    """
    :param text: The input string for which the font size needs to be determined.
    :return: An integer representing the calculated font size based on the length of the input text.
    """
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
