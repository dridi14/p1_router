from p1_router.artnet_sender.sender import send_dmx_packet

VALID_IPS = {"192.168.1.45", "192.168.1.46", "192.168.1.47", "192.168.1.48"}

def route_parsed_message(message: dict) -> None:
    """
    Traite un message eHuB déjà parsé + mappé, envoie les données DMX via ArtNet.
    Vérifie les IPs avant envoi.
    """
    universe = message.get("universe")
    for entity in message.get("entities", []):
        ip = entity.get("controller_ip")
        if ip not in VALID_IPS:
            print(f"[UNIV {universe}] IP invalide : {ip} pour entity {entity.get('id')}")
            continue

        start_channel = entity["channel_start"]
        channels = entity["channels"]  # ex: ["r", "g", "b"]
        color = entity["color"]        # ex: {"r": 255, "g": 255, "b": 0}

        # Crée un tableau DMX de 512 canaux (initialisé à 0)
        dmx_data = [0] * 512
        for i, c in enumerate(channels):
            value = color.get(c, 0)
            dmx_data[start_channel - 1 + i] = value

        # Envoi du paquet DMX via ArtNet
        send_dmx_packet(ip, universe, dmx_data)

