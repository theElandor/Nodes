import networkx as nx
import Nodes.utils as utils
import subprocess as sp
import socket
from prettytable import PrettyTable
import os
import datetime
from datetime import timedelta
from Nodes.messages import *
from Nodes.comunication import ComunicationManager
from Nodes.visualizer import Visualizer
from Nodes.const import Command, VisualizerState


class Initializer(ComunicationManager):
    """!Sets up the network before the execution of the algorithm."""
    
    def __init__(self,
                 client: str,
                 HOSTNAME: str,
                 PORT: int,
                 G: nx.Graph,
                 shell=True,
                 log_path=None,
                 visualizer=False):        
        """!Initialize initializer.
        
        @param  HOSTNAME (str): IP address of the initalizer.
        @param  BACK (int): Port where the initializer is waiting for RDY messages.
        @param  G (nx.Graph): Graph structure to build.
        @param  shell (bool): Whether to use a new shell for each process. 
                - True: The command is executed through a shell
                    (e.g., `cmd.exe` on Windows, `/bin/sh` on Unix).
                - False: The command is executed directly without a shell. 
                    This is safer and more efficient but may cause issues with
                    shell-specific commands.
        @param visualizer (bool): turn on/off visualization
        @return None
        """
        super().__init__()
        self._HOSTNAME: str = HOSTNAME
        self._PORT: int = PORT
        self._G: nx.Graph = G
        self._ports: list = [65432+x for x in range(self.number_of_nodes())] # one port for each node        
        self._DNS: dict = {node:port for node,port in zip(G.nodes(), self.ports)}        
        self._client: str = client        
        self._shell: bool = shell
        
        if not log_path: self._log_path = os.path.join(os.path.split(self.client)[0], "logs")
        else: self._log_path = None

        self._s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)        
        self._s.bind(("", self.PORT))
        self.start_listener(self._s, self.message_queue)

        self._visualizer_port = None
        self._visualizer = None
        if visualizer:
            self._visualizer_port = self.ports[-1]+1
            self._visualizer = Visualizer(self.visualizer_port, self.G)
        
        self.initialize_clients()
        self.setup_clients()

    @property
    def HOSTNAME(self):
        """!Return server hostname."""
        return self._HOSTNAME
    
    @property
    def PORT(self):
        """!Return server listener port."""
        return self._PORT
    
    @property
    def G(self):
        """!Return network structure."""
        return self._G
    
    @property
    def ports(self):
        """!Return ports used by the client nodes."""
        return self._ports
    
    @property
    def DNS(self):
        """!Return DNS (nodeID : Port)"""
        return self._DNS
    
    @property
    def client(self):
        """!Return path to client file."""
        return self._client
    
    @property
    def shell(self):
        """!Return True if each node should get a separate terminal."""
        return self._shell
    
    @property
    def log_path(self):
        """!Return root path to log files."""
        return self._log_path
    
    @property
    def s(self):
        """!Return socket used by the server to send messages."""
        return self._s

    @property
    def visualizer_port(self):
        """!Return visualizer port if visualizer is active."""
        return self._visualizer_port
    
    @property
    def visualizer(self):
        """!Return visualizer if activated."""
        return self._visualizer
    

    def __str__(self):
        """!Convert node to string."""
        table = PrettyTable()
        table.field_names = ["Node", "Port"]
        for key, val in self.DNS.items():
            table.add_row([key, val])
        return table.__str__()
    
    def number_of_nodes(self) -> int:
        """Return number of nodes in the network."""
        return self.G.number_of_nodes()

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
                process = sp.Popen(f'start cmd /K {command+str(port)}',
                                   stdout=sp.DEVNULL,
                                   stderr=sp.DEVNULL)
            else:
                full_command = ["python3",
                                self.client,
                                "localhost",
                                str(self.PORT),
                                str(port)]
                process = sp.Popen(full_command)
        ready_clients = 0
        while 1: # wait for RDY messages
            data = self.receive_message()
            new_message = Message.deserialize(data)
            if new_message.command != Command.READY:
                print(f"Something went wrong during initialization.")
                exit(0)
            else:
                print(f"{new_message.sender} is ready!")
                ready_clients += 1
                if ready_clients == len(self.ports):
                    print(f"All {ready_clients} clients are ready")
                    break

    def wait_for_termination(self):
        """!Wait for termination messages by nodes in the network."""
        EOP_received = 0
        while 1: # wait for RDY messages    
            try:
                data = self.receive_message()
                message = TerminationMessage.deserialize(data)            
                if message.command == Command.END_PROTOCOL:
                    EOP_received += 1
                    if EOP_received == self.number_of_nodes():
                        print("Received EOP from all nodes in the network.")
                        break
                elif message.command == Command.ERROR:
                    payload = message.payload
                    print(f"A node crashed with the following error: {payload}")
                    self.send_termination()
                    exit(0)
                else:
                    # put the message back in the queue if it's not a termination message.
                    self.insert_message(data)
            except KeyboardInterrupt:
                self.send_termination()
    
    def wait_for_number_of_messages(self):
        """!Wait for message containing number of messages from nodes in the network."""
        counts_received = 0
        total_count = 0
        while 1: # wait for RDY messages            
            data = self.receive_message()
            message = CountMessage.deserialize(data)
            total_count += message.counter
            counts_received += 1
            if counts_received == self.number_of_nodes():
                print("Received message count from all nodes.")
                print(f"Total number of messages: {total_count}")
                return total_count
                

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
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for node, port in self.DNS.items():
            local_dns = utils.get_local_dns(self.DNS, node, list(self.G.edges(node)))
            message = SetupMessage(node,
                                   list(self.G.edges(node)),
                                   local_dns,
                                   self.shell,
                                   self.exp_path,
                                   self.visualizer_port,
                                   )
            s.sendto(message.serialize(), ("localhost", port))
            # capture confirmation message
        acks = 0
        while acks < len(self.DNS):
            try:
                data = self.receive_message()
                if not data: continue
                ans_message = Message.deserialize(data)
                if ans_message.command != Command.START_PROTOCOL:
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

    def send_termination(self):
        """!Send termination message to all of the nodes in the network."""        
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        termination_message = TerminationMessage(Command.ERROR, "node crash")
        for node, port in self.DNS.items():
            s.sendto(termination_message.serialize(), ("localhost", port))

    def start_visualization(self):
        """!Communicate to the visualizer to start the visualization loop."""
        assert self.visualizer, "Specify visualizer=True in the constructor to use this method."
        state = self.visualizer.start_visualization()
        if state == VisualizerState.INTERNAL_ERROR:
            print("Sending termination")
            self.send_termination()
            exit(0)
        elif state == VisualizerState.EXTERNAL_ERROR:
            # error is alredy being handled from server
            pass
        elif state == VisualizerState.SUCCESS:
            print("End of visualization.")            

    def close(self):
        """!Close the socket connection"""
        try:
            self.listener.stop()
            self.s.close()
            print("Socket successfully closed.")
        except Exception as e:
            print(f"Error closing socket: {e}")