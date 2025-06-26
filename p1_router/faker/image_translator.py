from PIL import Image
import socket

def generate_ehub_packet_from_pixels(pixels, universe=1):
    """
    pixels : list of (entity_id, (r, g, b))
    universe : eHuB universe number
    """
    header = b"eHuB"
    msg_type = bytes([1])
    universe_byte = bytes([universe])
    reserved = b"\x00" * 4

    body = b""
    for entity_id, (r, g, b) in pixels:
        body += entity_id.to_bytes(2, 'big') + bytes([r, g, b]) + b"\x00"

    return header + msg_type + universe_byte + reserved + body

def send_udp_packet(packet, port=5568):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(packet, ("127.0.0.1", port))
    sock.close()

def image_to_led_entities(image_path, start_id=1000, max_entities=170):
    img = Image.open(image_path).convert("RGB")
    img = img.resize((max_entities, 1))  # horizontal strip
    pixels = list(img.getdata())  # [(r,g,b), ...]

    return [(start_id + i, rgb) for i, rgb in enumerate(pixels[:max_entities])]

if __name__ == "__main__":
    image_path = "faker/sample.png"  # à adapter
    universe = 1
    start_id = 1000

    entities = image_to_led_entities(image_path, start_id=start_id)
    packet = generate_ehub_packet_from_pixels(entities, universe=universe)
    send_udp_packet(packet)
    print(f"Image envoyée sous forme de {len(entities)} entités à l’univers {universe}")
