import threading
import socket
import time
from typing import Dict, Any, List
from collections import defaultdict
from ehub_receiver.parser import decode_ehub_packet, EHubUpdateMsg, EHubConfigMsg
from config.config_loader import load_config_tables
from models.decoder import EntityState
from artnet_sender.sender import create_and_send_dmx_packet
import tkinter as tk

# Shared config tables
entity_table, universe_table, channel_mapping_table = load_config_tables("config/config.json")


def event_listener(entity_table: Dict[int, Dict[str, Any]]):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", 5568))
    print("Listening for eHuB messages…")

    while True:
        data, _ = sock.recvfrom(65535)
        try:
            msg = decode_ehub_packet(data)
        except ValueError:
            continue

        if isinstance(msg, EHubUpdateMsg):
            for ent in msg.entities:
                if ent.id not in entity_table:
                    continue

                entity_table[ent.id]["r"] = ent.red
                entity_table[ent.id]["g"] = ent.green
                entity_table[ent.id]["b"] = ent.blue
        elif isinstance(msg, EHubConfigMsg):
            for r in msg.ranges:
                base = (r.red, r.green, r.blue, msg.universe)
                update = {
                    r.start_id + offset: {
                        "r": base[0],
                        "g": base[1],
                        "b": base[2],
                        "universe": base[3]
                    }
                    for offset in range(r.length)
                }
                entity_table.update(update)



def dmx_sender(entity_table: Dict[int, Dict[str, Any]],
               universe_table: Dict[int, str],
               channel_mapping_table: Dict[int, int]):
    while True:
        universe_entities: Dict[int, List[EntityState]] = defaultdict(list)

        # Build groups
        for entity_id, state in entity_table.items():
            universe_entities[state["universe"]].append(
                EntityState(entity_id, state["r"], state["g"], state["b"])
            )

        # Send packets
        for universe_id, entities in universe_entities.items():
            create_and_send_dmx_packet(
                entities,
                universe_table[universe_id],
                universe_id,
                channel_mapping_table
            )

        time.sleep(0.001)

def visualizer(entity_table):
    """Tkinter GUI running on a thread, showing entities in original snake pattern but as pixels."""
    root = tk.Tk()
    root.title("Live DMX Visualizer")

    size = 6   # smaller blocks = more fit on screen
    padding = 0
    col_width, row_height = size + padding, size + padding

    # Compute total number of columns needed
    all_entities = sorted(entity_table.keys())
    entity_idx = 0
    x = 0
    while entity_idx < len(all_entities):
        height = 129 if x % 2 == 0 else 128
        entity_idx += height + 1
        x += 1
    num_columns = x

    # Set canvas size based on calculated columns and max 129 rows
    canvas_width = num_columns * col_width
    canvas_height = 129 * row_height

    canvas = tk.Canvas(root, bg="black", width=canvas_width, height=canvas_height)
    canvas.pack()

    # Draw rectangles in your snake pattern
    rects = {}
    entity_idx = 0
    x = 0
    while entity_idx < len(all_entities):
        height = 129 if x % 2 == 0 else 128
        y_dir = -1 if x % 2 == 0 else 1
        start_row = 128
        for i in range(height):
            if entity_idx >= len(all_entities):
                break
            row = start_row - i if y_dir == -1 else i
            col = x
            x1 = col * col_width
            y1 = row * row_height
            x2 = x1 + size
            y2 = y1 + size
            entity_id = all_entities[entity_idx]
            rects[entity_id] = canvas.create_rectangle(x1, y1, x2, y2, fill="#000000", outline="")
            entity_idx += 1
        entity_idx += 1
        x += 1

    def update_colors():
        for entity_id, state in entity_table.items():
            if entity_id in rects:
                hex_color = f'#{state["r"]:02x}{state["g"]:02x}{state["b"]:02x}'
                canvas.itemconfig(rects[entity_id], fill=hex_color)
        root.after(50, update_colors)

    update_colors()
    root.mainloop()

if __name__ == "__main__":
    threading.Thread(
        target=event_listener, args=(entity_table,), daemon=True
    ).start()

    threading.Thread(
        target=dmx_sender,
        args=(entity_table, universe_table, channel_mapping_table),
        daemon=True
    ).start()

    threading.Thread(
        target=visualizer, args=(entity_table,), daemon=True
    ).start()

    # Keep main alive
    while True:
        time.sleep(1)
