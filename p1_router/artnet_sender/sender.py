import socket
import struct
from typing import List, Dict, Optional
from models.decoder import EntityState

ARTNET_PORT = 6454
ARTNET_HEADER_ID = b'Art-Net\x00'
OPCODE_OUTPUT = 0x5000

def create_and_send_dmx_packet(entities: List[EntityState], ip: str, universe: int, channel_mapping: Optional[Dict[int, int]] = None) -> None:
    """
    Place les entités RGB dans la trame DMX en respectant leur position.
    
    Args:
        entities: Liste des entités à envoyer
        ip: Adresse IP du contrôleur
        universe: Numéro d'univers ArtNet
        channel_mapping: Dictionnaire optionnel mappant les IDs d'entités à leurs canaux de départ
    """
    if not entities:
        return

    dmx_data = [0] * 512  # Initialiser tous les canaux à 0

    for entity in entities:
        # Si un mapping de canaux est fourni, l'utiliser, sinon positionnement séquentiel
        if channel_mapping and entity.id in channel_mapping:
            base = channel_mapping[entity.id]
        else:
            # Placement séquentiel par défaut (3 canaux par entité)
            base = (entity.id % 170) * 3  # 170 = 512/3 (maximum d'entités RGB par univers)
        
        # Vérifier que nous ne dépassons pas la limite DMX
        if base + 2 >= 512:
            print(f"Avertissement: L'entité {entity.id} dépasse la limite DMX pour l'univers {universe}")
            continue
            
        dmx_data[base] = entity.r
        dmx_data[base + 1] = entity.g
        dmx_data[base + 2] = entity.b
    
    print(f'Envoi vers univers {universe}, IP {ip}, {len([x for x in dmx_data if x > 0])} canaux actifs')
    send_dmx_packet_raw(ip, universe, dmx_data)


def send_dmx_packet_raw(ip: str, universe: int, dmx_data: List[int]) -> None:
    """
    Envoie un paquet ArtNet DMX brut à l'adresse IP et l'univers spécifiés.
    
    Args:
        ip: Adresse IP du contrôleur
        universe: Numéro d'univers ArtNet
        dmx_data: Liste des valeurs DMX (max 512)
    """
    if len(dmx_data) > 512:
        raise ValueError("DMX data exceeds 512 bytes")

    header = ARTNET_HEADER_ID
    opcode = struct.pack('<H', OPCODE_OUTPUT)  # Little-endian comme spécifié par ArtNet
    prot_ver = struct.pack('<H', 14)  # Little-endian pour la version du protocole
    sequence = b'\x00'  # Pas de séquence pour simplifier
    physical = b'\x00'  # Port physique 0
    
    # ArtNet utilise little-endian pour le numéro d'univers
    # Le premier octet est l'univers (0-255), le second est le subnet (0-15) et net (0-127)
    # Pour la simplicité, nous mettons tout dans le premier octet (univers)
    universe_bytes = struct.pack('<H', universe & 0xFF)
    
    # La longueur des données DMX doit être en big-endian selon la spec ArtNet
    length = struct.pack('>H', len(dmx_data))
    
    # Les données DMX sont juste une séquence d'octets
    data = bytes(dmx_data)

    packet = header + opcode + prot_ver + sequence + physical + universe_bytes + length + data

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(packet, (ip, ARTNET_PORT))
        sock.close()
    except Exception as e:
        print(f"Erreur lors de l'envoi du paquet ArtNet à {ip}: {e}")
