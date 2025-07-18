import socket
import struct
import threading
import tkinter as tk
from typing import List, Dict, Optional
from models.decoder import EntityState

ARTNET_PORT = 6454
ARTNET_HEADER_ID = b'Art-Net\x00'
OPCODE_OUTPUT = 0x5000

# Global visualizer state
_visualizer_canvas = None
_visualizer_rects = {}
_visualizer_ready = False
_visualizer_lock = threading.Lock()
_visualizer_colors = {}


def initialize_dmx_visualizer(all_entity_ids: List[int]):
    """Initialize the visualizer once with the full list of entity IDs."""
    global _visualizer_canvas, _visualizer_rects, _visualizer_ready, _visualizer_colors

    def visualizer_thread():
        root = tk.Tk()
        root.title("DMX Visualizer")

        size = 6
        padding = 0
        col_width = size + padding
        row_height = size + padding

        all_entity_ids_sorted = sorted(set(all_entity_ids))
        entity_idx = 0
        x = 0
        while entity_idx < len(all_entity_ids_sorted):
            height = 129 if x % 2 == 0 else 128
            entity_idx += height + 1
            x += 1
        num_columns = x

        canvas_width = num_columns * col_width
        canvas_height = 129 * row_height
        canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg="black")
        canvas.pack()

        rects = {}
        entity_idx = 0
        x = 0
        while entity_idx < len(all_entity_ids_sorted):
            height = 129 if x % 2 == 0 else 128
            y_dir = -1 if x % 2 == 0 else 1
            start_row = 128
            for i in range(height):
                if entity_idx >= len(all_entity_ids_sorted):
                    break
                row = start_row - i if y_dir == -1 else i
                col = x
                x1 = col * col_width
                y1 = row * row_height
                x2 = x1 + size
                y2 = y1 + size
                entity_id = all_entity_ids_sorted[entity_idx]
                rects[entity_id] = canvas.create_rectangle(x1, y1, x2, y2, fill="#000000", outline="")
                entity_idx += 1
            entity_idx += 1
            x += 1

        with _visualizer_lock:
            globals()["_visualizer_canvas"] = canvas
            globals()["_visualizer_rects"] = rects
            globals()["_visualizer_ready"] = True

        def update_loop():
            with _visualizer_lock:
                for entity_id, rect in rects.items():
                    color = _visualizer_colors.get(entity_id, "#000000")
                    canvas.itemconfig(rect, fill=color)
            canvas.update_idletasks()
            root.after(25, update_loop)

        update_loop()
        root.mainloop()

    threading.Thread(target=visualizer_thread, daemon=True).start()


def _update_dmx_visualizer(entities: List[EntityState]):
    if not _visualizer_ready:
        return
    with _visualizer_lock:
        for ent in entities:
            color = f'#{ent.r:02x}{ent.g:02x}{ent.b:02x}'
            _visualizer_colors[ent.id] = color


def create_and_send_dmx_packet(
    entities: List[EntityState],
    ip: str,
    universe: int,
    channel_mapping: Optional[Dict[int, int]] = None
) -> None:
    if not entities:
        return

    dmx_data = [0] * 512

    for entity in entities:
        base = channel_mapping.get(entity.id, (entity.id % 170) * 3) if channel_mapping else (entity.id % 170) * 3
        if base + 2 >= 512:
            print(f"Avertissement: L'entité {entity.id} dépasse la limite DMX")
            continue
        dmx_data[base] = entity.r
        dmx_data[base + 1] = entity.g
        dmx_data[base + 2] = entity.b

    _update_dmx_visualizer(entities)
    send_dmx_packet_raw(ip, universe, dmx_data)


def send_dmx_packet_raw(ip: str, universe: int, dmx_data: List[int]) -> None:
    if len(dmx_data) > 512:
        raise ValueError("DMX data exceeds 512 bytes")

    header = ARTNET_HEADER_ID
    opcode = struct.pack('<H', OPCODE_OUTPUT)
    prot_ver = struct.pack('<H', 14)
    sequence = b'\x00'
    physical = b'\x00'
    universe_bytes = struct.pack('<H', universe & 0xFF)
    length = struct.pack('>H', len(dmx_data))
    data = bytes(dmx_data)

    packet = header + opcode + prot_ver + sequence + physical + universe_bytes + length + data

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(packet, (ip, ARTNET_PORT))
    sock.close()
