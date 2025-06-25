
from models.decoder import ParsedMessage, EntityState

def decode_ehub_message(data: bytes) -> ParsedMessage:
    if not data.startswith(b"eHuB"):
        raise ValueError("Invalid message header")

    msg_type = data[4]  # 0x01 usually
    msg_id = data[5]

    # Entity data starts at byte 10
    entity_data = data[10:]

    entities = []
    for i in range(0, len(entity_data) - 5, 6):
        chunk = entity_data[i:i+6]
        if len(chunk) < 6:
            break
        entity_id = int.from_bytes(chunk[0:2], byteorder='big')
        r, g, b = chunk[2], chunk[3], chunk[4]
        entities.append(EntityState(id=entity_id, r=r, g=g, b=b))

    return ParsedMessage(universe=msg_id, entities=entities)
