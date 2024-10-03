import tkinter as tk
from tkinter import messagebox
import math

# Константы для сообщений об ошибках
ERROR_TITLE = "Ошибка"
ERROR_MESSAGE = "Некорректный ввод, допустим ввод только чисел для операций"
DIV_ZERO_MESSAGE = "Деление на ноль!"

# Основное окно
root = tk.Tk()
root.title("Инженерный Калькулятор")
root.geometry("375x300")
root.resizable(False, False)

# Поле для ввода
entry = tk.Entry(root, width=32, font=("Arial", 14))
entry.grid(row=0, column=0, columnspan=5, padx=10, pady=10)


# Функции для работы с калькулятором
def insert_value(value: str) -> None:
    """
    :param value: Текстовое значение, которое будет вставлено в виджет ввода.
    """
    entry.insert(tk.END, value)


def clear_entry() -> None:
    """
    Очищает содержимое текстового виджета ввода, удаляя текст от начала (индекс 0) до конца.

    :return: None
    """
    entry.delete(0, tk.END)


def evaluate_and_show_result() -> None:
    """
    Вычисляет математическое выражение, введенное пользователем, и отображает результат.
    Извлекает выражение из виджета ввода, вычисляет его и обрабатывает любые исключения.
    Если выражение вычислено успешно, результат отображается;
    в противном случае пользователю показывается сообщение об ошибке.

    :return: None
    """
    expression = entry.get()
    try:
        result = eval(expression)
        # Проверка на бесконечность (деление на ноль)
        if result == float('inf') or result == -float('inf'):
            raise ZeroDivisionError
        clear_entry()
        entry.insert(tk.END, result)
    except ZeroDivisionError:
        messagebox.showerror(ERROR_TITLE, DIV_ZERO_MESSAGE)
    except Exception:
        messagebox.showerror(ERROR_TITLE, ERROR_MESSAGE)


# noinspection PyTypeChecker
def calculate_and_display_sqrt() -> None:
    """
    Вычисляет квадратный корень числа, введенного пользователем, и отображает результат.

    Функция получает числовой ввод от пользователя через графический интерфейс ввода,
    вычисляет его квадратный корень и затем обновляет виджет ввода полученным значением.
    Если ввод не является допустимым числом, отображается сообщение об ошибке.

    :return: None
    """
    try:
        user_input = float(entry.get())
        result = math.sqrt(user_input)
        clear_entry()
        entry.insert(tk.END, result)
    except ValueError:
        messagebox.showerror(ERROR_TITLE, "Введите корректное число")
    except Exception:
        messagebox.showerror(ERROR_TITLE, ERROR_MESSAGE)


def calculate_and_display_trigonometric(func: callable) -> None:
    """
    :param func: Функция, которая принимает один аргумент типа float (в радианах) и возвращает float.
    Пример: math.sin, math.cos.
    :return: None
    """
    try:
        user_input = float(entry.get())
        if user_input:
            radians = math.radians(user_input)
            result = func(radians)
            clear_entry()
            entry.insert(tk.END, result)
        else:
            raise ValueError
    except ValueError:
        messagebox.showerror(ERROR_TITLE, "Введите корректное число")
    except Exception:
        messagebox.showerror(ERROR_TITLE, ERROR_MESSAGE)


# noinspection PyTypeChecker
def calculate_log() -> None:
    """
    Вычисляет десятичный логарифм введенного пользователем числа.
    Если пользователь ввел положительное число, результат вставляется обратно в виджет ввода.
    Если ввод не является положительным числом или недопустим, отображаются соответствующие сообщения об ошибках.

    :return: None
    """
    try:
        user_input = float(entry.get())
        if user_input > 0:
            result = math.log10(user_input)
            clear_entry()
            entry.insert(tk.END, result)
        else:
            raise ValueError
    except ValueError:
        messagebox.showerror(ERROR_TITLE, "Введите положительное число")
    except Exception:
        messagebox.showerror(ERROR_TITLE, ERROR_MESSAGE)


# Кнопки
buttons = [
    '7', '8', '9', '/',
    '4', '5', '6', '*',
    '1', '2', '3', '-',
    '0', '.', '=', '+'
]
row_val = 1
col_val = 0
for button in buttons:
    action = lambda x=button: insert_value(x) if x != "=" else evaluate_and_show_result()
    tk.Button(root, text=button, command=action, width=5, height=2).grid(row=row_val, column=col_val)
    col_val += 1
    if col_val > 3:
        col_val = 0
        row_val += 1

# Дополнительные функциональные кнопки
additional_buttons = {
    'C': clear_entry,
    '√': calculate_and_display_sqrt,
    'sin': lambda: calculate_and_display_trigonometric(math.sin),
    'cos': lambda: calculate_and_display_trigonometric(math.cos),
    'tan': lambda: calculate_and_display_trigonometric(math.tan),
    'log': calculate_log
}
row_val = 1
col_val = 4
for button, action in additional_buttons.items():
    tk.Button(root, text=button, command=action, width=5, height=2).grid(row=row_val, column=col_val)
    row_val += 1

# Запуск приложения
root.mainloop()