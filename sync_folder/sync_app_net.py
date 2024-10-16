import os
import shutil
import filecmp
import socket
import threading
import tkinter as tk
from tkinter import filedialog
from tqdm import tqdm
from datetime import datetime

# Network settings
HOST = '127.0.0.1'  # Server IP address (change to the target machine's IP)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)


# Function to check if the source and destination directories exist
def check_directories(src_dir, dst_dir):
    if not os.path.exists(src_dir):
        log_message(f"Source directory '{src_dir}' does not exist.")
        return False
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        log_message(f"Destination directory '{dst_dir}' created.")
    return True


# Function to send a file over the network
def send_file(file_path, dest_ip, dest_port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((dest_ip, dest_port))
            with open(file_path, 'rb') as f:
                s.sendall(f.read())
        log_message(f"Sent '{file_path}' to {dest_ip}:{dest_port}.")
    except Exception as e:
        log_message(f"Error sending '{file_path}': {e}")


# Function to synchronize files between two directories
def sync_directories(src_dir, dst_dir, delete=False):
    log_message("Synchronization started.")
    log_to_file("Synchronization started.")

    files_to_sync = []
    for root, dirs, files in os.walk(src_dir):
        for directory in dirs:
            files_to_sync.append(os.path.join(root, directory))
        for file in files:
            files_to_sync.append(os.path.join(root, file))

    # Create a list of threads for sending files
    threads = []

    with tqdm(total=len(files_to_sync), desc="Syncing files", unit="file") as pbar:
        for source_path in files_to_sync:
            replica_path = os.path.join(dst_dir, os.path.relpath(source_path, src_dir))

            if os.path.isdir(source_path):
                if not os.path.exists(replica_path):
                    os.makedirs(replica_path)
            else:
                if not os.path.exists(replica_path) or not filecmp.cmp(source_path, replica_path, shallow=False):
                    pbar.set_description(f"Processing '{source_path}'")
                    shutil.copy2(source_path, replica_path)  # Local copy

                    # Start a new thread for sending the file
                    thread = threading.Thread(target=send_file, args=(source_path, HOST, PORT))
                    thread.start()
                    threads.append(thread)  # Keep track of the thread

            pbar.update(1)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    if delete:
        files_to_delete = []
        for root, dirs, files in os.walk(dst_dir):
            for directory in dirs:
                files_to_delete.append(os.path.join(root, directory))
            for file in files:
                files_to_delete.append(os.path.join(root, file))

        with tqdm(total=len(files_to_delete), desc="Deleting files", unit="file") as pbar:
            for replica_path in files_to_delete:
                source_path = os.path.join(src_dir, os.path.relpath(replica_path, dst_dir))
                if not os.path.exists(source_path):
                    pbar.set_description(f"Processing '{replica_path}'")
                    if os.path.isdir(replica_path):
                        shutil.rmtree(replica_path)
                    else:
                        os.remove(replica_path)
                pbar.update(1)

    log_message("Synchronization completed.")
    log_to_file("Synchronization completed.")


# Function to start the synchronization process
def start_sync():
    src_dir = src_entry.get()
    dst_dir = dst_entry.get()
    delete = delete_var.get()

    if not check_directories(src_dir, dst_dir):
        return

    sync_directories(src_dir, dst_dir, delete)


# Function to select the source directory
def select_src_dir():
    dir_name = filedialog.askdirectory()
    src_entry.delete(0, tk.END)
    src_entry.insert(0, dir_name)


# Function to select the destination directory
def select_dst_dir():
    dir_name = filedialog.askdirectory()
    dst_entry.delete(0, tk.END)
    dst_entry.insert(0, dir_name)


# Flag to control the synchronization process
running = False


# Function to run synchronization periodically
def periodic_sync():
    global running

    if not running:
        return  # Stop synchronization if running is False

    interval = interval_entry.get()

    try:
        interval_ms = int(float(interval) * 1000)
        if interval_ms < 1000 or interval_ms > 60000:
            raise ValueError
    except ValueError:
        log_message("Invalid synchronization interval.")
        return

    start_sync()

    # Schedule the next synchronization after the given interval
    root.after(interval_ms, periodic_sync)


# Function to start periodic synchronization
def start_periodic_sync():
    global running
    running = True
    periodic_sync()


# Function to stop synchronization
def stop_sync():
    global running
    running = False
    log_message("Synchronization stopped.")
    log_to_file("Synchronization stopped.")


# Function to log messages to the text area and the log file
def log_message(message):
    log_area.insert(tk.END, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    log_area.see(tk.END)  # Scroll to the end of the log


# Function to log messages to a file
def log_to_file(message):
    with open("sync_log.txt", "a") as log_file:
        log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")


# Create the main window
root = tk.Tk()
root.title("Folder Synchronization")

# Create labels and entry fields for the source and destination directories
src_label = tk.Label(root, text="Source Directory:")
src_label.grid(row=0, column=0, padx=10, pady=10)
src_entry = tk.Entry(root, width=50)
src_entry.grid(row=0, column=1, padx=10, pady=10)
src_button = tk.Button(root, text="Browse", command=select_src_dir)
src_button.grid(row=0, column=2, padx=10, pady=10)

dst_label = tk.Label(root, text="Destination Directory:")
dst_label.grid(row=1, column=0, padx=10, pady=10)
dst_entry = tk.Entry(root, width=50)
dst_entry.grid(row=1, column=1, padx=10, pady=10)
dst_button = tk.Button(root, text="Browse", command=select_dst_dir)
dst_button.grid(row=1, column=2, padx=10, pady=10)

# Create checkbox for the delete option
delete_var = tk.BooleanVar()
delete_check = tk.Checkbutton(root, text="Delete extraneous files in destination", variable=delete_var)
delete_check.grid(row=2, columnspan=3, padx=10, pady=10)

# Create an entry for synchronization interval
interval_label = tk.Label(root, text="Synchronization Interval (seconds, 1-60):")
interval_label.grid(row=3, column=0, padx=10, pady=10)
interval_entry = tk.Entry(root, width=10)
interval_entry.grid(row=3, column=1, padx=10, pady=10)
interval_entry.insert(0, "10")  # Default value: 10 seconds

# Create the start and stop buttons
sync_button = tk.Button(root, text="Start Periodic Synchronization", command=start_periodic_sync)
sync_button.grid(row=4, columnspan=3, padx=10, pady=10)

stop_button = tk.Button(root, text="Stop Synchronization", command=stop_sync)
stop_button.grid(row=5, columnspan=3, padx=10, pady=10)

# Create a text area to display log messages
log_area = tk.Text(root, height=10, width=80)
log_area.grid(row=6, columnspan=3, padx=10, pady=10)

# Start the Tkinter main loop
root.mainloop()
