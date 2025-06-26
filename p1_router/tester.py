import tkinter as tk
from tkinter.colorchooser import askcolor
from config.config_loader import load_universe_config


class EntityCanvas(tk.Canvas):
    def __init__(self, master, universes, update_callback, width, height):
        super().__init__(master, bg="white", width=width, height=height)
        self.universes = universes
        self.update_callback = update_callback
        self.selected_color = {"r": 0, "g": 0, "b": 0, "w": 0}
        self.entity_rects = {}

        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<Button-1>", self.on_click)

        self.draw_all_entities()

    def draw_all_entities(self):
        size = 8    
        padding = 1
        col_width = size + padding
        row_height = size + padding

        all_entities = sorted([
            entity_id
            for universe_id in sorted(self.universes.keys())
            for entity_id in (self.universes[universe_id].entity_ids)
        ])
        
        x = 0
        y_direction = -1  
        start_row = 128 
        entity_idx = 0

        while entity_idx < len(all_entities):
            height = 129 if x % 2 == 0 else 128
            y_direction = -1 if x % 2 == 0 else 1

            for i in range(height):
                if entity_idx >= len(all_entities):
                    break

                row = start_row - i if y_direction == -1 else i
                col = x

                x1 = col * col_width
                y1 = row * row_height
                x2 = x1 + size
                y2 = y1 + size

                entity_id = all_entities[entity_idx]
                rect = self.create_rectangle(x1, y1, x2, y2, fill="#000000", tags=(f"entity_{entity_id}"))
                self.entity_rects[rect] = entity_id
                entity_idx += 1
            entity_idx +=1
            x += 1

    def set_all_to_black(self):
        for rect in self.entity_rects.keys():
            self.itemconfig(rect, fill="#000000")
            entity_id = self.entity_rects[rect]
            self.update_callback(entity_id, {"r": 0, "g": 0, "b": 0, "w": 0})

    def on_click(self, event):
        self.apply_color(event.x, event.y)

    def on_drag(self, event):
        self.apply_color(event.x, event.y)

    def apply_color(self, x, y):
        item = self.find_closest(x, y)
        if item and item[0] in self.entity_rects:
            entity_id = self.entity_rects[item[0]]
            self.itemconfig(item[0], fill=self.rgb_to_hex(self.selected_color))
            self.update_callback(entity_id, self.selected_color.copy())

    def set_selected_color(self, rgb):
        self.selected_color = {"r": int(rgb[0]), "g": int(rgb[1]), "b": int(rgb[2]), "w": 0}

    def rgb_to_hex(self, color):
        return f'#{color["r"]:02x}{color["g"]:02x}{color["b"]:02x}'


class TestUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ArtNet Test UI")
        self.attributes('-fullscreen', True)

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight() - 100  # Leave space for buttons

        self.entity_colors = {}
        self.universes = load_universe_config("config/config.json")

        self.color_button = tk.Button(self, text="Select Color", command=self.choose_color)
        self.color_button.pack()

        self.send_button = tk.Button(self, text="Send", command=self.send_messages)
        self.send_button.pack()

        self.blackout_button = tk.Button(self, text="Set All to Black", command=self.set_all_black)
        self.blackout_button.pack()

        self.canvas = EntityCanvas(self, self.universes, self.update_entity_color, screen_width, screen_height)
        self.canvas.pack()

        # Optional: Esc key to close fullscreen
        self.bind("<Escape>", lambda e: self.destroy())

    def choose_color(self):
        rgb, _ = askcolor()
        if rgb:
            self.canvas.set_selected_color(rgb)

    def update_entity_color(self, entity_id, color):
        self.entity_colors[entity_id] = color

    def send_messages(self):
        for universe in self.universes.values():
            universe.entities_states.clear()
            for entity_id in universe.entity_ids:
                if entity_id in self.entity_colors:
                    universe.update_entity_state(entity_id, self.entity_colors[entity_id])

        for universe in self.universes.values():
            if universe.entities_states:
                universe.send_message()

    def set_all_black(self):
        self.canvas.set_all_to_black()
        self.entity_colors = {
            entity_id: {"r": 0, "g": 0, "b": 0, "w": 0}
            for universe in self.universes.values()
            for entity_id in universe.entity_ids
        }


if __name__ == "__main__":
    app = TestUI()
    app.mainloop()
