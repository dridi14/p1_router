import socket
import struct
from models.decoder import EntityState
from typing import List

ARTNET_PORT = 6454
ARTNET_HEADER_ID = b'Art-Net\x00'
OPCODE_OUTPUT = 0x5000

def send_dmx_packet_raw(ip: str, universe: int, dmx_data: list[int]) -> None:
    if len(dmx_data) > 512:
        raise ValueError("DMX data exceeds 512 bytes")

    header = ARTNET_HEADER_ID
    opcode = struct.pack('<H', OPCODE_OUTPUT)
    prot_ver = struct.pack('>H', 14)
    sequence = b'\x00'
    physical = b'\x00'
    universe_bytes = struct.pack('<H', universe)
    length = struct.pack('>H', len(dmx_data))
    data = bytes(dmx_data)

    packet = header + opcode + prot_ver + sequence + physical + universe_bytes + length + data

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(packet, (ip, ARTNET_PORT))
    print(f"Sent DMX packet to {ip}:{ARTNET_PORT}, universe {universe}, data length {len(dmx_data)}")
    sock.close()

def create_and_send_dmx_packet(entities: List[EntityState], ip, universe: int) -> None:
    """
    Agrège les données DMX de plusieurs entités et envoie un seul paquet ArtNet à l'IP donnée.

    Args:
        entities: Liste d'EntityState (doit contenir channel_start, channels, color, universe).
        ip: IP du contrôleur ArtNet cible.
    """
    if not entities:
        return

    dmx_data = [0] * 512

    for entity in entities:
        start = entity.channel_start
        for i, ch in enumerate(entity.channels):
            value = entity.color.get(ch, 0)
            index = start - 1 + i
            if 0 <= index < 512:
                dmx_data[index] = value

    send_dmx_packet_raw(ip, universe, dmx_data) 