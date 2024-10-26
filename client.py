import sys
import socket
import pickle
if len(sys.argv) != 4:
    raise ValueError('Please provide host, initializer PORT and port number.')
HOSTNAME, BACK, PORT =sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
print(f"Hostname: {HOSTNAME}")
print(f"Invoker port: {BACK}")
print(f"Listening on port {PORT}")

message = str(f"RDY {PORT}").encode()
confirmation_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
confirmation_socket.sendto(message, ("localhost", BACK))

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Accept UDP datagrams, on the given port, from any sender
s.bind(("", PORT))
while 1:
# Receive up to 1,024 bytes in a datagram
    data = s.recv(4096)
    data = data.decode("utf-8")
    print(data)