import json
from pathlib import Path
from models.decoder import ParsedMessage

class Universe:
    def __init__(self, name: int, ip: str, entity_ids: set[int]):
        self.name = name  # ArtNet universe (int)
        self.ip = ip
        self.parsed_message: ParsedMessage = None

    def update_parsed_message(self, parsed_message: ParsedMessage) -> None:
        """
        Met à jour le message analysé pour l'univers.
        """
        self.parsed_message = parsed_message
        self.send_message()

    def send_message(self) -> None:
        """
        Envoie un message à l'univers, enregistre le dernier message envoyé.
        """
        from p1_router.artnet_sender.sender import send_dmx_packet

        send_dmx_packet(self.parsed_message)

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

    return universes
