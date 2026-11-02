import socket
import config

socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(
    b'{"type": "promote"}', (config.SYNC_HOST, config.PROMOTE_PORT))
print("promote sent")