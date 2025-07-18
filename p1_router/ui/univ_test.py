import tkinter as tk
from tkinter import messagebox
from tkinter.colorchooser import askcolor
from config.config_loader import load_universe_config


class UniverseCanvas(tk.Canvas):
    def __init__(self, master, universes, update_callback):
        super().__init__(master, bg="white", scrollregion=(0, 0, 1000, 1000))
        self.universes = universes
        self.update_callback = update_callback
        self.universe_rects = {}
        self.selected_color = {"r": 0, "g": 0, "b": 0, "w": 0}

        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<Button-1>", self.on_click)

        self.draw_universes()

    def draw_universes(self):
        size = 40
        padding = 10
        cols = 10

        universe_ids = sorted(self.universes.keys())
        for i, universe_id in enumerate(universe_ids):
            row = i // cols
            col = i % cols
            x1 = col * (size + padding)
            y1 = row * (size + padding)
            x2 = x1 + size
            y2 = y1 + size
            label = self.create_rectangle(x1, y1, x2, y2, fill="#000000", tags=(f"universe_{universe_id}"))
            self.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=str(universe_id), fill="white")
            self.universe_rects[label] = universe_id

    def on_click(self, event):
        self.apply_color(event.x, event.y)

    def on_drag(self, event):
        self.apply_color(event.x, event.y)

    def apply_color(self, x, y):
        item = self.find_closest(x, y)
        if item and item[0] in self.universe_rects:
            universe_id = self.universe_rects[item[0]]
            self.itemconfig(item[0], fill=self.rgb_to_hex(self.selected_color))
            self.update_callback(universe_id, self.selected_color.copy())

    def set_selected_color(self, rgb):
        self.selected_color = {"r": int(rgb[0]), "g": int(rgb[1]), "b": int(rgb[2]), "w": 0}

    def rgb_to_hex(self, color):
        return f'#{color["r"]:02x}{color["g"]:02x}{color["b"]:02x}'


class TestUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ArtNet Test UI")
        self.geometry("1000x700")

        self.entity_colors_by_universe = {}
        self.universes = load_universe_config("config/config.json")

        self.color_button = tk.Button(self, text="Select Color", command=self.choose_color)
        self.color_button.pack()

        self.send_button = tk.Button(self, text="Send", command=self.send_messages)
        self.send_button.pack()

        self.scroll_frame = tk.Frame(self)
        self.scroll_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = UniverseCanvas(self.scroll_frame, self.universes, self.update_universe_color)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.scroll_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(yscrollcommand=self.scrollbar.set)

    def choose_color(self):
        rgb, _ = askcolor()
        if rgb:
            self.canvas.set_selected_color(rgb)

    def update_universe_color(self, universe_id, color):
        self.entity_colors_by_universe[universe_id] = color

    def send_messages(self):
        for universe_id, universe in self.universes.items():
            universe.entities_states.clear()
            if universe_id in self.entity_colors_by_universe:
                color = self.entity_colors_by_universe[universe_id]
                for entity_id in universe.entity_ids:
                    universe.update_entity_state(entity_id, color)

        for universe in self.universes.values():
            if universe.entities_states:
                universe.send_message()


if __name__ == "__main__":
    app = TestUI()
    app.mainloop()
