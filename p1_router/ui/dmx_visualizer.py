import threading
import socket
import time
from typing import Dict, Any, List
from collections import defaultdict
from ehub_receiver.parser import decode_ehub_packet, EHubUpdateMsg, EHubConfigMsg
from config.config_loader import load_config_tables
from models.decoder import EntityState
from artnet_sender.sender import create_and_send_dmx_packet, initialize_dmx_visualizer
import tkinter as tk

stop_event = threading.Event()
threads = []

# Shared config tables
entity_table, universe_table, channel_mapping_table = load_config_tables("config/config.json")


def event_listener(entity_table: Dict[int, Dict[str, Any]]):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", 5568))
    print("Listening for eHuB messages…")

    while not stop_event.is_set():
        data, _ = sock.recvfrom(65535)
        try:
            msg = decode_ehub_packet(data)
        except ValueError:
            continue

        if isinstance(msg, EHubUpdateMsg):
            for ent in msg.entities:
                if ent.id in entity_table:
                    entity_table[ent.id].update({"r": ent.red, "g": ent.green, "b": ent.blue})
        elif isinstance(msg, EHubConfigMsg):
            for r in msg.ranges:
                for offset in range(r.length):
                    eid = r.start_id + offset
                    entity_table[eid] = {"r": r.red, "g": r.green, "b": r.blue, "universe": msg.universe}


def dmx_sender(entity_table: Dict[int, Dict[str, Any]],
               universe_table: Dict[int, str],
               channel_mapping_table: Dict[int, int]):
    last_state: Dict[int, List[EntityState]] = defaultdict(list)
    # initialize_dmx_visualizer(list(entity_table.keys()))
    while not stop_event.is_set():
        current_state: Dict[int, List[EntityState]] = defaultdict(list)
        for entity_id, state in entity_table.items():
            current_state[state["universe"]].append(
                EntityState(entity_id, state["r"], state["g"], state["b"])
            )

        for universe_id, entities in current_state.items():
            if entities != last_state[universe_id]:
                create_and_send_dmx_packet(
                    entities,
                    universe_table[universe_id],
                    universe_id,
                    channel_mapping_table
                )
                last_state[universe_id] = entities
        # 40 fps
        time.sleep(0.025)

def visualizer(entity_table):
    """Tkinter GUI running on a thread, showing entities in original snake pattern but as pixels."""
    root = tk.Tk()
    root.title("Live DMX Visualizer")

    size = 6 
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

    # Draw rectangles in snake pattern
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
        if stop_event.is_set():
            root.destroy()
            return
        for entity_id, state in entity_table.items():
            if entity_id in rects:
                hex_color = f'#{state["r"]:02x}{state["g"]:02x}{state["b"]:02x}'
                canvas.itemconfig(rects[entity_id], fill=hex_color)
        root.after(25, update_colors)

    update_colors()
    root.mainloop()
    
def reset_visualizer_state():
    global threads, stop_event
    threads.clear()
    stop_event = threading.Event()

def stop_threads():
    print("Stopping threads...")
    stop_event.set()
    for t in threads:
        t.join()
    threads.clear()
    stop_event.clear()

def main() -> int:
    global threads

    # Background threads only
    threads.append(threading.Thread(target=event_listener, args=(entity_table,)))
    threads.append(threading.Thread(target=dmx_sender, args=(entity_table, universe_table, channel_mapping_table)))

    for t in threads:
        t.start()

    try:
        # Run visualizer in main thread
        visualizer(entity_table)
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Shutting down.")
    finally:
        stop_threads()
        reset_visualizer_state()
        return 1


if __name__ == "__main__":
    exit(main())
