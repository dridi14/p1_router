# parser.py  ────────────────────────────────────────────────────────────────
import gzip
from dataclasses import dataclass
from io import BytesIO
from typing import List, Union

_HEADER       = b"eHuB"
_UPDATE       = 2
_CONFIG       = 1
_BYTES_PER_LED = 6        # 2-byte id + R G B W

# ── Domain models (adapt as needed) ────────────────────────────────────────
@dataclass
class EntityState:
    id: int
    red: int
    green: int
    blue: int

@dataclass
class EHubUpdateMsg:
    universe: int
    entities: List[EntityState]

@dataclass
class ConfigRange:
    start_id: int
    length: int
    red: int
    green: int
    blue: int
    white: int

@dataclass
class EHubConfigMsg:
    universe: int
    ranges: List[ConfigRange]

# ── Public API ─────────────────────────────────────────────────────────────
def decode_ehub_packet(packet: bytes) -> Union[EHubUpdateMsg, EHubConfigMsg]:
    """
    Parse one raw eHuB UDP datagram and return a domain object.
    Raises ValueError on any structural problem.
    """
    if len(packet) < 10 or not packet.startswith(_HEADER):
        raise ValueError("Not a valid eHuB packet")

    msg_type      = packet[4]
    universe      = packet[5]
    entity_count  = int.from_bytes(packet[6:8],  "little")
    comp_len      = int.from_bytes(packet[8:10], "little")

    if 10 + comp_len > len(packet):
        raise ValueError("Payload length field larger than datagram")

    compressed    = packet[10:10 + comp_len]
    payload       = _gunzip(compressed)

    if msg_type == _CONFIG:
        raise ValueError
        return _parse_config_payload(universe, payload)
    elif msg_type == _UPDATE:
        return _parse_update_payload(universe, payload, entity_count)
    else:
        raise ValueError(f"Unknown eHuB message type {msg_type}")

# ── Helpers ────────────────────────────────────────────────────────────────
def _gunzip(blob: bytes) -> bytes:
    with gzip.GzipFile(fileobj=BytesIO(blob)) as gz:
        return gz.read()

# ---- Config ---------------------------------------------------------------
def _parse_config_payload(universe: int, payload: bytes) -> EHubConfigMsg:
    ranges: List[ConfigRange] = []

    # Each config range is 8 bytes: uint16 start, uint16 length, RGBA (4 × uint8)
    if len(payload) % 8 != 0:
        raise ValueError("Config payload size is not a multiple of 8 bytes")

    for off in range(0, len(payload), 8):
        start_id  = int.from_bytes(payload[off     : off + 2], "little")
        length    = int.from_bytes(payload[off + 2 : off + 4], "little")
        r, g, b, w = payload[off + 4 : off + 8]
        ranges.append(ConfigRange(start_id, length, r, g, b, w))

    return EHubConfigMsg(universe=universe, ranges=ranges)

# ---- Update ---------------------------------------------------------------
def _parse_update_payload(
    universe: int, payload: bytes, entity_count_field: int
) -> EHubUpdateMsg:
    if len(payload) % _BYTES_PER_LED != 0:
        raise ValueError("Update payload size is not a multiple of 6 bytes")

    # Optional cross-check with header’s entity-count field
    entity_count_payload = len(payload) // _BYTES_PER_LED
    if entity_count_field != 0 and entity_count_field != entity_count_payload:
        raise ValueError(
            f"Header says {entity_count_field} entities but payload has "
            f"{entity_count_payload}"
        )

    entities: List[EntityState] = []
    for off in range(0, len(payload), _BYTES_PER_LED):
        eid       = int.from_bytes(payload[off : off + 2], "little")
        r, g, b, w = payload[off + 2 : off + 6]
        entities.append(EntityState(eid, r, g, b))

    return EHubUpdateMsg(universe=universe, entities=entities)
