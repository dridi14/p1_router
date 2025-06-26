from config.config_loader import load_universe_config
import socket
from ehub_receiver.parser import decode_ehub_packet, EHubUpdateMsg, EHubConfigMsg
import logging
import socket
from collections import defaultdict
from typing import Dict, Set

## load config 
universes = load_universe_config("config/config.json")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", 5568))
print("Listening for eHuB messages…")

# Optional: map entity-ID → universe in O(1) instead of a nested loop
entity_to_universe: Dict[int, "Universe"] = {}
for uni in universes.values():
    for eid in uni.entity_ids:
        entity_to_universe[eid] = uni

# ───────────────────────────────────────────────────────────────────────────
while True:
    data, addr = sock.recvfrom(65_535)

    # 1. Parse raw packet → domain object (update or config)
    try:
        msg = decode_ehub_packet(data)
    except ValueError as exc:           # bad header, bad gzip, wrong size, …
        logging.debug("Drop malformed packet from %s: %s", addr, exc)
        continue

    # 2. CONFIG message: update local universe metadata and move on
    # ----------------------------------------------------------------
    if isinstance(msg, EHubConfigMsg):
        uni = universes.get(msg.universe)
        if not uni:
            logging.warning("CONFIG for unknown universe %d", msg.universe)
            continue

        uni.apply_config_ranges(msg.ranges)   # write your own helper
        logging.info("Updated config for universe %s (%d ranges)",
                     uni.name, len(msg.ranges))
        continue                               # nothing to transmit

    # 3. UPDATE message: push RGB(W) to the right universes
    # ----------------------------------------------------------------
    dirty: Set["Universe"] = set()

    for ent in msg.entities:
        # Fast O(1) lookup via the pre-built dictionary
        target_universe = entity_to_universe.get(ent.id)
        if not target_universe:
            logging.debug("Entity %d not mapped to any universe", ent.id)
            continue

        target_universe.update_entity_state(
            ent.id,
            {
                "r": ent.red,
                "g": ent.green,
                "b": ent.blue,
                "w": getattr(ent, "white", 0),   # ignore if no W channel in use
            },
        )
        dirty.add(target_universe)

    # 4. Transmit only the universes that actually changed this frame
    # ----------------------------------------------------------------
    for uni in dirty:
        uni.send_message()
        print("Sent frame for universe %s", uni.name)
        logging.debug("Sent frame for universe %s", uni.name)


# if __name__ == "__main__":
#     with open("ehub_sample1.bin", "rb") as f:
#         data = f.read()
#         try:
#             parsed_message = decode_ehub_packet(data)
#             print(f"Parsed message: {parsed_message}")
#         except ValueError as e:
#             print(f"Error parsing eHuB message: {e}")