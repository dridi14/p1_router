# import socket

# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# sock.bind(('', 5568))  

# print("Listening for eHuB messages...")
# while True:
#     data, addr = sock.recvfrom(65535)
#     print(f"Received {len(data)} bytes from {addr}")
#     print(data)
#     break
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', 5568))

print("Listening for eHuB messages...")

while True:
    data, addr = sock.recvfrom(65535)
    print(f"Received {len(data)} bytes from {addr}")

    # Save to file for later testing
    with open("ehub_sample.bin", "wb") as f:
        f.write(data)
    print("Message saved to ehub_sample.bin")
    break
