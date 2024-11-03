import networkx as nx
import utils
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
        self.BUFFER_SIZE = 4096
        self.G = G
        self.N = G.number_of_nodes()
        self.ports = [65432+x for x in range(self.N)] # one port for each node
        self.DNS = {node:port for node,port in zip(G.nodes(), self.ports)}

    def __str__(self):
        table = PrettyTable()
        table.field_names = ["Node", "Port"]
        for key, val in self.DNS.items():
            table.add_row([key, val])
        return table.__str__()

    def initialize_clients(self):
        """
        This method creates a process for each client (node), comunicating
        what is the port that they should use to wait for messages. Then,
        it waits for a confirmation message (RDY) from all of them.
        """
        command = f"python3 client.py localhost {self.PORT} "
        for port in self.ports:
            process = sp.Popen(f'start cmd /K {command+str(port)}', shell=True)
            print(command+str(port))
        confirmation_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        confirmation_socket.bind(("", self.PORT))
        ready_clients = 0
        while 1: # wait for RDY messages
            data,addr = confirmation_socket.recvfrom(self.BUFFER_SIZE)
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
        """
        This method should send to all of the nodes in the network
        the information needed to properly work. This includes:
        + The ID in the network;
        + The list of connections (edges) with neighboors (nodes);
        + The local dns that they need to comunicate to other nodes;
        """
        pass

    @abc.abstractmethod
    def wakeup(self, message:str):
        """
        Wakeup protocol: sends a wakeup message to one (of more) of
        the nodes in the network.
        """
        pass

class RingNetworkInitializer(Initializer):
    def __init__(self, HOSTNAME:str, PORT:int, G:nx.Graph):
        super().__init__(HOSTNAME, PORT, G)
    
    def setup_clients(self):
        for node, port in self.DNS.items():
            local_dns = utils.get_local_dns(self.DNS, node, list(self.G.edges(node)))
            message = str([node, list(self.G.edges(node)), local_dns]).encode()
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(message, ("localhost", port))

    def wakeup(self, wake_up_node:int, message:str):
        """
        Method do send the wake up message to a specific node to start the computation.
        Parameters:
            wake_up_node: integer representing the ID of the node to wake up.
            message: wake up message to send. It might vary based on the protocol.
        """
        wake_up_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        wake_up_socket.sendto(message, ("localhost", self.DNS[wake_up_node]))
    
    def wait_for_number_of_messages(self):
        """
        Methods that opens a socket to wait for a message from all nodes
        containing the number of messages sent by the node.
        If it obtains this information from all of the nodes, it prints the sum.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("", self.PORT))
        received_messages = 0
        counts = []
        while 1: # wait for RDY messages    
            data,addr = s.recvfrom(self.BUFFER_SIZE)            
            command, messages = eval(data.decode("utf-8"))
            counts.append(int(messages))
            received_messages += 1
            if received_messages == self.N:
                print(f"The protocol used {sum(counts)} number of messages to terminate computation!")
                break