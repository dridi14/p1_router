"""Entity LED mapping GUI with image and video playback.

Every time a new video frame is rendered, DMX messages are sent immediately so that
entities update in real‑time on the physical fixtures – no extra clicks required.

Requires:
    pip install pillow opencv-python
"""

from __future__ import annotations

import tkinter as tk
from tkinter.colorchooser import askcolor
from tkinter import filedialog
from typing import Dict, Tuple

import cv2
from PIL import Image

from config.config_loader import load_universe_config

RGBDict = Dict[str, int]


class EntityCanvas(tk.Canvas):
    """Canvas that draws entities and paints them from images."""

    def __init__(
        self,
        master: tk.Misc,
        universes: Dict[int, "Universe"],
        update_callback,
        width: int,
        height: int,
    ) -> None:
        super().__init__(master, bg="white", width=width, height=height)
        self.universes = universes
        self.update_callback = update_callback
        self.selected_color: RGBDict = {"r": 0, "g": 0, "b": 0, "w": 0}
        self.entity_rects: Dict[int, int] = {}
        self.entity_positions: Dict[int, Tuple[int, int]] = {}
        self.num_columns: int = 0
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<Button-1>", self._on_click)
        self._draw_all_entities()

    # ------------------------------------------------------------------
    #  Public helpers
    # ------------------------------------------------------------------
    def paint_image(self, image: Image.Image) -> None:
        """Resize *image* to the grid and propagate its pixels to rectangles."""
        if not self.entity_rects or self.num_columns == 0:
            return
        resized = image.resize((self.num_columns, 129)).convert("RGB")
        for rect, entity_id in self.entity_rects.items():
            col, row = self.entity_positions[entity_id]
            r, g, b = resized.getpixel((col, row))
            colour = {"r": r, "g": g, "b": b, "w": 0}
            self.itemconfig(rect, fill=self._rgb_to_hex(colour))
            self.update_callback(entity_id, colour)

    def set_selected_color(self, rgb: Tuple[float, float, float]) -> None:
        self.selected_color = {"r": int(rgb[0]), "g": int(rgb[1]), "b": int(rgb[2]), "w": 0}

    def set_all_to_black(self) -> None:
        for rect in self.entity_rects:
            self.itemconfig(rect, fill="#000000")
            entity_id = self.entity_rects[rect]
            self.update_callback(entity_id, {"r": 0, "g": 0, "b": 0, "w": 0})

    # ------------------------------------------------------------------
    #  Internal utilities
    # ------------------------------------------------------------------
    def _draw_all_entities(self) -> None:
        size, padding = 8, 1
        col_width, row_height = size + padding, size + padding
        all_entities = sorted(
            entity_id
            for universe_id in sorted(self.universes.keys())
            for entity_id in self.universes[universe_id].entity_ids
        )
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
    """Main GUI – now fires DMX on every video frame."""

    def __init__(self) -> None:
        super().__init__()
        self.title("ArtNet Test UI")
        self.attributes("-fullscreen", True)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight() - 100
        self.entity_colors: Dict[int, RGBDict] = {}
        self.universes = load_universe_config("config/config.json")
        self._setup_controls()
        self.canvas = EntityCanvas(
            self, self.universes, self._update_entity_color, screen_width, screen_height
        )
        self.canvas.pack()
        self.video_cap: cv2.VideoCapture | None = None
        self.bind("<Escape>", lambda _e: self.destroy())

    # ------------------------------------------------------------------
    #  Controls
    # ------------------------------------------------------------------
    def _setup_controls(self) -> None:
        controls = tk.Frame(self)
        controls.pack()
        tk.Button(controls, text="Select Color", command=self._choose_color).pack(
            side=tk.LEFT, padx=5, pady=5
        )
        tk.Button(controls, text="Upload Image", command=self._load_image).pack(
            side=tk.LEFT, padx=5, pady=5
        )
        tk.Button(controls, text="Play Video", command=self._play_video).pack(
            side=tk.LEFT, padx=5, pady=5
        )
        tk.Button(controls, text="Send Once", command=self._send_messages).pack(
            side=tk.LEFT, padx=5, pady=5
        )
        tk.Button(controls, text="Set All to Black", command=self._set_all_black).pack(
            side=tk.LEFT, padx=5, pady=5
        )

    # ------------------------------------------------------------------
    #  UI callbacks
    # ------------------------------------------------------------------
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
        """Grab next frame, update canvas, and send DMX immediately."""
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
        self.entity_colors[entity_id] = color

    def _send_messages(self) -> None:
        for universe in self.universes.values():
            universe.entities_states.clear()
            for entity_id in universe.entity_ids:
                if entity_id in self.entity_colors:
                    universe.update_entity_state(entity_id, self.entity_colors[entity_id])
        for universe in self.universes.values():
            if universe.entities_states:
                universe.send_message()

    def _set_all_black(self) -> None:
        self.canvas.set_all_to_black()
        self.entity_colors = {
            eid: {"r": 0, "g": 0, "b": 0, "w": 0}
            for universe in self.universes.values()
            for eid in universe.entity_ids
        }
        self._send_messages()


if __name__ == "__main__":
    app = TestUI()
    app.mainloop()
