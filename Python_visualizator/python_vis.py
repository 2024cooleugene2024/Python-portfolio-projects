import math
import tkinter as tk
from tkinter import messagebox
import traceback


class CodeVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Code Visualizer")

        self.code_text = tk.Text(root, height=15, width=60)
        self.code_text.grid(row=0, column=0, padx=10, pady=10)

        self.run_button = tk.Button(root, text="Run", command=self.run_code)
        self.run_button.grid(row=1, column=0)

        self.step_forward_button = tk.Button(root, text="Step Forward", command=self.step_forward)
        self.step_forward_button.grid(row=1, column=1)

        self.step_back_button = tk.Button(root, text="Step Back", command=self.step_back)
        self.step_back_button.grid(row=1, column=2)

        self.modify_button = tk.Button(root, text="Modify & Restart", command=self.modify_code)
        self.modify_button.grid(row=1, column=3)

        self.output_text = tk.Text(root, height=10, width=60, bg="light gray")
        self.output_text.grid(row=2, column=0, padx=10, pady=10)

        self.canvas = tk.Canvas(root, height=200, width=600, bg="white")
        self.canvas.grid(row=3, column=0, padx=10, pady=10)

        self.current_line = 0
        self.code_lines = []
        self.globals_dict = {}  # Хранение глобальных переменных во время выполнения
        self.executed_lines = []  # Список исполненных строк

    def highlight_line(self, line_num):
        """Подсветка текущей строки."""
        self.code_text.tag_remove("highlight", "1.0", tk.END)  # Удалить старые подсветки
        self.code_text.tag_add("highlight", f"{line_num}.0", f"{line_num}.end")
        self.code_text.tag_config("highlight", background="yellow")
        self.root.update()  # Обновить интерфейс, чтобы подсветка применялась мгновенно

    def run_code(self):
        """Инициализация кода и подготовка для шаговой отладки."""
        code = self.code_text.get("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.canvas.delete("all")  # Очистить предыдущие визуализации

        # Разделение кода по строкам для пошаговой подсветки
        self.code_lines = code.splitlines()
        self.current_line = 0
        self.executed_lines = []  # Очистить список исполненных строк
        self.globals_dict = {}  # Перезапуск глобальных переменных

    def step_forward(self):
        """Шаг вперед: выполнение одной строки кода."""
        if self.current_line < len(self.code_lines):
            line = self.code_lines[self.current_line]
            try:
                exec(line, self.globals_dict)
                self.executed_lines.append(line)  # Добавить выполненную строку в список
                self.highlight_line(self.current_line + 1)
                self.current_line += 1
            except Exception as e:
                error_msg = traceback.format_exc()
                self.output_text.insert(tk.END, f"Ошибка:\n{error_msg}")
        else:
            self.output_text.insert(tk.END, "Программа завершена.\n")

        # Визуализировать объекты после выполнения шага
        self.visualize_globals()

    def step_back(self):
        """Шаг назад: отмена последней выполненной строки."""
        if self.current_line > 0:
            self.current_line -= 1
            self.executed_lines.pop()  # Удалить последнюю выполненную строку
            self.globals_dict = {}  # Перезапустить все переменные
            # Выполнить весь код до текущей строки
            for i, line in enumerate(self.executed_lines):
                exec(line, self.globals_dict)
            self.highlight_line(self.current_line + 1)
        else:
            self.output_text.insert(tk.END, "Нельзя откатить дальше начала программы.\n")

        # Обновить визуализацию объектов
        self.canvas.delete("all")
        self.visualize_globals()

    def modify_code(self):
        """Изменение кода в реальном времени и перезапуск с начала."""
        # Перезапуск программы с изменениями
        self.run_code()

    def visualize_globals(self):
        """Визуализация глобальных переменных, включая списки, словари и объекты."""
        self.canvas.delete("all")
        for var_name, var_value in self.globals_dict.items():
            if isinstance(var_value, list):
                self.visualize_list(var_value, var_name)
            elif isinstance(var_value, dict):
                self.visualize_dict(var_value, var_name)
            elif hasattr(var_value, '__dict__'):
                self.visualize_object(var_value, var_name)

    def visualize_list(self, lst, name):
        """Визуализация списка."""
        width = 50  # Ширина каждого столбца
        max_height = 200  # Высота холста
        max_value = max(lst) if lst else 1  # Защита от деления на ноль

        for i, value in enumerate(lst):
            # Рассчитать высоту столбца
            height = (value / max_value) * max_height
            x0 = i * width
            y0 = max_height - height
            x1 = (i + 1) * width
            y1 = max_height

            # Нарисовать прямоугольник (столбец)
            self.canvas.create_rectangle(x0, y0, x1, y1, fill="blue")
            # Подписать значения
            self.canvas.create_text(x0 + width / 2, y0 - 10, text=str(value), fill="black")

    def visualize_dict(self, dct, name):
        """Визуализация словаря."""
        y = 10
        for key, value in dct.items():
            self.canvas.create_text(10, y, anchor="w", text=f"{key}: {value}", fill="green")
            y += 20

    def visualize_object(self, obj, name):
        """Визуализация объектов классов."""
        y = 10
        self.canvas.create_text(10, y, anchor="w", text=f"Object: {name} ({obj.__class__.__name__})", fill="purple")
        y += 20
        for attr, value in obj.__dict__.items():
            self.canvas.create_text(10, y, anchor="w", text=f"{attr}: {value}", fill="purple")
            y += 20

    def visualize_tree(self, root_node):
        """Визуализация дерева с корнем root_node."""
        self.canvas.delete("all")
        self._draw_tree_node(root_node, 300, 20, 200)

    def _draw_tree_node(self, node, x, y, offset):
        """Рекурсивное рисование узла дерева."""
        if node:
            self.canvas.create_text(x, y, text=str(node.value), fill="blue")
            if node.left:
                self.canvas.create_line(x, y, x - offset, y + 50)
                self._draw_tree_node(node.left, x - offset, y + 50, offset // 2)
            if node.right:
                self.canvas.create_line(x, y, x + offset, y + 50)
                self._draw_tree_node(node.right, x + offset, y + 50, offset // 2)

    def visualize_graph(self, graph):
        """Визуализация графа."""
        self.canvas.delete("all")
        nodes = list(graph.keys())
        radius = 20
        positions = {}
        # Разместить узлы на круге
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / len(nodes)
            x = 300 + 200 * math.cos(angle)
            y = 200 + 200 * math.sin(angle)
            positions[node] = (x, y)
            self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="lightblue")
            self.canvas.create_text(x, y, text=str(node), fill="black")

        # Нарисовать ребра
        for node, edges in graph.items():
            x1, y1 = positions[node]
            for edge in edges:
                x2, y2 = positions[edge]
                self.canvas.create_line(x1, y1, x2, y2)


if __name__ == "__main__":
    root = tk.Tk()
    app = CodeVisualizer(root)
    root.mainloop()
