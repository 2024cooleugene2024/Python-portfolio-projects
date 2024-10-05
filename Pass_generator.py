import tkinter as tk
from tkinter import messagebox, filedialog
import secrets
import string


class PasswordGenerator:
    """
    A GUI-based password generator application using Tkinter.

    Methods:
        __init__(self, master):
            Initializes the main window and its components.
        generate_password(self):
            Generates a random password based on user preferences.
        show_password_window(self, password):
            Displays the generated password in a new window.
        copy_to_clipboard(self):
            Copies the generated password to the clipboard.
        save_password(self):
            Saves the generated password to a text file.
    """

    def __init__(self, master):
        self.master = master
        master.title("Password Generator")
        master.geometry("600x400")
        master.resizable(False, False)

        self.length_label = tk.Label(master, text="Password Length:")
        self.length_label.pack()

        self.length_var = tk.IntVar(value=20)
        self.length_scale = tk.Scale(master, from_=12, to=64, orient=tk.HORIZONTAL, variable=self.length_var)
        self.length_scale.pack()

        self.include_upper = tk.BooleanVar(value=True)
        self.include_upper_checkbox = tk.Checkbutton(master, text="Include uppercase letters",
                                                     variable=self.include_upper)
        self.include_upper_checkbox.pack()

        self.include_digits = tk.BooleanVar(value=True)
        self.include_digits_checkbox = tk.Checkbutton(master, text="Include digits", variable=self.include_digits)
        self.include_digits_checkbox.pack()

        self.include_special = tk.BooleanVar(value=True)
        self.include_special_checkbox = tk.Checkbutton(master, text="Include special characters",
                                                       variable=self.include_special)
        self.include_special_checkbox.pack()

        self.include_extended = tk.BooleanVar(value=True)
        self.include_extended_checkbox = tk.Checkbutton(master, text="Include extended ASCII characters",
                                                        variable=self.include_extended)
        self.include_extended_checkbox.pack()

        self.generate_button = tk.Button(master, text="Generate Password", command=self.generate_password)
        self.generate_button.pack()

        self.password_label = tk.Label(master, text="", wraplength=550, font=("Courier", 12))
        self.password_label.pack()

        self.copy_button = tk.Button(master, text="Copy to Clipboard", command=self.copy_to_clipboard)
        self.copy_button.pack()

        self.save_button = tk.Button(master, text="Save Password", command=self.save_password)
        self.save_button.pack()

    def generate_password(self):
        length = self.length_var.get()
        characters = set(string.ascii_lowercase)

        if self.include_upper.get():
            characters.update(string.ascii_uppercase)
        if self.include_digits.get():
            characters.update(string.digits)
        if self.include_special.get():
            characters.update(string.punctuation)
        if self.include_extended.get():
            extended_chars = {chr(i) for i in range(32, 127)}
            characters.update(extended_chars - characters)  # Уникальное множество символов

        characters = ''.join(characters)
        password = ''.join(secrets.choice(characters) for _ in range(length))
        self.password_label.config(text=password)
        self.show_password_window(password)

    def show_password_window(self, password):
        for widget in self.master.winfo_children():
            if isinstance(widget, tk.Toplevel):
                widget.destroy()

        password_window = tk.Toplevel(self.master)
        password_window.title("Generated Password")
        password_window.geometry("600x200")
        password_window.resizable(False, False)

        password_display = tk.Label(password_window, text=password, font=("Courier", 14), wraplength=550)
        password_display.pack(pady=20)

    def copy_to_clipboard(self):
        password = self.password_label.cget("text")
        if not password:
            messagebox.showwarning("Warning", "No password to copy")
            return

        try:
            self.master.clipboard_clear()
            self.master.clipboard_append(password)
            messagebox.showinfo("Success", "Password copied to clipboard")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy password: {str(e)}")

    def save_password(self):
        password = self.password_label.cget("text")
        if not password:
            messagebox.showwarning("Warning", "Generate a password first")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            try:
                with open(file_path, 'a') as file:
                    file.write(password + '\n')
                messagebox.showinfo("Success", "Password saved")
            except IOError as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordGenerator(root)
    root.mainloop()