import networkx as nx
import utils
import sys
import matplotlib.pyplot as plt
import subprocess as sp
import socket
import pickle
import time
G = nx.Graph()
if len(sys.argv) != 2:
    raise ValueError('Please provide exactly one argument.')
N, edges = utils.read_graph(sys.argv[1])
print("Graph info")
print(f"Nodes: {N} \nEdges: {len(edges)}")
nodes = [x+1 for x in range(N)]
G.add_nodes_from(nodes)
G.add_edges_from(edges)
# nx.draw(G, pos = None, ax = None, with_labels = True,font_size = 20, node_size = 2000, node_color = 'lightgreen')
# plt.show()
# for each node, we must reserve a port
HOST = "localhost"
PORT = 65000
ports = [65432+x for x in range(N)] # one port for each node
# create a process for each node
# remember binding: (node, port) --> connections
DNS = {node:port for node,port in zip(G.nodes(), ports)}
print(DNS)
command = f"python3 client.py localhost {PORT} "
for port in ports:
    process = sp.Popen(f'start cmd /K {command+str(port)}', shell=True)
confirmation_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
confirmation_socket.bind(("", PORT))
ready_clients = 0
while 1: # wait for RDY messages
    data,addr = confirmation_socket.recvfrom(4096)
    command, target_port = data.decode("utf-8").split(" ")
    if command != "RDY":
        print("Something went wrong during initialization.")
        exit(0)
    else:
        print(f"{target_port} is ready!")
        ready_clients += 1
        if ready_clients == len(ports):
            print(f"All {ready_clients} clients are ready")
            break        
#send information to processes via socket datagram
for node, port in DNS.items():
    local_dns = utils.get_local_dns(DNS, node, list(G.edges(node)))
    print(local_dns)    
    message = str([node, list(G.edges(node))]).encode()    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(message, ("localhost", port))
    