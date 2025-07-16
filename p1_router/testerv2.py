"""Entity LED mapping GUI with image and video playback.


Requires:
    pip install pillow opencv-python
"""

from __future__ import annotations

import tkinter as tk
from tkinter.colorchooser import askcolor
from tkinter import filedialog
from typing import Dict, Tuple
from collections import defaultdict

import cv2
from PIL import Image

from config.config_loader import load_config_tables
from artnet_sender.sender import create_and_send_dmx_packet
from models.decoder import EntityState

RGBDict = Dict[str, int]


class EntityCanvas(tk.Canvas):
    def __init__(
        self,
        master: tk.Misc,
        entity_table: Dict[int, Dict[str, int]],
        update_callback,
        width: int,
        height: int,
    ) -> None:
        super().__init__(master, bg="white", width=width, height=height)
        self.entity_table = entity_table
        self.update_callback = update_callback
        self.selected_color: RGBDict = {"r": 0, "g": 0, "b": 0}
        self.entity_rects: Dict[int, int] = {}
        self.entity_positions: Dict[int, Tuple[int, int]] = {}
        self.num_columns: int = 0
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<Button-1>", self._on_click)
        self._draw_all_entities()

    def paint_image(self, image: Image.Image) -> None:
        if not self.entity_rects or self.num_columns == 0:
            return
        resized = image.resize((self.num_columns, 129)).convert("RGB")
        for rect, entity_id in self.entity_rects.items():
            col, row = self.entity_positions[entity_id]
            r, g, b = resized.getpixel((col, row))
            colour = {"r": r, "g": g, "b": b}
            self.itemconfig(rect, fill=self._rgb_to_hex(colour))
            self.update_callback(entity_id, colour)

    def set_selected_color(self, rgb: Tuple[float, float, float]) -> None:
        self.selected_color = {"r": int(rgb[0]), "g": int(rgb[1]), "b": int(rgb[2])}

    def set_all_to_black(self) -> None:
        for rect in self.entity_rects:
            self.itemconfig(rect, fill="#000000")
            entity_id = self.entity_rects[rect]
            self.update_callback(entity_id, {"r": 0, "g": 0, "b": 0})

    def _draw_all_entities(self) -> None:
        size, padding = 8, 1
        col_width, row_height = size + padding, size + padding
        all_entities = sorted(self.entity_table.keys())
        x, entity_idx = 0, 0
        start_row = 128
        while entity_idx < len(all_entities):
            height = 129 if x % 2 == 0 else 128
            y_dir = -1 if x % 2 == 0 else 1
            for i in range(height):
                if entity_idx >= len(all_entities):
                    break
                row = start_row - i if y_dir == -1 else i
                col = x
                x1, y1 = col * col_width, row * row_height
                x2, y2 = x1 + size, y1 + size
                entity_id = all_entities[entity_idx]
                rect = self.create_rectangle(x1, y1, x2, y2, fill="#000000")
                self.entity_rects[rect] = entity_id
                self.entity_positions[entity_id] = (col, row)
                entity_idx += 1
            entity_idx += 1
            x += 1
        self.num_columns = x

    def _on_click(self, event: tk.Event) -> None:
        self._apply_color(event.x, event.y)

    def _on_drag(self, event: tk.Event) -> None:
        self._apply_color(event.x, event.y)

    def _apply_color(self, x: int, y: int) -> None:
        item = self.find_closest(x, y)
        if item and item[0] in self.entity_rects:
            entity_id = self.entity_rects[item[0]]
            self.itemconfig(item[0], fill=self._rgb_to_hex(self.selected_color))
            self.update_callback(entity_id, self.selected_color.copy())

    @staticmethod
    def _rgb_to_hex(color: RGBDict) -> str:
        return f'#{color["r"]:02x}{color["g"]:02x}{color["b"]:02x}'


class TestUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ArtNet Test UI")
        self.attributes("-fullscreen", True)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight() - 100

        self.entity_table, self.universe_table, self.channel_mapping_table = load_config_tables("config/config.json")

        self._setup_controls()
        self.canvas = EntityCanvas(
            self, self.entity_table, self._update_entity_color, screen_width, screen_height
        )
        self.canvas.pack()
        self.video_cap: cv2.VideoCapture | None = None
        self.bind("<Escape>", lambda _e: self.destroy())

    def _setup_controls(self) -> None:
        controls = tk.Frame(self)
        controls.pack()
        tk.Button(controls, text="Select Color", command=self._choose_color).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(controls, text="Upload Image", command=self._load_image).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(controls, text="Play Video", command=self._play_video).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(controls, text="Send Once", command=self._send_messages).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(controls, text="Set All to Black", command=self._set_all_black).pack(side=tk.LEFT, padx=5, pady=5)

    def _choose_color(self) -> None:
        rgb, _ = askcolor()
        if rgb:
            self.canvas.set_selected_color(rgb)

    def _load_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")],
        )
        if file_path:
            image = Image.open(file_path)
            self.canvas.paint_image(image)
            self._send_messages()

    def _play_video(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select a video",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")],
        )
        if file_path:
            if self.video_cap is not None and self.video_cap.isOpened():
                self.video_cap.release()
            self.video_cap = cv2.VideoCapture(file_path)
            self._next_frame()

    def _next_frame(self) -> None:
        if self.video_cap is None or not self.video_cap.isOpened():
            return
        ret, frame = self.video_cap.read()
        if not ret:
            self.video_cap.release()
            self.video_cap = None
            return
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.canvas.paint_image(Image.fromarray(frame_rgb))
        self._send_messages()
        fps = max(self.video_cap.get(cv2.CAP_PROP_FPS), 5)
        delay = int(1000 / fps)
        self.after(delay, self._next_frame)

    def _update_entity_color(self, entity_id: int, color: RGBDict) -> None:
        self.entity_table[entity_id].update(color)

    def _send_messages(self) -> None:
        universe_entities = defaultdict(list)
        for entity_id, state in self.entity_table.items():
            universe_entities[state["universe"]].append(
                EntityState(entity_id, state["r"], state["g"], state["b"])
            )
        for universe_id, entities in universe_entities.items():
            create_and_send_dmx_packet(
                entities,
                self.universe_table[universe_id],
                universe_id,
                self.channel_mapping_table
            )

    def _set_all_black(self) -> None:
        for entity_id in self.entity_table:
            self.entity_table[entity_id].update({"r": 0, "g": 0, "b": 0})
        self.canvas.set_all_to_black()
        self._send_messages()


if __name__ == "__main__":
    app = TestUI()
    app.mainloop()
