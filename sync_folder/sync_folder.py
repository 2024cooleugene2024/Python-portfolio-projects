import os
import shutil
import customtkinter as ctk
from tkinter import filedialog, messagebox
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

ctk.set_appearance_mode("System")  # Внешний вид: 'System', 'Light' или 'Dark'
ctk.set_default_color_theme("blue")  # Цветовая тема: 'blue', 'green' или 'dark-blue'

class SyncHandler(FileSystemEventHandler):
    """Handles file system events to synchronize folders and backup deleted files."""

    def __init__(self, source_folder, target_folder, backup_folder, log_callback):
        self.source_folder = source_folder
        self.target_folder = target_folder
        self.backup_folder = backup_folder
        self.log_callback = log_callback

    def on_modified(self, event):
        """Triggered when a file is modified; sync folders."""
        self.sync_folders()

    def on_created(self, event):
        """Triggered when a file is created; sync folders."""
        self.sync_folders()

    def on_deleted(self, event):
        """Triggered when a file is deleted; back up the deleted file."""
        self.backup_deleted_file(event.src_path)

    def sync_folders(self):
        """Synchronize the source and target folders."""
        # Copy the contents of the source folder to the target folder
        if os.path.exists(self.source_folder):
            for root, dirs, files in os.walk(self.source_folder):
                relative_path = os.path.relpath(root, self.source_folder)
                target_dir = os.path.join(self.target_folder, relative_path)
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)

                # Copy each file to the target directory
                for file in files:
                    source_file = os.path.join(root, file)
                    target_file = os.path.join(target_dir, file)
                    shutil.copy2(source_file, target_file)
                    self.log_callback(f"Copied: {source_file} -> {target_file}")

    def backup_deleted_file(self, file_path):
        """Back up a deleted file or directory by moving it to the backup folder."""
        if not os.path.exists(self.backup_folder):
            os.makedirs(self.backup_folder)

        file_name = os.path.basename(file_path)
        backup_file_path = os.path.join(self.backup_folder, file_name)

        if os.path.exists(file_path):
            shutil.move(file_path, backup_file_path)
            self.log_callback(f"File backed up: {file_path} -> {backup_file_path}")
        elif os.path.isdir(file_path):
            backup_dir_path = os.path.join(self.backup_folder, file_name)
            shutil.move(file_path, backup_dir_path)
            self.log_callback(f"Directory backed up: {file_path} -> {backup_dir_path}")


class App(ctk.CTk):
    """Main application class for the folder synchronization GUI."""

    def __init__(self):
        super().__init__()

        self.title("Folder Synchronization")
        self.geometry("500x500")

        self.source_folder = ""
        self.target_folder = ""
        self.backup_folder = ""
        self.observer = None
        self.is_syncing = False

        # Create and pack GUI elements
        self.label = ctk.CTkLabel(self, text="Select folders to synchronize:", font=("Arial", 16))
        self.label.pack(pady=10)

        self.source_button = ctk.CTkButton(self, text="Select Source Folder", command=self.select_source_folder)
        self.source_button.pack(pady=5)

        self.target_button = ctk.CTkButton(self, text="Select Target Folder", command=self.select_target_folder)
        self.target_button.pack(pady=5)

        self.backup_button = ctk.CTkButton(self, text="Select Backup Folder", command=self.select_backup_folder)
        self.backup_button.pack(pady=5)

        self.start_button = ctk.CTkButton(self, text="Start Synchronization", command=self.start_sync)
        self.start_button.pack(pady=20)

        self.stop_button = ctk.CTkButton(self, text="Stop Synchronization", command=self.stop_sync, state="disabled")
        self.stop_button.pack(pady=5)

        # Textbox to show selected folders
        self.folder_display = ctk.CTkTextbox(self, width=400, height=80)
        self.folder_display.pack(pady=10)

        # Textbox for synchronization log
        self.log_display = ctk.CTkTextbox(self, width=400, height=150)
        self.log_display.pack(pady=10)

        self.status_label = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.status_label.pack(pady=10)

    def update_folder_display(self):
        """Update the textbox to show the selected folders."""
        folders_info = (
            f"Source Folder: {self.source_folder}\n"
            f"Target Folder: {self.target_folder}\n"
            f"Backup Folder: {self.backup_folder}"
        )
        self.folder_display.delete(1.0, "end")
        self.folder_display.insert("end", folders_info)

    def log_callback(self, message):
        """Callback to update the log display."""
        self.log_display.insert("end", message + "\n")
        self.log_display.see("end")

    def select_source_folder(self):
        """Open a dialog to select the source folder."""
        self.source_folder = filedialog.askdirectory()
        self.update_folder_display()

    def select_target_folder(self):
        """Open a dialog to select the target folder."""
        self.target_folder = filedialog.askdirectory()
        self.update_folder_display()

    def select_backup_folder(self):
        """Open a dialog to select the backup folder."""
        self.backup_folder = filedialog.askdirectory()
        self.update_folder_display()

    def start_sync(self):
        """Start monitoring the source folder for changes."""
        if not self.source_folder or not self.target_folder:
            messagebox.showerror("Error", "Please select both source and target folders.")
            return

        self.is_syncing = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.log_display.delete(1.0, "end")

        event_handler = SyncHandler(self.source_folder, self.target_folder, self.backup_folder, self.log_callback)
        self.observer = Observer()
        self.observer.schedule(event_handler, self.source_folder, recursive=True)
        threading.Thread(target=self.run_observer, daemon=True).start()

        self.status_label.configure(text="Monitoring changes...")

    def run_observer(self):
        """Run the observer in a separate thread."""
        self.observer.start()
        try:
            while self.is_syncing:
                self.update()
        except KeyboardInterrupt:
            self.observer.stop()

    def stop_sync(self):
        """Stop the folder synchronization."""
        if self.observer:
            self.observer.stop()
            self.observer.join()

        self.is_syncing = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_label.configure(text="Stopped monitoring.")

# Run the application
if __name__ == "__main__":
    app = App()
    app.mainloop()
