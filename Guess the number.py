import random
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import pygame  # для звуковых эффектов

# Инициализация звуков
pygame.mixer.init()
WIN_SOUND = pygame.mixer.Sound("win.wav")
LOSE_SOUND = pygame.mixer.Sound("lose.wav")


def play_sound(result):
    if result == "win":
        WIN_SOUND.play()
    elif result == "lose":
        LOSE_SOUND.play()


class GuessNumberGame:
    """
        Class-based implementation of a "Guess the Number" game with selectable difficulty levels, scoring,
        and a countdown timer.

        Attributes:
        EASY, MEDIUM, HARD: Difficulty levels represented as string constants.
        root_: The Tkinter root_ window.
        score: The current game score.
        secret_number: The randomly chosen number that the player needs to guess.
        max_number: The maximum number for the selected difficulty level.
        time_limit: The time limit for the selected difficulty level.
        remaining_time: The remaining time in the game countdown.
        timer_running: Boolean flag indicating if the timer is running.

        Methods:
        __init__(self, root_):
            Initializes the game with a given Tkinter root_ window and sets initial values.

        create_widgets(self):
            Creates and initializes the game widgets.

        create_difficulty_selector(self):
            Creates the difficulty level dropdown selector widget.

        create_entry_field(self):
            Creates the input field for the player to enter their guess.

        create_start_button(self):
            Creates the start button to begin the game.

        create_timer_label(self):
            Creates the label to display the remaining time.

        create_score_label(self):
            Creates the label to display the current score.

        create_check_button(self):
            Creates the check button to submit the player's guess.

        start_game(self):
            Resets values, updates difficulty settings, generates a new secret number, and starts the game timer.

        reset_values(self):
            Resets game values to initial states.

        update_difficulty(self):
            Updates game settings based on the selected difficulty level.

        generate_secret_number(self):
            Generates a random number for the player to guess.

        check_number(self):
            Checks the player's guess against the secret number and updates the score and game state accordingly.

        update_score(self):
            Updates the score label with the current score.

        update_timer_label(self):
            Updates the timer label with the remaining time.

        start_timer(self):
            Starts the countdown timer and updates it every second.

        end_game(self):
            Ends the game when time runs out, disables relevant buttons, and shows the secret number in a message box.

        play_sound(self, result):
            Plays a sound based on the result (win or lose).
    """
    EASY, MEDIUM, HARD = "Легкий (1-10)", "Средний (1-100)", "Сложный (1-1000)"

    def __init__(self, root_):
        self.check_button = None
        self.score_label = None
        self.timer_label = None
        self.start_button = None
        self.number_entry = None
        self.entry_label = None
        self.difficulty = None
        self.root = None
        self.difficulty_combobox = ttk.Combobox(self.root, textvariable=self.difficulty,
                                                values=[self.EASY, self.MEDIUM, self.HARD], state="readonly")
        self.difficulty = tk.StringVar()
        self.level_label = None
        self.style = None
        self.root = root_
        self.root.title("Угадай число")
        self.score = 0
        self.secret_number = None
        self.max_number = 100
        self.time_limit = 10
        self.remaining_time = self.time_limit
        self.timer_running = False
        self.create_widgets()

    def create_widgets(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.create_difficulty_selector()
        self.create_entry_field()
        self.create_start_button()
        self.create_timer_label()
        self.create_score_label()
        self.create_check_button()

    def create_difficulty_selector(self):
        self.level_label = ttk.Label(self.root, text="Выберите уровень сложности:")
        self.level_label.pack(pady=10)
        self.difficulty_combobox.current(1)
        self.difficulty_combobox.pack(pady=5)

    def create_entry_field(self):
        self.entry_label = ttk.Label(self.root, text="Введите число:")
        self.entry_label.pack(pady=10)
        self.number_entry = ttk.Entry(self.root)
        self.number_entry.pack(pady=5)

    def create_start_button(self):
        self.start_button = ttk.Button(self.root, text="Начать игру", command=self.start_game)
        self.start_button.pack(pady=10)

    def create_timer_label(self):
        self.timer_label = ttk.Label(self.root, text="Время: 10 секунд")
        self.timer_label.pack(pady=10)

    def create_score_label(self):
        self.score_label = ttk.Label(self.root, text=f"Очки: {self.score}")
        self.score_label.pack(pady=10)

    def create_check_button(self):
        self.check_button = ttk.Button(self.root, text="Проверить", command=self.check_number, state=tk.DISABLED)
        self.check_button.pack(pady=10)

    def start_game(self):
        self.reset_values()
        self.update_difficulty()
        self.generate_secret_number()
        self.start_timer()
        self.check_button.config(state=tk.NORMAL)
        self.start_button.config(state=tk.DISABLED)

    def reset_values(self):
        self.score = 0
        self.update_score()
        self.remaining_time = self.time_limit
        self.update_timer_label()
        self.timer_running = True

    def update_difficulty(self):
        level = self.difficulty.get()
        if level == self.EASY:
            self.max_number = 10
            self.time_limit = 15
        elif level == self.MEDIUM:
            self.max_number = 100
            self.time_limit = 10
        elif level == self.HARD:
            self.max_number = 1000
            self.time_limit = 7
        self.remaining_time = self.time_limit

    def generate_secret_number(self):
        self.secret_number = random.randint(1, self.max_number)

    def check_number(self):
        try:
            guess = int(self.number_entry.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите правильное число!")
            return
        if guess == self.secret_number:
            self.score += 1
            self.update_score()
            play_sound("win")
            messagebox.showinfo("Победа", "Вы угадали число!")
            self.generate_secret_number()
        else:
            messagebox.showinfo("Неправильно", "Неправильное число! Попробуйте снова.")

    def update_score(self):
        self.score_label.config(text=f"Очки: {self.score}")

    def update_timer_label(self):
        self.timer_label.config(text=f"Время: {self.remaining_time} секунд")

    def start_timer(self):
        if self.timer_running:
            if self.remaining_time > 0:
                self.remaining_time -= 1
                self.update_timer_label()
                self.root.after(1000, self.start_timer)
            else:
                self.end_game()

    def end_game(self):
        self.timer_running = False
        self.check_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)
        play_sound("lose")
        messagebox.showinfo("Время вышло", f"Вы не успели! Загаданное число было {self.secret_number}")


if __name__ == "__main__":
    root = tk.Tk()
    game = GuessNumberGame(root)
    root.mainloop()


