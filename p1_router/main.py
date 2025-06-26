import threading
import socket
import time
from typing import Dict, Any, Set, List
from ehub_receiver.parser import decode_ehub_packet, EHubUpdateMsg, EHubConfigMsg
from config.config_loader import load_config_tables
from models.decoder import EntityState
from artnet_sender.sender import create_and_send_dmx_packet

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

                # If using lock:
                # with entity_table_lock:
                entity_table[ent.id]["r"] = ent.red
                entity_table[ent.id]["g"] = ent.green
                entity_table[ent.id]["b"] = ent.blue
        elif isinstance(msg, EHubConfigMsg):
            for r in msg.ranges:
                for offset in range(r.length):
                    entity_id = r.start_id + offset
                    entity_table[entity_id] = {
                        "r": r.red,
                        "g": r.green,
                        "b": r.blue,
                        "universe": msg.universe,
                    }


# ─────────────────────────────────────────────────────────────────────────────
def dmx_sender(entity_table: Dict[int, Dict[str, Any]],
               universe_table: Dict[int, str],
               channel_mapping_table: Dict[int, int]):
    while True:
        universe_entities: Dict[int, List[EntityState]] = {}

        # with entity_table_lock:
        for entity_id, state in entity_table.items():
            uni = state["universe"]
            if uni not in universe_entities:
                universe_entities[uni] = []
            universe_entities[uni].append(EntityState(
                id=entity_id,
                r=state["r"],
                g=state["g"],
                b=state["b"]
            ))

        for universe_id, entities in universe_entities.items():
            ip = universe_table[universe_id]
            create_and_send_dmx_packet(entities, ip, universe_id, channel_mapping_table)

        time.sleep(0.025)  # 40Hz (25ms)

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    threading.Thread(
        target=event_listener, args=(entity_table,), daemon=True
    ).start()

    threading.Thread(
        target=dmx_sender,
        args=(entity_table, universe_table, channel_mapping_table),
        daemon=True
    ).start()

    # Keep main alive
    while True:
        time.sleep(1)
