import socket
import struct
from types.decoder import ParsedMessage


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
    sock.close()

def create_and_send_dmx_packet(parsed_message) -> None:
    """
    Envoie une trame ArtNet pour un message parsé (ParsedMessage).
    Envoie une trame par IP différente.
    """
    ip_data_map = {}  # {ip: dmx_data}

    for entity in parsed_message.entities:
        ip = entity.controller_ip
        if ip not in ip_data_map:
            ip_data_map[ip] = [0] * 512

        for i, c in enumerate(entity.channels):
            value = entity.color.get(c, 0)
            dmx_index = entity.channel_start - 1 + i
            if 0 <= dmx_index < 512:
                ip_data_map[ip][dmx_index] = value

    for ip, dmx_data in ip_data_map.items():
        send_dmx_packet_raw(ip, parsed_message.universe, dmx_data)