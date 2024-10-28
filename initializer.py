import networkx as nx
import utils
import sys
import subprocess as sp
import socket
from prettytable import PrettyTable
import abc

class Initializer(metaclass=abc.ABCMeta):
    def __init__(self, HOSTNAME:str, PORT:int, G:nx.Graph):
        """
        Paramters:
            HOSTNAME: (IP address) IP of the initalizer
            BACK: Port where the initializer is waiting for RDY messages
            G: Graph structure to build
        """
        self.HOSTNAME = HOSTNAME
        self.PORT = PORT
        self.G = G
        self.ports = [65432+x for x in range(N)] # one port for each node
        self.DNS = {node:port for node,port in zip(G.nodes(), self.ports)}
    def __str__(self):
        table = PrettyTable()
        table.field_names = ["Node", "Port"]
        for key, val in self.DNS.items():
            table.add_row([key, val])
        return table.__str__()
    def initialize_clients(self):
        command = f"python3 client.py localhost {self.PORT} "
        for port in self.ports:
            process = sp.Popen(f'start cmd /K {command+str(port)}', shell=True)
            print(command+str(port))
        confirmation_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        confirmation_socket.bind(("", self.PORT))
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
                if ready_clients == len(self.ports):
                    print(f"All {ready_clients} clients are ready")
                    break
    @abc.abstractmethod
    def setup_clients(self):
        pass

    @abc.abstractmethod
    def wakeup(self):
        pass

class RingNetworkInitializer(Initializer):
    def __init__(self, HOSTNAME:str, PORT:int, G:nx.Graph):
        super().__init__(HOSTNAME, PORT, G)
    
    def setup_clients(self):
        for node, port in self.DNS.items():
            local_dns = utils.get_local_dns(self.DNS, node, list(G.edges(node)))
            message = str([node, list(G.edges(node)), local_dns]).encode()
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(message, ("localhost", port))

    def wakeup(self):
        WUN = 3
        message = str([3, -1, 0]).encode()
        wake_up_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        wake_up_socket.sendto(message, ("localhost", self.DNS[WUN]))

G = nx.Graph()
if len(sys.argv) != 2:
    raise ValueError('Please provide exactly one argument.')
N, edges = utils.read_graph(sys.argv[1])
print("Graph info")
print(f"Nodes: {N} \nEdges: {len(edges)}")
nodes = [x+1 for x in range(N)]
G.add_nodes_from(nodes)
G.add_edges_from(edges)
# for each node, we must reserve a port
init = RingNetworkInitializer("localhost", 65000, G)
print(init)
init.initialize_clients()
init.setup_clients()
init.wakeup()