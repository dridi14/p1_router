import json
from pathlib import Path
from models.decoder import EntityState

import json
from pathlib import Path
from typing import Dict, Any, Tuple


class Universe:
    def __init__(self, name: int, ip: str, entity_ids: set[int]):
        self.name = name  # ArtNet universe number
        self.ip = ip
        self.entity_ids = entity_ids
        self.entities_states: dict[int, EntityState] = {}
        self.channel_mapping: dict[
            int, int
        ] = {}  # Mapping des IDs d'entité vers les canaux de départ

    def update_entity_state(self, entity_id: int, state: dict) -> None:
        self.entities_states[entity_id] = EntityState(
            id=entity_id, r=state["r"], g=state["g"], b=state["b"]
        )

    def send_message(self) -> None:
        from artnet_sender.sender import create_and_send_dmx_packet

        create_and_send_dmx_packet(
            list(self.entities_states.values()),
            self.ip,
            self.name,
            self.channel_mapping,
        )


def load_config_tables(
    config_path: str,
) -> Tuple[Dict[int, Dict[str, Any]], Dict[int, str], Dict[int, int]]:
    """
    Loads the configuration and returns three tables:
    - entity_table: {entity_id: {'r': 0, 'g': 0, 'b': 0, 'universe': int}}
    - universe_table: {universe_id: ip}
    - channel_mapping_table: {entity_id: dmx_start_channel}
    """
    config_data = json.loads(Path(config_path).read_text())

    entity_table: Dict[int, Dict[str, Any]] = {}
    universe_table: Dict[int, str] = {}
    channel_mapping_table: Dict[int, int] = {}

    for block in config_data:
        from_id = block["from"]
        to_id = block["to"]
        ip = block["ip"]
        universe_id = block["universe"]

        universe_table[universe_id] = ip

        for i, entity_id in enumerate(range(from_id, to_id + 1)):
            entity_table[entity_id] = {
                "r": 0,
                "g": 0,
                "b": 0,
                "universe": universe_id,
            }

            channel_mapping_table[entity_id] = i * 3

    return entity_table, universe_table, channel_mapping_table
