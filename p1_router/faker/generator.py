import socket
import time

def generate_fake_ehub_packet(entities, universe=1):
    """
    Crée une trame eHuB binaire avec en-tête 'eHuB', msg_type = 0x01, universe = `universe`.
    Chaque entité : 2 bytes ID + 3 bytes RGB + 1 byte padding.
    """
    header = b"eHuB"
    msg_type = bytes([1])
    universe_byte = bytes([universe])
    reserved = b"\x00" * 4

    body = b""
    for e_id, (r, g, b) in entities.items():
        body += e_id.to_bytes(2, 'big') + bytes([r, g, b]) + b"\x00"

    return header + msg_type + universe_byte + reserved + body

def send_udp_packet(packet, port=5568):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(packet, ("127.0.0.1", port))
    sock.close()

if __name__ == "__main__":
    # Exemple d'entités simulées
    fake_entities = {
        1001: (255, 0, 0),    # rouge
        1002: (0, 255, 0),    # vert
        1003: (0, 0, 255),    # bleu
    }

    packet = generate_fake_ehub_packet(fake_entities)
    print("Envoi du paquet eHuB simulé...")
    send_udp_packet(packet)
    time.sleep(1)
