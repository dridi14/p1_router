import json
import socket
from PIL import Image

CONFIG_PATH = "config/config.json"
IMAGE_PATH = "faker/sample.png"

def load_config(path=CONFIG_PATH):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    universes = {}
    for block in data:
        u = block["universe"]
        if u not in universes:
            universes[u] = {
                "ip": block["ip"],
                "ids": []
            }
        universes[u]["ids"].extend(range(block["from"], block["to"] + 1))

    # tri des IDs pour chaque univers
    for u in universes:
        universes[u]["ids"].sort()

    return universes

def generate_ehub_packet(entities, universe):
    header = b"eHuB"
    msg_type = bytes([1])
    universe_byte = bytes([universe])
    reserved = b"\x00" * 4

    body = b""
    for entity_id, (r, g, b) in entities:
        body += entity_id.to_bytes(2, 'big') + bytes([r, g, b]) + b"\x00"

    return header + msg_type + universe_byte + reserved + body

def send_udp(packet, ip, port=5568):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(packet, (ip, port))
    sock.close()

def distribute_pixels(image_path, config):
    # total number of LEDs
    total_leds = sum(len(u["ids"]) for u in config.values())
    img = Image.open(image_path).convert("RGB")
    img = img.resize((total_leds, 1))  # 1D mapping
    pixels = list(img.getdata())  # [(r,g,b), ...]

    pixel_index = 0
    for universe, uconf in config.items():
        id_list = uconf["ids"]
        entities = []
        for eid in id_list:
            if pixel_index >= len(pixels):
                break
            entities.append((eid, pixels[pixel_index]))
            pixel_index += 1

        packet = generate_ehub_packet(entities, universe)
        send_udp(packet, uconf["ip"])
        print(f"✅ Univers {universe} → {len(entities)} entités envoyées à {uconf['ip']}")

if __name__ == "__main__":
    config = load_config()
    distribute_pixels(IMAGE_PATH, config)
