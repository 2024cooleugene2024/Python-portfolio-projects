import sqlite3
import os

# Database initialization
def init_db():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            deadline TEXT,
            category TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database when the app starts
init_db()

import tkinter as tk
from tkinter import ttk, messagebox
import datetime

class ToDoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("To-Do List")

        # Setting up the main interface
        self.setup_ui()

        # Load tasks from the database
        self.load_tasks()

    def setup_ui(self):
        # Main Frame
        self.frame = ttk.Frame(self.root, padding="10")
        self.frame.grid(row=0, column=0, sticky="nsew")

        # Entry for task title
        self.title_label = ttk.Label(self.frame, text="Task Title:")
        self.title_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.title_entry = ttk.Entry(self.frame, width=30)
        self.title_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Task description
        self.desc_label = ttk.Label(self.frame, text="Description:")
        self.desc_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.desc_entry = ttk.Entry(self.frame, width=30)
        self.desc_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Task deadline
        self.deadline_label = ttk.Label(self.frame, text="Deadline (YYYY-MM-DD):")
        self.deadline_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.deadline_entry = ttk.Entry(self.frame, width=30)
        self.deadline_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Task category
        self.category_label = ttk.Label(self.frame, text="Category:")
        self.category_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.category_entry = ttk.Entry(self.frame, width=30)
        self.category_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Add Task button
        self.add_button = ttk.Button(self.frame, text="Add Task", command=self.add_task)
        self.add_button.grid(row=4, column=0, columnspan=2, pady=10)

        # Task List
        self.tree = ttk.Treeview(self.frame, columns=("ID", "Title", "Description", "Deadline", "Category", "Status"), show='headings')
        self.tree.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Description", text="Description")
        self.tree.heading("Deadline", text="Deadline")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Status", text="Status")

        # Scrollbar for the task list
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=self.scrollbar.set)
        self.scrollbar.grid(row=5, column=2, sticky="ns")

    def add_task(self):
        # Collect task details from the entries
        title = self.title_entry.get()
        description = self.desc_entry.get()
        deadline = self.deadline_entry.get()
        category = self.category_entry.get()

        # Insert into database
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (title, description, deadline, category, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, description, deadline, category, "in progress"))
        conn.commit()
        conn.close()

        # Clear entry fields
        self.title_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.deadline_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)

        # Reload task list
        self.load_tasks()

    def load_tasks(self):
        # Clear the current tasks
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Fetch from database and display in treeview
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks")
        rows = cursor.fetchall()
        for row in rows:
            self.tree.insert("", tk.END, values=row)
        conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = ToDoApp(root)
    root.mainloop()
