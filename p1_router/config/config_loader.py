import json
from pathlib import Path
from models.decoder import EntityState

class Universe:
    def __init__(self, name: int, ip: str, entity_ids: set[int]):
        self.name = name  # ArtNet universe number
        self.ip = ip
        self.entity_ids = entity_ids
        self.entities_states: dict[int, EntityState] = {}
        self.channel_mapping: dict[int, int] = {}  # Mapping des IDs d'entité vers les canaux de départ

    def update_entity_state(self, entity_id: int, state: dict) -> None:
        self.entities_states[entity_id] = EntityState(
            id=entity_id,
            r=state["r"],
            g=state["g"],
            b=state["b"]
        )

    def send_message(self) -> None:
        from artnet_sender.sender import create_and_send_dmx_packet
        create_and_send_dmx_packet(list(self.entities_states.values()), self.ip, self.name, self.channel_mapping)

def load_universe_config(config_path: str) -> dict[int, Universe]:
    """
    Load universes from config file.
    Returns a dict of {universe_number: Universe}
    """
    config_data = json.loads(Path(config_path).read_text())
    universes: dict[int, Universe] = {}

    for block in config_data:
        from_id = block["from"]
        to_id = block["to"]
        ip = block["ip"]
        universe_id = block["universe"]
        entity_ids = set(range(from_id, to_id + 1))

        if universe_id in universes:
            # merge entity IDs if universe defined multiple times
            universes[universe_id].entity_ids.update(entity_ids)
        else:
            universes[universe_id] = Universe(universe_id, ip, entity_ids)
            
        # Créer un mapping de canaux simple pour chaque entité
        # Par défaut, on place les entités de façon séquentielle (3 canaux par entité)
        # Dans un univers réel, ce mapping pourrait être plus complexe
        universe = universes[universe_id]
        for entity_id in range(from_id, to_id + 1):
            # Calcul d'un offset de canal basé sur l'ID relatif dans ce bloc
            # Chaque entité prend 3 canaux (R,G,B)
            relative_id = entity_id - from_id
            channel_start = relative_id * 3
            universe.channel_mapping[entity_id] = channel_start

    return universes
