import threading
import socket
import time
import struct
import tkinter as tk
from collections import defaultdict
from typing import Dict, Any, List

from config.config_loader import load_config_tables
from models.decoder import EntityState
from artnet_sender.sender import create_and_send_dmx_packet, initialize_dmx_visualizer

stop_event = threading.Event()
threads = []

# Load config
entity_table, universe_table, channel_mapping_table = load_config_tables("config/config.json")

# Build Unity index → real entity ID map (taking gaps into account)
unity_to_real_id = {}
all_entities = sorted(entity_table.keys())
entity_idx = 0
unity_idx = 0
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
        unity_index = (127 - row) * 128 + col
        unity_to_real_id[unity_index] = all_entities[entity_idx]
        entity_idx += 1
    entity_idx += 1
    x += 1

def decode_unity_packet(data: bytes):
    result = []
    offset = 0
    while offset < len(data):
        if data[offset] == 0xFE:
            # Range update
            if offset + 8 > len(data):
                break  # malformed
            from_id = struct.unpack_from("<H", data, offset + 1)[0]
            to_id = struct.unpack_from("<H", data, offset + 3)[0]
            r, g, b = struct.unpack_from("BBB", data, offset + 5)
            for led_id in range(from_id, to_id + 1):
                result.append((led_id, r, g, b))
            offset += 8
        else:
            if offset + 5 > len(data):
                break  # malformed
            led_id = struct.unpack_from("<H", data, offset)[0]
            r, g, b = struct.unpack_from("BBB", data, offset + 2)
            result.append((led_id, r, g, b))
            offset += 5
    return result


def event_listener(entity_table: Dict[int, Dict[str, Any]]):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", 5568))
    print("Listening for Unity frames on port 5568...")

    while not stop_event.is_set():
        try:
            data, _ = sock.recvfrom(65535)
            updates = decode_unity_packet(data)
            for unity_id, r, g, b in updates:
                if unity_id in unity_to_real_id:
                    eid = unity_to_real_id[unity_id]
                    entity_table[eid].update({"r": r, "g": g, "b": b})
        except Exception as e:
            print("UDP receive error:", e)

def dmx_sender(entity_table: Dict[int, Dict[str, Any]],
               universe_table: Dict[int, str],
               channel_mapping_table: Dict[int, int]):
    last_state: Dict[int, List[EntityState]] = defaultdict(list)
    initialize_dmx_visualizer(list(entity_table.keys()))
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

        time.sleep(0.025)

if __name__ == "__main__":
    threads.append(threading.Thread(target=event_listener, args=(entity_table,), daemon=True))
    threads.append(threading.Thread(target=dmx_sender, args=(entity_table, universe_table, channel_mapping_table), daemon=True))

    for t in threads:
        t.start()

    try:
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
        for t in threads:
            t.join()
