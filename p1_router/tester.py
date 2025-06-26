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
        size = 4
        padding = 1
        col_width = size + padding
        row_height = size + padding

        all_entities = sorted([
            entity_id
            for universe_id in sorted(self.universes.keys())
            for entity_id in (self.universes[universe_id].entity_ids)
        ])

        x = 0
        start_row = 130
        entity_idx = 0

        while entity_idx < len(all_entities):
            height = 130 if x % 2 == 0 else 129
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
        screen_height = self.winfo_screenheight() - 100

        self.entity_colors = {}
        self.universes = load_universe_config("config/config.json")

        self.color_button = tk.Button(self, text="Select Color", command=self.choose_color)
        self.color_button.pack()

        self.send_button = tk.Button(self, text="Send", command=self.send_messages)
        self.send_button.pack()

        self.blackout_button = tk.Button(self, text="Set All to Black", command=self.set_all_black)
        self.blackout_button.pack()

        self.start_shape_button = tk.Button(self, text="Start Shape", command=self.start_geometry_animation)
        self.start_shape_button.pack()

        self.stop_shape_button = tk.Button(self, text="Stop Shape", command=self.stop_geometry_animation)
        self.stop_shape_button.pack()

        self.canvas = EntityCanvas(self, self.universes, self.update_entity_color, screen_width, screen_height)
        self.canvas.pack()

        # Variables pour l'animation
        self.geometry_animating = False
        self.shape_pos = [10, 10]
        self.shape_dir = [1, 1]
        self.shape_size = 10
        self.shape_color = {"r": 255, "g": 255, "b": 0, "w": 0}

        self.bind("<Escape>", lambda e: self.destroy())

    def start_geometry_animation(self):
        self.geometry_animating = True
        self.run_geometry_animation()

    def stop_geometry_animation(self):
        self.geometry_animating = False
        
    def run_geometry_animation(self):
        if not self.geometry_animating:
            return

        self.set_all_black()

        max_pos = 128 - self.shape_size
        for i in range(2):
            self.shape_pos[i] += self.shape_dir[i]
            if self.shape_pos[i] <= 0 or self.shape_pos[i] >= max_pos:
                self.shape_dir[i] *= -1

        entity_ids = self.get_entities_in_circle(self.shape_pos[0], self.shape_pos[1], self.shape_size)
        for eid in entity_ids:
            self.entity_colors[eid] = self.shape_color
            self.canvas.itemconfig(self.canvas.find_withtag(f"entity_{eid}"), fill=self.canvas.rgb_to_hex(self.shape_color))

        self.send_messages()
        self.after(50, self.run_geometry_animation)

    def get_entities_in_circle(self, cx, cy, radius):
        result = []
        id_to_coord = self.build_entity_id_lookup()
        for eid, (x, y) in id_to_coord.items():
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                result.append(eid)
        return result

    def build_entity_id_lookup(self):
        size = 4
        padding = 1

        lookup = {}
        all_entities = sorted([
            entity_id
            for universe in self.universes.values()
            for entity_id in universe.entity_ids
        ])

        x = 0
        start_row = 130
        entity_idx = 0

        while entity_idx < len(all_entities):
            height = 130 if x % 2 == 0 else 129
            y_direction = -1 if x % 2 == 0 else 1

            for i in range(height):
                if entity_idx >= len(all_entities):
                    break
                row = start_row - i if y_direction == -1 else i
                col = x
                entity_id = all_entities[entity_idx]
                lookup[entity_id] = (col, row)
                entity_idx += 1
            x += 1

        return lookup

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
