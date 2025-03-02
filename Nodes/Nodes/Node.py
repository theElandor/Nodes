
from datetime import datetime
import socket
import pause
from Nodes.comunication import ComunicationManager
from art import text2art
from Nodes.messages import *
import time
import os
import sys

class Node(ComunicationManager):
    """!Main class, encapsulate foundamental primitives."""
    
    def __init__(self, hostname:str, back:int, port:int, fifo=False):
        """!Node base initializer.

        @param HOSTNAME (str): IP of the initalizer.
        @param BACK (int): Port where the initalizer is listening for confirmation.
        @param PORT (int): Port on which this node has to listen

        @return None
        """
        super().__init__()        
        self._hostname:str = hostname        
        self._back:int = back
        self._port:int = port
        self._fifo:bool = fifo
        self._in_socket = None
        self._setup:bool = False                
        self._log_file:bool = None
        self._shell:bool = None
        self._id:int = None
        self._edges:dict = None
        self._local_dns:dict = None
        self._reverse_local_dns:dict = None
        self._exp_path:str = None
        self._visualizer_port = None
        self._total_messages = 0
        self._sleep_delay = 1
        # ========== parameters needed for fifo mode ========
        if fifo:
            self.send_sequence = {}
            self.recv_sequence = {}
        # ========== initialization sequence ================
        self.send_RDY()
        self.bind_to_port()
        self.wait_for_instructions()        

    @property
    def hostname(self):
        """!Return IP address of the node."""
        return self._hostname
    
    @property
    def fifo(self):
        return self._fifo
    
    @property
    def back(self):
        """!Return the port of the initializer (server)."""
        return self._back
    
    @property
    def port(self):
        """!Return the port used by the node to receive messages."""
        return self._port
    
    @property
    def in_socket(self):
        """!Return the socket used by the message receiver."""
        return self._in_socket

    @property
    def setup(self):
        """!Return True if the node is correctly setup."""
        return self._setup
    
    @property    
    def log_file(self):
        """!Return a reference to the log file."""
        return self._log_file    

    @property
    def shell(self):
        """!Return True if the node outputs on terminal."""
        return self._shell        

    @property
    def id(self):
        """!Return the unique ID of the node."""
        return self._id

    @property
    def edges(self):
        """!Return the connections of the node."""
        return self._edges
    
    @property
    def local_dns(self):
        """!Return the DNS of the node."""
        return self._local_dns
    
    @property
    def reverse_local_dns(self):
        """!Return the reverse DNS of the node."""
        return self._reverse_local_dns
    
    @property
    def exp_path(self):
        """!Return the path to the log directory."""
        return self._exp_path
    
    @property
    def visualizer_port(self):
        """!Return the port used by the visualizer."""
        return self._visualizer_port

    @property
    def total_messages(self):
        """!Return the total number of messages sent by the node."""
        return self._total_messages
    
    @total_messages.setter
    def total_messages(self, value):        
        assert value >= 0
        assert isinstance(value, int)
        self._total_messages = value
    
    @property
    def sleep_delay(self):
        return self._sleep_delay

    @sleep_delay.setter
    def sleep_delay(self, value):        
        assert value >= 0
        assert isinstance(value, int)
        self._sleep_delay = value
    

    def print_info(self):
        """!Print basic informations about the node."""
        Art = Art=text2art(f"{self.id}",font='block',chr_ignore=True)
        self.log(Art)
        res = f"\nHostname: {self.hostname}\n"
        res += f"Invoker port: {self.back}\n"
        res += f"Listening on port {self.port}\n"
        res += f"Fifo mode: {self.fifo}\n"
        if self.setup:
            res += (f"ID: {self.id}\n")
            res += (f"Edges: {self.edges}\n")
            res += (f"DNS: {self.local_dns}")
        self.log(res)

    def log(self, message:str):
        """!Log function to either print on terminal or on a log file.

        @param message (str): message to print.

        @return None
        """
        if self.shell:
            print(message)
        else:
            if not self.log_file:
                path = os.path.join(self.exp_path, f"{self.id}.out")
                self._log_file = open(path, "a")
            self.log_file.write(message + "\n")

    def get_neighbors(self, id_only=False) -> list:
        """!Return the neighboring nodes (tuple with id and port).
        
        @param id_only (bool): if set to True, it will return a list with
            only the IDs of the neighboring nodes.
        
        @return list
        """
        if not id_only:
            return [(key, val) for key, val in self.local_dns.items()]
        else:
            return list(self.local_dns.keys())

    def send_RDY(self):
        """!Send RDY message to initializer.

        This method is used to send RDY message to the initializer,
        confirming that this node is ready to receive instructions.
        This method does not increment the total_message counter as
        this message is part of the initial handshake.

        @return None
        """
        message = Message(Command.READY, self.port)
        self._send(message, self.back)

    def bind_to_port(self):
        """!Create a socket where the node can listen for setup messages."""
        
        self._in_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Accept UDP datagrams, on the given port, from any sender
        self._in_socket.bind(("", self.port))
        self.start_listener(self._in_socket, self.message_queue)
    
    def wait_for_instructions(self):
        """!This method is used to start listening for setup messages."""
        assert self.in_socket is not None, "You need to bind to a valid socket first!"
        while 1:
            data = self.receive_message()
            if not data: continue
            try:
                new_message = SetupMessage.deserialize(data)
            except Exception as e:
                print(f"Error while deserializing message: {e}")
            ## Unique ID of the node.
            self._id = new_message.node
            self._edges = new_message.edges
            self._local_dns = new_message.local_dns
            self._shell = new_message.shell
            self._exp_path = new_message.exp_path
            self._visualizer_port = new_message.visualizer_port
            self._setup = True
            self._reverse_local_dns = {}
            for key, val in self.local_dns.items():
                self.reverse_local_dns[val] = key
            return
            
    def _send(self, message: Message, port: int, log: bool=False):
        """!Primitive to send messages.

        @param message (Message): message object to send
        @param port (int): target port
        @param log (bool): whether or not to write the operation on log file

        @return None
        """
        if log:
            self.log(f"Sending to: {self.reverse_local_dns[port]}) this message: {message}")
        forward_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if port != self.back and self.visualizer_port:
            time.sleep(self.sleep_delay)
        # ============= additional information for FIFO mode ===============
        if self.fifo and port != self.back: # we only want to track node-node messages.
            target_id = self.reverse_local_dns[port]
            if target_id not in self.send_sequence:
                self.send_sequence[target_id] = 0
            
            message.seq_number = self.send_sequence[target_id]            
            self.send_sequence[target_id] += 1
        # ============= sending to target and visualizer if needed ============
        forward_socket.sendto(message.serialize(), ("localhost", port))
        # We want to replicate only node to node messages or error messages
        if self.visualizer_port:
            if port != self.back or (port == self.back and message.command == Command.ERROR):
                if port != self.back:
                    receiver = self.reverse_local_dns[port]
                else:
                    receiver = -1
                v_message = VisualizationMessage(message, receiver)
                forward_socket.sendto(v_message.serialize(), ("localhost", self.visualizer_port))

    def _send_eov(self):
        """!Send a termination message to the visualizer."""
        if not self.visualizer_port:
            return
        else:
            eov_message = EndOfVisualizationMessage()
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            v_message = VisualizationMessage(eov_message, -1)
            s.sendto(v_message.serialize(), ("localhost", self.visualizer_port))
            
    def send_random(self, message:Message):
        """!Send given message to the first neighbor in the DNS list.
        
        @param message (Message): message to send.        

        @return None
        """
        _, address = list(self.local_dns.items())[0]
        self._send(message, address)
        self.total_messages += 1

    def send_to(self, message: Message, target: int):
        """!Send a message to target node.
        @param message (Message): message to send.
        @param target (int): target node.

        @return None        
        """
        self._send(message, self.local_dns[target])
        self.total_messages += 1

    def send_back(self, message:Message):
        """!Send message back to initializer (server).
        @param message (Message): message to send.

        @return None
        """
        self._send(message, self.back)

    def send_to_all(self, message:Message):
        """!Send given message to all neighbors.

        This primitive is used to send the given message to
        all neighbors.

        @param message (Message): message to send.

        @return None
        """
        for v, address in self.local_dns.items():
            self._send(message, address)
            self.total_messages += 1

    def send_to_all_except(self, sender: int, message: Message):
        """!Send given message to all neighbors except the sender.
        
        @param sender (int): node to exclude.
        @param message (Message): message to send.

        @return None
        """
        for v, address in self.local_dns.items():
            if v == sender: continue            
            self._send(message, address)
            self.total_messages += 1
            
    def send_to_missing(self, senders: list, message: Message):
        """!Send given message to all neighbors except the ones in the list.
        
        @param senders (list): nodes to exclude
        @param message (Message): message to send

        @return None
        """
        s = set(senders)
        assert len(s) == len(senders)-1
        for v, address in self.local_dns.items():
            if v not in s:
                self._send(message, address)
                self.total_messages += 1

    def _send_end_of_protocol(self):
        """!Send termination message back to initializer at the end of the protocol."""
        message = TerminationMessage(Command.END_PROTOCOL, "", self.id)
        self._send(message, self.back)

    def send_total_messages(self):
        """!Send total number of messages sent to the initializer."""
        message = CountMessage(Command.COUNT_M,self.total_messages, self.id)
        self._send(message, self.back)

    def _send_start_of_protocol(self):
        """!Send SOP message to the initializer."""
        message = Message(Command.START_PROTOCOL, self.port)
        self._send(message, self.back)
    
    def _start_at(self, message:WakeupAllMessage):
        """!Decode the WAKEUP or START_AT message.

        This method offers a quick way to decode the WAKEUP or
        START_AT message, used for async or sync start.
        You should always call this method at the beginning of
        your protocol. Check leader_election_atw_protocol() as 
        an example.
        """
        pause.until(datetime(message.year,
                             message.month,
                             message.day,
                             message.hour,
                             message.minute,
                             message.second))
        return "WAKEUP"  # from now on it's like I received a wakeup message
        
    def cleanup(self):
        """!Cleanup resources before shutting down."""
        if self.listener:
            self.listener.stop()
        if self.in_socket:
            self.in_socket.close()
        if self.log_file:
            self.log_file.close()
        self._send_eov()