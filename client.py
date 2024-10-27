import sys
import socket
import pickle
BUFFER_SIZE = 4096
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
    data = s.recv(BUFFER_SIZE)
    data = data.decode("utf-8")
    node, edges, local_dns = eval(data) # eval(data) is probably super unsafe
    print(f"Node: {node}")
    print(f"Edges: {edges}")
    print(f"DNS: {local_dns}")
    break
while 1:
    msg = s.recv(BUFFER_SIZE)
    data = msg.decode("utf-8")
    origin, sender, counter = eval(data)
    print(f"Origin: {origin}, Sender: {sender}, Counter: {counter}")
    if origin == node and counter != 0:
        print(f"Received back my message! Nodes in network: {counter}")
        break    
    for v, address in local_dns.items(): # send message in other direction
        if sender != v:            
            print(f"Sending to: {v}({address}) this message: {str([origin, node, int(counter)+1])}")
            forward_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            forward_message = str([origin, node, int(counter)+1]).encode()
            forward_socket.sendto(forward_message, ("localhost", address))
            break