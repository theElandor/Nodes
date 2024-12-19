import networkx as nx
import Nodes.utils as utils
import subprocess as sp
import socket
from prettytable import PrettyTable
import os
import abc

class Initializer(metaclass=abc.ABCMeta):
    def __init__(self, client:str, HOSTNAME:str, PORT:int, G:nx.Graph, shell=True, log_path=None):
        """
        Args:
            HOSTNAME (str): IP address of the initalizer.
            BACK (int): Port where the initializer is waiting for RDY messages.
            G (nx.Graph): Graph structure to build.
            shell (bool): Whether to use a new shell for each process. 
                - True: The command is executed through a shell (e.g., `cmd.exe` on Windows, `/bin/sh` on Unix).
                - False: The command is executed directly without a shell. 
                This is safer and more efficient but may cause issues with shell-specific commands.
        Returns:
            None            
        """
        self.HOSTNAME = HOSTNAME
        self.PORT = PORT
        self.BUFFER_SIZE = 4096
        self.G = G
        self.N = G.number_of_nodes()
        self.ports = [65432+x for x in range(self.N)] # one port for each node
        self.DNS = {node:port for node,port in zip(G.nodes(), self.ports)}
        self.client = client
        self.shell = shell
        if not log_path:
            self.log_path = os.path.join(os.path.split(self.client)[0], "logs")

    def __str__(self):
        table = PrettyTable()
        table.field_names = ["Node", "Port"]
        for key, val in self.DNS.items():
            table.add_row([key, val])
        return table.__str__()

    def initialize_clients(self):
        """ This method creates a process for each client (node), comunicating
        what is the port that they should use to wait for messages. Then,
        it waits for a confirmation message (RDY) from all of them.
        Args:
            None
        Returns:
            None
        """
        command = f"python3 {self.client} localhost {self.PORT} "        
        self.exp_path = utils.init_logs(self.log_path)
        for port in self.ports:
            if self.shell:
                process = sp.Popen(f'start cmd /K {command+str(port)}', stdout=sp.DEVNULL, stderr=sp.DEVNULL)
            else:
                full_command = ["python3", self.client, "localhost", str(self.PORT), str(port)]
                process = sp.Popen(full_command)        
        confirmation_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        confirmation_socket.bind(("", self.PORT))
        ready_clients = 0
        while 1: # wait for RDY messages
            data,addr = confirmation_socket.recvfrom(self.BUFFER_SIZE)
            command, target_port = eval(data.decode("utf-8"))
            if command != "RDY":
                print(f"Something went wrong during initialization.")
                exit(0)
            else:
                print(f"{target_port} is ready!")
                ready_clients += 1
                if ready_clients == len(self.ports):
                    print(f"All {ready_clients} clients are ready")
                    break
    
    def wait_for_number_of_messages(self):
        """Method that opens a socket to wait for a message from all nodes
        containing the number of messages sent by the node.
        If it obtains this information from all of the nodes, it prints the sum.
        Args:
            None
        Returns:
            None
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("", self.PORT))
        received_messages = 0
        counts = []
        while 1: # wait for RDY messages    
            data,_ = s.recvfrom(self.BUFFER_SIZE)
            _, messages = eval(data.decode("utf-8"))
            counts.append(int(messages))
            received_messages += 1
            if received_messages == self.N:
                print(f"The protocol used {sum(counts)}  messages!")
                break

    def setup_clients(self):
        """This method sends to all of the nodes in the network
        the information needed to properly work. This includes:
        + The ID in the network;
        + The list of connections (edges) with neighboors (nodes);
        + The local dns that they need to comunicate to other nodes;
        + A boolean (True if logging on terminal, False to log on files)
        + The path of the experiment directory (needed for logging)
        Args:
            None
        Returns:
            None
        """
        confirmation_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        confirmation_socket.bind(("", self.PORT))
        ready_clients = 0        
        for node, port in self.DNS.items():
            local_dns = utils.get_local_dns(self.DNS, node, list(self.G.edges(node)))
            message = str([node, 
                           list(self.G.edges(node)), 
                           local_dns, 
                           self.shell,
                           self.exp_path]).encode()
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)            
            s.sendto(message, ("localhost", port))            
            # capture confirmation message
            data,_ = confirmation_socket.recvfrom(self.BUFFER_SIZE)
            command, target_port = eval(data.decode("utf-8"))
            if command != "SOP":
                print("Something went wrong during clients setup.")
                exit(0)
            else:
                print(f"{target_port} started the protocol!")
                ready_clients += 1
        if ready_clients == len(self.ports):
            print(f"All {ready_clients} clients are ready")
        else:            
            print(f"Did not receive SOP message from some clients.\nReceived: {ready_clients} messages")
            exit(0)

    def wakeup(self, wake_up_node:int):
        """Method do send the wake up message to a specific node to start the computation.
        Args:
            wake_up_node (int): represents the ID of the node to wake up.
        Returns:
            None
        """
        message = str(["WAKEUP"]).encode()
        wake_up_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        wake_up_socket.sendto(message, ("localhost", self.DNS[wake_up_node]))
        pass
    def wakeup_all(self, delta:int):
        """
        Send the absolute wakeup time to the nodes.
        Args:
            delta (int): integer representing the absolute delta time to start the nodes.
        Returns:
            None
        """

        
