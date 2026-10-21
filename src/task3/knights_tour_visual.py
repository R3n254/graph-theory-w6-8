import tkinter as tk
from tkinter import messagebox

from knights_tour import knights_tour  # must be in the same folder

LIGHT = "#f0d9b5"
DARK = "#b58863"
VISITED = "#a8d5a2"
CURRENT = "#ffb347"
PATH_COLOR = "#2a5db0"


class TourApp:
    def __init__(self, root, cols, rows, path):
        self.root = root
        self.cols, self.rows, self.path = cols, rows, path
        self.cell = max(30, min(90, 700 // max(cols, rows)))
        self.delay = 500
        self.index = 0
        self.paused = False
        self.job = None
        self.rects = {}

        root.title("Knight's Tour Visualizer")
        self.canvas = tk.Canvas(root, width=cols * self.cell, height=rows * self.cell)
        self.canvas.pack(padx=10, pady=10)

        self.status = tk.Label(root, text="", font=("Arial", 12))
        self.status.pack()

        bar = tk.Frame(root)
        bar.pack(pady=8)
        self.pause_btn = tk.Button(bar, text="Pause", width=10, command=self.toggle_pause)
        self.pause_btn.grid(row=0, column=0, padx=4)
        tk.Button(bar, text="Restart", width=10, command=self.restart).grid(row=0, column=1, padx=4)
        tk.Button(bar, text="Show all", width=10, command=self.show_all).grid(row=0, column=2, padx=4)

        speed = tk.Scale(root, from_=50, to=1000, orient="horizontal", length=250,
                         label="Delay between moves (ms)", command=self.set_delay)
        speed.set(self.delay)
        speed.pack(pady=(0, 10))

        self.draw_board()
        self.step()

    # ---------- drawing ----------
    def center(self, x, y):
        return x * self.cell + self.cell / 2, y * self.cell + self.cell / 2

    def draw_board(self):
        self.canvas.delete("all")
        self.rects.clear()
        c = self.cell
        for x in range(self.cols):
            for y in range(self.rows):
                color = LIGHT if (x + y) % 2 == 0 else DARK
                self.rects[(x, y)] = self.canvas.create_rectangle(
                    x * c, y * c, (x + 1) * c, (y + 1) * c, fill=color, outline="")
                self.canvas.create_text(x * c + 3, y * c + 2, anchor="nw",
                                        text=f"{x},{y}", font=("Arial", max(6, c // 8)),
                                        fill="#555555")

    def draw_move(self, i):
        x, y = self.path[i]
        c = self.cell

        # previous square becomes "visited", and a line is drawn to the new one
        if i > 0:
            px, py = self.path[i - 1]
            self.canvas.itemconfig(self.rects[(px, py)], fill=VISITED)
            x1, y1 = self.center(px, py)
            x2, y2 = self.center(x, y)
            self.canvas.create_line(x1, y1, x2, y2, fill=PATH_COLOR, width=2,
                                    arrow=tk.LAST, tags="path")

        self.canvas.itemconfig(self.rects[(x, y)], fill=CURRENT)

        # move number in the square
        cx, cy = self.center(x, y)
        self.canvas.create_text(cx, cy + c * 0.28, text=str(i + 1),
                                font=("Arial", max(8, c // 5), "bold"), fill="black")

        # knight marker
        self.canvas.delete("knight")
        self.canvas.create_text(cx, cy - c * 0.1, text="\u265E",
                                font=("Segoe UI Symbol", int(c * 0.45)),
                                fill="black", tags="knight")

        self.canvas.tag_raise("path")
        self.canvas.tag_raise("knight")
        self.status.config(text=f"Move {i + 1} / {len(self.path)}   at ({x},{y})")

    # ---------- animation ----------
    def step(self):
        if self.index < len(self.path):
            self.draw_move(self.index)
            self.index += 1
            if not self.paused:
                self.job = self.root.after(self.delay, self.step)
        else:
            self.status.config(text=f"Done! All {len(self.path)} squares visited.")
            self.pause_btn.config(text="Pause")

    def cancel_job(self):
        if self.job is not None:
            self.root.after_cancel(self.job)
            self.job = None

    def toggle_pause(self):
        if self.index >= len(self.path):
            return
        self.paused = not self.paused
        self.pause_btn.config(text="Resume" if self.paused else "Pause")
        if not self.paused:
            self.step()
        else:
            self.cancel_job()

    def restart(self):
        self.cancel_job()
        self.draw_board()
        self.index = 0
        self.paused = False
        self.pause_btn.config(text="Pause")
        self.step()

    def show_all(self):
        self.cancel_job()
        while self.index < len(self.path):
            self.draw_move(self.index)
            self.index += 1
        self.status.config(text=f"Done! All {len(self.path)} squares visited.")

    def set_delay(self, value):
        self.delay = int(value)


def main():
    cols, rows = map(int, input("Columns and rows (e.g. 5 5): ").split())
    start_x, start_y = map(int, input("Start position (e.g. 2 2): ").split())

    path = knights_tour(cols, rows, start_x, start_y)
    if path is None:
        print("path not found")
        return

    root = tk.Tk()
    TourApp(root, cols, rows, path)
    root.mainloop()


if __name__ == "__main__":
    main()
