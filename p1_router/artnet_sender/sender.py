import socket
import struct
from typing import List

ARTNET_PORT = 6454
ARTNET_HEADER_ID = b'Art-Net\x00'
OPCODE_OUTPUT = 0x5000

def create_and_send_dmx_packet(entities: List, ip: str, universe: int) -> None:
    """
    Place les entités RGB à la suite dans la trame DMX.
    3 canaux par entité, sans channel_start.
    """
    if not entities:
        return

    dmx_data = [0] * 512

    for i, entity in enumerate(entities):
        base = i * 3
        if base + 2 >= 512:
            break  # dépasse la limite DMX

        dmx_data[base] = entity.r
        dmx_data[base + 1] = entity.g
        dmx_data[base + 2] = entity.b

    send_dmx_packet_raw(ip, universe, dmx_data)


def send_dmx_packet_raw(ip: str, universe: int, dmx_data: List[int]) -> None:
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
    sock.close()
