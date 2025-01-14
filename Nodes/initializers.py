import networkx as nx
import Nodes.utils as utils
import subprocess as sp
import socket
from prettytable import PrettyTable
import os
import abc
import datetime
import pause
from datetime import timedelta

class Initializer(metaclass=abc.ABCMeta):
    def __init__(self, client:str, HOSTNAME:str, PORT:int, G:nx.Graph, shell=True, log_path=None):
        """!Initializer initializer :)
        
        @param  HOSTNAME (str): IP address of the initalizer.
        @param  BACK (int): Port where the initializer is waiting for RDY messages.
        @param  G (nx.Graph): Graph structure to build.
        @param  shell (bool): Whether to use a new shell for each process. 
                - True: The command is executed through a shell (e.g., `cmd.exe` on Windows, `/bin/sh` on Unix).
                - False: The command is executed directly without a shell. 
                This is safer and more efficient but may cause issues with shell-specific commands.
        @return None
        """
        ## Initializer node hostname.
        self.HOSTNAME:str = HOSTNAME
        ## Initializer port
        self.PORT:int = PORT
        ## Maximum buffer size
        self.BUFFER_SIZE:int = 4096
        ## Graph
        self.G:nx.Graph = G
        ## Number of nodes in the graph
        self.N:int = G.number_of_nodes()
        ## Available ports, one for each node of the graph
        self.ports:list = [65432+x for x in range(self.N)] # one port for each node
        ## DNS server holding tuples <node:port>
        self.DNS:dict = {node:port for node,port in zip(G.nodes(), self.ports)}
        ## path of the client size
        self.client:str = client
        ## Boolean
        self.shell:bool = shell
        if not log_path:
            self.log_path = os.path.join(os.path.split(self.client)[0], "logs")

    def __str__(self):
        table = PrettyTable()
        table.field_names = ["Node", "Port"]
        for key, val in self.DNS.items():
            table.add_row([key, val])
        return table.__str__()

    def initialize_clients(self):
        """!Method that initializes all of the nodes of the graph.

        This method creates a process for each client (node), comunicating
        what is the port that they should use to wait for messages. Then,
        it waits for a confirmation message (RDY) from all of them.    

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
        """!Wait for a message containing the number of messages from each node.

        Method that opens a socket to wait for a message from all nodes
        containing the number of messages sent by the node.
        If it obtains this information from all of the nodes, it prints the sum.
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
                print(f"The protocol used {sum(counts)} messages!")
                break

    def setup_clients(self):
        """!Method needed to provide usefull information to nodes after initialization.

        This method sends to all of the nodes in the network
        the information needed to properly work. This includes:
        + The ID in the network;
        + The list of connections (edges) with neighboors (nodes);
        + The local dns that they need to comunicate to other nodes;
        + A boolean (True if logging on terminal, False to log on files)
        + The path of the experiment directory (needed for logging)
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
            print(f"All {ready_clients} clients started the protocol!")
        else:            
            print(f"Did not receive SOP message from some clients.\nReceived: {ready_clients} messages")
            exit(0)

    def wakeup(self, wake_up_node:int):
        """!Method do send the wake up message to a specific node to start the computation.        

        @param wake_up_node (int): represents the ID of the node to wake up.

        @return None    
        """
        message = str(["WAKEUP"]).encode()
        wake_up_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        wake_up_socket.sendto(message, ("localhost", self.DNS[wake_up_node]))
    def wakeup_all(self, delta:int):
        """!Method that sends the absolute wakeup time to the nodes.
        
        Method needed to wakeup nodes all at once. The only way to do it is sync them
        with local clock, and wait for them to start up. Some algorithms perform worse
        in terms of number of messages when all nodes wakeup together.

        @param delta (int): integer representing the absolute delta time to start the nodes.
        
        @return None
        """
        wake_up_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        now = datetime.datetime.now()
        start_time = now + timedelta(seconds=delta)        
        year = start_time.year
        month = start_time.month
        day = start_time.day
        hour = start_time.hour
        minute = start_time.minute
        second = start_time.second
        for node, port in self.DNS.items():
            message = str(["START_AT", year, month,day,hour, minute, second]).encode()
            wake_up_socket.sendto(message, ("localhost", port))

