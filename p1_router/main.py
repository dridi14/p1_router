from config.config_loader import load_universe_config
import socket
from ehub_receiver.parser import decode_ehub_message

## load config 
universes = load_universe_config("config/config.json")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', 5568))  
print("Listening for eHuB messages...")

while True:
    data, addr = sock.recvfrom(65535)
    parsed_message = decode_ehub_message(data)
    if parsed_message is None:
        print("Received invalid eHuB message")
        continue
    for entity in parsed_message.entities:
        for universe in universes.values():
            if entity.id in universe.entity_ids:
                universe.update_entity_state(entity.id, {
                    "r": entity.r,
                    "g": entity.g,
                    "b": entity.b,
                })
                break

    for universe in universes.values():
        if universe.entities_states:
            universe.send_message()

# if __name__ == "__main__":
#     with open("ehub_sample1.bin", "rb") as f:
#         data = f.read()
#         try:
#             parsed_message = decode_ehub_message(data)
#             print(f"Parsed message: {parsed_message}")
#         except ValueError as e:
#             print(f"Error parsing eHuB message: {e}")
        