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
    Вставляет значение в поле ввода.

    :param value: Текстовое значение, которое будет вставлено в виджет ввода.
    """
    entry.insert(tk.END, value)


def clear_entry() -> None:
    """
    Очищает поле ввода.
    """
    entry.delete(0, tk.END)


def evaluate_and_show_result() -> None:
    """
    Вычисляет математическое выражение, введенное пользователем, и отображает результат.
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
    except (SyntaxError, NameError):
        messagebox.showerror(ERROR_TITLE, ERROR_MESSAGE)
    except Exception as e:
        messagebox.showerror(ERROR_TITLE, f"Ошибка: {e}")


def calculate_and_display_sqrt() -> None:
    """
    Вычисляет квадратный корень числа, введенного пользователем, и отображает результат.
    """
    try:
        user_input = float(entry.get())
        if user_input < 0:
            raise ValueError("Квадратный корень из отрицательного числа не определён")
        result = math.sqrt(user_input)
        clear_entry()
        entry.insert(tk.END, result)
    except ValueError as ve:
        messagebox.showerror(ERROR_TITLE, f"Ошибка: {ve}")
    except Exception:
        messagebox.showerror(ERROR_TITLE, ERROR_MESSAGE)


def calculate_and_display_trigonometric(func: callable) -> None:
    """
    Вычисляет тригонометрическую функцию для введенного пользователем значения.

    :param func: Функция (например, math.sin, math.cos), которая принимает радианы и возвращает результат.
    """
    try:
        user_input = float(entry.get())
        radians = math.radians(user_input)
        result = func(radians)
        clear_entry()
        entry.insert(tk.END, result)
    except ValueError:
        messagebox.showerror(ERROR_TITLE, "Введите корректное число")
    except Exception:
        messagebox.showerror(ERROR_TITLE, ERROR_MESSAGE)


def calculate_log() -> None:
    """
    Вычисляет десятичный логарифм введенного пользователем числа.
    """
    try:
        user_input = float(entry.get())
        if user_input <= 0:
            raise ValueError("Логарифм может быть вычислен только для положительных чисел")
        result = math.log10(user_input)
        clear_entry()
        entry.insert(tk.END, result)
    except ValueError as ve:
        messagebox.showerror(ERROR_TITLE, f"Ошибка: {ve}")
    except Exception:
        messagebox.showerror(ERROR_TITLE, ERROR_MESSAGE)


# Создание кнопок
buttons = [
    ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3),
    ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3),
    ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
    ('0', 4, 0), ('.', 4, 1), ('=', 4, 2), ('+', 4, 3),
]

for (text, row, col) in buttons:
    action = (lambda x=text: insert_value(x)) if text != "=" else evaluate_and_show_result
    tk.Button(root, text=text, command=action, width=5, height=2).grid(row=row, column=col)

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
