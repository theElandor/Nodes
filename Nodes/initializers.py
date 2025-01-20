import networkx as nx
import Nodes.utils as utils
from Nodes.nodes import MessageListener
import subprocess as sp
import socket
from prettytable import PrettyTable
import os
import abc
import datetime
import queue
from datetime import timedelta
from Nodes.messages import Message
from Nodes.messages import SetupMessage, CountMessage, WakeUpMessage
from Nodes.messages import WakeupAllMessage


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
        ## path of the client file
        self.client:str = client
        ## Boolean
        self.shell:bool = shell
        ## Message queue to store incoming messages
        self.message_queue: queue.Queue = queue.Queue()

        if not log_path:
            self.log_path = os.path.join(os.path.split(self.client)[0], "logs")

        ## Initialize message listener
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)        
        self.s.bind(("", self.PORT))
        self.listener = MessageListener(self.s, self.message_queue)
        self.listener.start()

    def __str__(self):
        table = PrettyTable()
        table.field_names = ["Node", "Port"]
        for key, val in self.DNS.items():
            table.add_row([key, val])
        return table.__str__()
    
    def receive_message(self, timeout:float=None) -> Message:
        """!Get a message from the queue.
        
        @param timeout (int): How long to wait for the message.
        
        @return message (str): The message if one was received, None if timeout occured.        
        """
        try:
            return self.message_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def initialize_clients(self):
        """!Initialize all of the nodes of the graph.

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
        ready_clients = 0
        while 1: # wait for RDY messages
            data = self.receive_message()
            new_message = Message.deserialize(data)
            if new_message.command != "RDY":
                print(f"Something went wrong during initialization.")
                exit(0)
            else:
                print(f"{new_message.sender} is ready!")
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
        received_messages = 0
        counts = []
        while 1: # wait for RDY messages    
            data = self.receive_message()
            message = CountMessage.deserialize(data)
            counts.append(message.counter)
            received_messages += 1
            if received_messages == self.N:
                print(f"The protocol used {sum(counts)} messages!")
                break

    def setup_clients(self):
        """!Provide usefull information to nodes after initialization.

        This method sends to all of the nodes in the network
        the information needed to properly work. This includes:
        + The ID in the network;
        + The list of connections (edges) with neighboors (nodes);
        + The local dns that they need to comunicate to other nodes;
        + A boolean (True if logging on terminal, False to log on files)
        + The path of the experiment directory (needed for logging)
        """
        ready_clients = 0
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)        
        for node, port in self.DNS.items():
            local_dns = utils.get_local_dns(self.DNS, node, list(self.G.edges(node)))
            message = SetupMessage("SETUP", node, list(self.G.edges(node)), local_dns, self.shell, self.exp_path)
            s.sendto(message.serialize(), ("localhost", port))
            # capture confirmation message
        acks = 0
        while acks < len(self.DNS):
            try:
                data = self.receive_message()
                if not data: continue
                ans_message = Message.deserialize(data)
                if ans_message.command != "SOP":
                    print("Something went wrong during clients setup.")
                    break
                else:
                    print(f"{ans_message.sender} started the protocol!")
                    acks += 1
            except Exception as e:
                print(f"Error receiving ack from a node. {e}")
        if acks < len(self.DNS):
            print(f"Did not receive SOP message from some clients.\nReceived: {acks} messages")
        else:
            print(f"All {acks} clients started the protocol!")

    def wakeup(self, wake_up_node:int):
        """!Send the wake up message to a specific node to start the computation.

        @param wake_up_node (int): represents the ID of the node to wake up.

        @return None    
        """
        message = WakeUpMessage()
        wake_up_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        wake_up_socket.sendto(message.serialize(), ("localhost", self.DNS[wake_up_node]))
        
    def wakeup_all(self, delta:int):
        """!Send the absolute wakeup time to the nodes.
        
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
            message = WakeupAllMessage(year, month,day,hour, minute, second)
            wake_up_socket.sendto(message.serialize(), ("localhost", port))

