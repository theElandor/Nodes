import socket
import os
from art import text2art
import pause
from datetime import datetime
import threading
import queue
from typing import Optional
from Nodes.messages import Message, FloodingMessage
from Nodes.messages import CountMessage, SetupMessage
from Nodes.messages import LeaderElectionAtwMessage
from Nodes.messages import LeaderElectionAFMessage
from Nodes.messages import ControlledDistanceMessage

class MessageListener(threading.Thread):
    """!Thread that continuously listens for incoming messages and puts them in a queue."""
    
    def __init__(self, socket: socket.socket, message_queue: queue.Queue):
        """!Initialize the message listener thread.
        
        @param socket (socket): The socket to listen on.
        @param message_queue (queue): Queue to store received messages.

        @return None
        """
        super().__init__()
        self.socket = socket
        self.message_queue = message_queue
        self.running = True
        self.daemon = True  # Thread will exit when main program exits
        
    def run(self):
        """!Listen for messages."""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)  # Using standard buffer size
                self.message_queue.put(data)
            except socket.error:
                if self.running:  # Only log if we're still meant to be running
                    print("Socket error occurred in listener thread")
                    
    def stop(self):
        """Stop the listener thread."""
        self.running = False

class Node:    
    """!Main class, encapsulate foundamental primitives."""
    
    def __init__(self, HOSTNAME:str, BACK:int, PORT:int):
        """!Node base initializer.

        @param HOSTNAME (str): IP of the initalizer.
        @param BACK (int): Port where the initalizer is listening for confirmation.
        @param PORT (int): Port on which this node has to listen

        @return None
        """
        ## IP address of the node.
        self.HOSTNAME:str = HOSTNAME
        ## Port of the initializer (server).
        self.BACK:int = BACK
        ## Port used to receive messages.
        self.PORT:int = PORT
        ## Max length of messages.
        self.BUFFER_SIZE:int = 4096
        ## Flag to check if node is correctly setup.
        self.setup:bool = False
        ## Flag that indicates where to write output (terminal or log file).
        self.log_file:bool = None
        # Queue used by the listener to add incoming messages.
        self.message_queue: queue.Queue = queue.Queue()
        # Socket used by the node to receive messages.
        self.s:socket = None
        # Message listener that handles the message queue.
        self.listener:MessageListener = None
        ## True if node outputs on terminal, false to use log files.
        self.shell:bool = None
        # Unique ID of the Node.
        self.id:int = None
        # Connections of the node
        self.edges:dict = None
        ## DNS containing usefull ports and adresses to comunicate.        
        self.local_dns:dict = None
        ## Path to the log directory.
        self.exp_path:str = None
        ## Counts the number of messages sent during the execution of an algorithm.
        self.total_messages = 0

    def _print_info(self):
        """!Print basic informations about the node."""
        Art = Art=text2art(f"{self.id}",font='block',chr_ignore=True)
        self._log(Art)
        res = f"\nHostname: {self.HOSTNAME}\n"
        res += f"Invoker port: {self.BACK}\n"
        res += f"Listening on port {self.PORT}\n"
        if self.setup:
            res += (f"ID: {self.id}\n")
            res += (f"Edges: {self.edges}\n")
            res += (f"DNS: {self.local_dns}")
        self._log(res)

    def _log(self, message):
        """!Log function to either print on terminal or on a log file.

        @param message (str): message to print.

        @return None
        """
        if self.shell:
            print(message)
        else:
            if not self.log_file:
                path = os.path.join(self.exp_path, f"{self.id}.out")
                self.log_file = open(path, "a")
            self.log_file.write(message + "\n")

    def _get_neighbors(self):
        return [(key, val) for key, val in self.local_dns.items()]

    def send_RDY(self):
        """!Send RDY message to initializer.

        This method is used to send RDY message to the initializer,
        confirming that this node is ready to receive instructions.
        This method does not increment the total_message counter as
        this message is part of the initial handshake.

        @return None
        """
        message = Message("RDY", self.PORT)
        self._send(message, self.BACK)

    def bind_to_port(self):
        """!Create a socket where the node can listen for setup messages."""
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Accept UDP datagrams, on the given port, from any sender
        self.s.bind(("", self.PORT))
        self.listener = MessageListener(self.s, self.message_queue)
        self.listener.start()

    def wait_for_instructions(self):
        """!This method is used to start listening for setup messages.
        """
        if not self.s:
            print("You need to bind to a valid socket first!")
            return
        while 1:
            data = self.receive_message()
            if not data: continue
            try:
                new_message = SetupMessage.deserialize(data)
            except Exception as e:
                print(f"Error while deserializing message: {e}")
            ## Unique ID of the node.
            self.id = new_message.node
            self.edges = new_message.edges            
            self.local_dns = new_message.local_dns            
            self.shell = new_message.shell
            self.exp_path = new_message.exp_path
            self.setup = True
            self.reverse_local_dns = {}
            for key, val in self.local_dns.items():
                self.reverse_local_dns[val] = key
            return
    def _send(self, message:Message, port:int, log:bool=False):
        """Primitive to send messages.

        @param message (Message): message object to send
        @param port (int): target port
        @param log (bool): whether or not to write the operation on log file

        @return None
        """
        if log:
            self._log(f"Sending to: {self.reverse_local_dns[port]}) this message: {message}")
        forward_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        forward_socket.sendto(message.serialize(), ("localhost", port))

    def _send_random(self, message:str):
        """!Send given message to a random neighbor.
        
        @param message (str): message to send.        

        @return None
        """
        _, address = list(self.local_dns.items())[0]
        self._send(message, address)
        self.total_messages += 1

    def _send_to_all(self, message:Message, silent=False):
        """!Send given message to all neighbors.

        This primitive is used to send the given message to
        all neighbors.

        @param message (str): message to send.

        @return None
        """
        for v, address in self.local_dns.items():
            if not silent:
                self._log(str(message))
            self._send(message, address)
            self.total_messages += 1

    def _send_to_all_except(self,sender:int, message:Message, silent:bool=False):
        for v, address in self.local_dns.items():
            if v == sender: continue
            if not silent:
                self._log(str(message))
            self._send(message, address)
            self.total_messages += 1

    def _send_total_messages(self):
        """!Send total number of messages sent to the initializer."""
        message = CountMessage("COUNT",self.total_messages, self.id)
        self._send(message, self.BACK)

    def _send_start_of_protocol(self):
        """!Send SOP message to the initializer."""
        message = Message("SOP", self.PORT)
        self._send(message, self.BACK)

    def _wake_up_decoder(self, data):
        """!Decode the WAKEUP or START_AT message.

        This method offers a quick way to decode the WAKEUP or
        START_AT message, used for async or sync start.
        You should always call this method at the beginning of
        your protocol. Check leader_election_atw_protocol() as 
        an example.
        """
        command = eval(data)[0]
        if command == "WAKEUP":
            return command
        elif command == "START_AT":
            y, mo, d, h, mi, s = eval(data)[1:]
            pause.until(datetime(y, mo, d, h, mi, s))
            return "WAKEUP"  # from now on it's like I received a wakeup message
        
    def receive_message(self, timeout: Optional[float] =None) -> Optional[str]:
        """!Get a message from the queue.
        
        @param timeout (int): How long to wait for the message.
        
        @return message (str): The message if one was received, None if timeout occured.        
        """
        try:
            return self.message_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def cleanup(self):
        """!Cleanup resources before shutting down."""
        if self.listener:
            self.listener.stop()
        if self.s:
            self.s.close()
        if self.log_file:
            self.log_file.close()

            
    def flooding_protocol(self):
        """!Flood information across the network.

        Expected number of messages if there is a single initiator
        is 2m-(n-1).
        
        Message format: <command, sender>
        """
        self._send_start_of_protocol()
        self.state = "ASLEEP"
        while True:
            data = self.receive_message()
            if not data: continue
            try:
                message = Message.deserialize(data)
                self._log(f"Received {message.command}, sender: {message.sender}")
            except Exception as e:
                self._log(f"Error processing message: {e}")
                print("Here")
            if self.state == "ASLEEP":
                if message.command in ["WAKEUP", "I"]:
                    new_message = FloodingMessage("I", self.id)
                    if message.command == "WAKEUP": self._send_to_all(new_message)
                    else: self._send_to_all_except(message.sender, new_message)
                    self.state = "DONE"
                    self._log("Computation is DONE locally.")
                    break
                else: raise ValueError()
        self.cleanup()
        self._send_total_messages()

class RingNode(Node):
    """!Class that encapsulates primitives and protocols used in a Ring-shaped network.

    This class encapsulates primitives and protocols that only work on Ring Networks.
    Each protocol has its own method, and the primitives for that protocol have the
    same prefix.
    """
    
    def __init__(self, HOSTNAME, BACK, PORT):
        """!RingNode init function.
        """
        super().__init__(HOSTNAME, BACK, PORT)
        

    def _send_to_other(self, sender: int, message: str, silent=False):        
        """!Send given message to the "other" node.

        This primitive is used to send the given message to
        the only node in the local DNS which is != sender.
        This implies that the node only has 2 neighbors (RingNode structure)

        @param sender (Node): node to exclude.
        @param message (str): message to forward.

        @return None
        """        
        for v, address in self.local_dns.items():  # send message in other direction
            if sender != v:
                if not silent:
                    self._log(f"Sending to: {v}({address}) this message: "+str(message))
                self._send(message, address)
                break
        self.total_messages += 1

    def _send_back(self, sender: int, message: Message, silent=False):
        """!Primitive that sends given message the specified node.

        This primitive is basically the same as a standard _send,
        but it is more readable and automatically increases
        self.total_messages.

        @param sender (Node): target node.
        @param message (str): message to send.
        @return None
        """
        port = self.local_dns[sender]       
        if not silent:
            self._log(f"Sending to: {sender}({port}) this message: "+str(message))
        self._send(message, port)
        self.total_messages += 1

    def count_protocol(self):
        """!Count nodes in a ring-shaped network."""
        self._send_start_of_protocol()
        while True:
            data = self.receive_message()
            if not data: continue
            message = Message.deserialize(data)
            self._log(str(message))
            if message.command == "WAKEUP":
                new_message = LeaderElectionAtwMessage("FWD",1, self.id, self.id)
                self._send_random(new_message)
            elif message.command == "FWD":
                if message.origin == self.id:
                    self._log(f"Received back my message! Nodes in network: {message.counter}")
                    new_message = LeaderElectionAtwMessage("END", message.counter, self.id, self.id)
                    self._send_random(new_message)
                    break
                else:
                    new_message = LeaderElectionAtwMessage("FWD", message.counter+1, message.origin, self.id)
                    self._send_to_other(message.sender,  new_message)
            elif message.command == "END":
                self._log(f"{message.origin} discovered that there are {message.counter} nodes in the network.")
                new_message = LeaderElectionAtwMessage("END", message.counter, message.origin, self.id)
                self._send_to_other(message.sender, new_message)
                break
        self._send_total_messages()
        self.cleanup()
        
    def _leader_election_atw_initialize(self):
        """!Primitive for leader_election algorithm."""
        self.count = 1 #
        self.ringsize = 1 # measures
        self.known = False
        new_message = LeaderElectionAtwMessage("Election", 1, self.id, self.id)
        _, dest_port = self._get_neighbors()[0]
        self._send(new_message, dest_port) # need to manually increment the message count
        self.total_messages += 1
        self.min = self.id

    def _leader_election_atw_check(self):
        """!Primitive for leader_election algorithm."""
        self._log(f"Count: {self.count}")
        self._log(f"Ringsize: {self.ringsize}")
        self._log(f"Min: {self.min}")
        if self.count == self.ringsize:
            if self.id == self.min:
                self.state = "LEADER"
                new_message = LeaderElectionAtwMessage("TERM", 1, self.id, self.id)
                self._send_random(new_message)
            else:
                self.state = "FOLLOWER"
            self._log(f"Elected {self.state}")

    def leader_election_atw_protocol(self):
        """!Leader election: All the way version.
        
        Recommended message class: LeaderElectionAtwMessage
        """
        self._send_start_of_protocol()
        self.state = "ASLEEP"
        while True:
            data = self.receive_message()
            if not data: continue
            try: # generic message
                message = Message.deserialize(data)
                command = message.command
                sender = message.sender
            except Exception as e:
                self._log(f"Error in decoding incoming message. {e}")
            if command != "WAKEUP":
                origin = message.origin
                counter = message.counter
                self._log(f"Received {command}, origin: {origin}, sender: {sender}, counter: {counter}")
            else: # command or term
                self._log(f"Received {command}")
            if command == "TERM":
                if origin == self.id: self._log("Got back termination message.")
                else:
                    new_message = LeaderElectionAtwMessage("TERM", counter+1, origin, self.id)
                    self._send_to_other(sender, new_message)
                break
            if self.state == "ASLEEP":
                self._leader_election_atw_initialize()
                if command == "WAKEUP":
                    self.state = "AWAKE"
                    continue
                else:
                    new_message = LeaderElectionAtwMessage("Election", counter+1, origin, self.id)
                    self._send_to_other(sender, new_message)
                    self.min = min(self.min, origin)
                    self.count += 1
                    self.state = "AWAKE"
            elif self.state == "AWAKE":
                if self.id != origin:
                    new_message = LeaderElectionAtwMessage("Election", counter+1, origin, self.id)
                    self._send_to_other(sender, new_message)
                    self.min = min(self.min, origin)
                    self.count += 1
                    if self.known:
                        self._leader_election_atw_check()
                else:
                    self.ringsize = counter
                    self.known = True
                    self._leader_election_atw_check()
        self._send_total_messages()
        self.cleanup()
        
    def leader_election_AF_protocol(self):
        """!Leader election: "As Far as it can" version.

        Message format: <command, origin, sender>
        """
        self._send_start_of_protocol()
        self.state = "ASLEEP"
        while True:
            data = self.receive_message()
            if not data:continue
            try:
                message = Message.deserialize(data)
                command = message.command
                sender = message.sender
            except Exception as e:
                self._log(f"Error while decoding message: {e}")
            self._log(f"Received: {str(message)}")
            if command != "WAKEUP":
                origin = message.origin
            if self.state == "ASLEEP":
                if command == "WAKEUP":
                    new_message = LeaderElectionAFMessage("Election", self.id, self.id)
                    _, dest_port = self._get_neighbors()[0]
                    self._send(new_message, dest_port, log=True) # need to manually increment the message count
                    self.total_messages += 1
                    self.min = self.id
                else:
                    self.min = self.id
                    if origin < self.min:
                        new_message = LeaderElectionAFMessage("Election", self.id, origin)
                        self._send_to_other(sender, new_message)
                        self.min = origin
                    else:
                        new_message = LeaderElectionAFMessage("Election", self.id, self.id)
                        self._send_to_other(sender, new_message)
                self.state = "AWAKE"
            elif self.state == "AWAKE":
                if command == "Election":
                    if origin < self.min:
                        new_message = LeaderElectionAFMessage("Election", self.id, origin)
                        self._send_to_other(sender, new_message)
                        self.min = origin
                    elif origin == self.min:
                        new_message = LeaderElectionAFMessage("Notify", self.id, origin)
                        self._send_to_other(sender, new_message)
                        self.state = "LEADER"
                        self._log(f"Elected {self.state}")
                        break
                if command == "Notify":
                    new_message = LeaderElectionAFMessage("Notify", self.id, origin)
                    self._send_to_other(sender, new_message)
                    self.state = "FOLLOWER"
                    self._log(f"Elected {self.state}")
                    break
        self._send_total_messages()
        self.cleanup()

    def _leader_election_controlled_distance_initialize(self):
        """!Primtive for the controlled distance algorithm."""
        self.limit = 1
        self.count = 0 # back messages
        new_message = ControlledDistanceMessage("Forth", self.id, self.id, self.limit)
        self._send_to_all(new_message)

    def _leader_election_controlled_distance_process_message(self, origin:int, sender:int, limit:int):
        """!Primitive for the controlled distance algorithm.

        @param origin (int): generator of the message.
        @param sender (int): sender of the message.
        @param limit (int): hops left for this message.

        @return None
        """
        limit = limit - 1
        self._log(f"Process message received {limit}")
        if limit == 0:# end of travel
            new_message = ControlledDistanceMessage("Back", self.id, origin, -1)
            self._send_back(sender, new_message)
        else:
            new_message = ControlledDistanceMessage("Forth", self.id, origin, limit)
            self._send_to_other(sender, new_message)

    def _leader_election_controlled_distance_check(self, origin):
        """!Primitive for the controlled distance algorithm.

        @param origin (int): generator of the message.

        @return None
        """
        self.count += 1
        if self.count == 2:
            self.count = 0
            self.limit = 2 * self.limit
            new_message = ControlledDistanceMessage("Forth", origin, origin, self.limit)
            self._send_to_all(new_message)

    def leader_election_controlled_distance_protocol(self):
        """!Leader election: controlled_distance version.

        Message format: <command, origin, sender, limit>.
        In this case, the message has to bring the "hops left" information,
        since the protocol procedes in states.
        """
        self._send_start_of_protocol()
        self.state = "ASLEEP"
        while True:
            data = self.receive_message()
            if not data: continue
            try:  # generic message
                message = Message.deserialize(data)
                command = message.command
                sender = message.sender
            except Exception as e:
                self._log(f"Error while decoding message: {e}")
                break
            if command != "WAKEUP":
                origin = message.origin
                limit = message.limit
            self._log(f"Received: {str(message)}")
            if self.state == "ASLEEP":
                if command == "WAKEUP":
                    self.state = "CANDIDATE"
                    self._leader_election_controlled_distance_initialize()
                elif command == "Forth":
                    if origin < self.id:
                        self._leader_election_controlled_distance_process_message(origin, sender, limit)
                        self.state = "DEFEATED"
                    else:
                        self._leader_election_controlled_distance_initialize()
                        self.state = "CANDIDATE"
            elif self.state == "CANDIDATE":
                if command == "Forth":
                    if origin < self.id:
                        self._leader_election_controlled_distance_process_message(origin, sender, limit)
                        self.state = "DEFEATED"
                    elif origin == self.id:
                        # command origin sender limit
                        new_message = ControlledDistanceMessage("Notify", self.id, self.id, -1)
                        self._send_to_other(sender, new_message)
                        self.state = "LEADER"
                        self._log("Elected LEADER")
                        break
                if command == "Back":
                    if origin == self.id: # don't really know if this is necessary
                        self._leader_election_controlled_distance_check(origin)
            elif self.state == "DEFEATED":
                if command == "Forth":
                    self._leader_election_controlled_distance_process_message(origin, sender, limit)
                elif command == "Back":
                    new_message = ControlledDistanceMessage("Back", self.id, origin, -1)
                    self._send_to_other(sender, new_message)
                elif command == "Notify":
                    new_message = ControlledDistanceMessage("Notfy", self.id, origin, -1)
                    self._send_to_other(sender, new_message)
                    self.state = "FOLLOWER"
                    self._log("Elected FOLLOWER")
                    break
        self._send_total_messages()
        self.cleanup()
        
