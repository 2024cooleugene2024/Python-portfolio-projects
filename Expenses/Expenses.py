import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox


def init_db():
    """
    Initializes the database and creates the expenses table if it doesn't exist.
    The expenses table has the following columns:
    - id: INTEGER PRIMARY KEY
    - amount: REAL
    - category: TEXT
    - date: TEXT
    - comment: TEXT
    """
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
                        id INTEGER PRIMARY KEY,
                        amount REAL,
                        category TEXT,
                        date TEXT,
                        comment TEXT)''')
    conn.commit()
    conn.close()


def add_expense(amount, category, comment=""):
    """
    Adds a new expense to the expenses table.

    Parameters:
    - amount (float): The amount of the expense.
    - category (str): The category of the expense.
    - comment (str): The comment for the expense (optional, default is an empty string).
    """
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO expenses (amount, category, date, comment) VALUES (?, ?, ?, ?)",
                   (amount, category, date, comment))
    conn.commit()
    conn.close()


def get_expenses():
    """
    Retrieves all expenses from the expenses table.

    Returns:
    - rows (list): A list of tuples, where each tuple represents an expense.
    """
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    rows = cursor.fetchall()
    conn.close()
    return rows


def plot_expenses():
    """
    Plots a pie chart of expenses by category.
    """
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    data = cursor.fetchall()
    conn.close()

    if not data:
        messagebox.showinfo("Информация", "Нет данных для отображения.")
        return

    categories = [row[0] for row in data]
    amounts = [row[1] for row in data]

    plt.figure(figsize=(6, 6))
    plt.pie(amounts, labels=categories, autopct='%1.1f%%')
    plt.title('Расходы по категориям')
    plt.show()


def submit_expense():
    """
    Submits a new expense through the interface.
    """
    try:
        amount = float(amount_entry.get())
        category = category_entry.get()
        comment = comment_entry.get()

        if not category:
            messagebox.showerror("Ошибка", "Введите категорию.")
            return

        add_expense(amount, category, comment)
        messagebox.showinfo("Успех", "Расход добавлен.")
        refresh_expenses()
    except ValueError:
        messagebox.showerror("Ошибка", "Введите корректную сумму.")


def refresh_expenses():
    """
    Refreshes the list of expenses in the interface.
    """
    for row in expense_tree.get_children():
        expense_tree.delete(row)

    expenses = get_expenses()
    for expense in expenses:
        expense_tree.insert("", "end", values=(expense[0], expense[1], expense[2], expense[3], expense[4]))


def create_interface():
    """
    Creates the graphical user interface for managing expenses.
    """
    root = tk.Tk()
    root.title("Учёт расходов")
    root.geometry("600x400")

    # Frame for input data
    input_frame = ttk.Frame(root, padding="10")
    input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

    # Input fields
    ttk.Label(input_frame, text="Сумма:").grid(row=0, column=0, sticky="w")
    global amount_entry
    amount_entry = ttk.Entry(input_frame)
    amount_entry.grid(row=0, column=1, sticky="ew")

    ttk.Label(input_frame, text="Категория:").grid(row=1, column=0, sticky="w")
    global category_entry
    category_entry = ttk.Entry(input_frame)
    category_entry.grid(row=1, column=1, sticky="ew")

    ttk.Label(input_frame, text="Комментарий:").grid(row=2, column=0, sticky="w")
    global comment_entry
    comment_entry = ttk.Entry(input_frame)
    comment_entry.grid(row=2, column=1, sticky="ew")

    # Button to add expense
    add_button = ttk.Button(input_frame, text="Добавить расход", command=submit_expense)
    add_button.grid(row=3, column=0, columnspan=2, pady=5)

    # Frame for expense table
    table_frame = ttk.Frame(root, padding="10")
    table_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    # Expense table
    global expense_tree
    expense_tree = ttk.Treeview(table_frame, columns=("ID", "Amount", "Category", "Date", "Comment"), show="headings")
    expense_tree.heading("ID", text="ID")
    expense_tree.heading("Amount", text="Сумма")
    expense_tree.heading("Category", text="Категория")
    expense_tree.heading("Date", text="Дата")
    expense_tree.heading("Comment", text="Комментарий")

    expense_tree.column("ID", width=30)
    expense_tree.column("Amount", width=100)
    expense_tree.column("Category", width=150)
    expense_tree.column("Date", width=100)
    expense_tree.column("Comment", width=150)

    expense_tree.pack(fill="both", expand=True)

    # Button to plot expenses
    plot_button = ttk.Button(root, text="Построить график расходов", command=plot_expenses)
    plot_button.grid(row=2, column=0, padx=10, pady=5)

    # Refresh expense table
    refresh_expenses()

    # Configure layout flexibility
    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(0, weight=1)

    root.mainloop()


# Initialize database and start interface
if __name__ == "__main__":
    init_db()
    create_interface()
