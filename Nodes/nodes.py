import socket
import os
from art import text2art
import pause
from datetime import datetime
import threading
import queue
from typing import Optional

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
                message = data.decode("utf-8")
                self.message_queue.put(message)
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

        @return None
        """
        message = self._create_message("RDY", self.PORT)
        self._send(message, self.BACK)

    def bind_to_port(self):
        """!Create a socket where the node can listen for setup messages."""
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Accept UDP datagrams, on the given port, from any sender
        self.s.bind(("", self.PORT))

    def wait_for_instructions(self):
        """!This method is used to start listening for setup messages.
        """
        if not self.s:
            self._log("You need to bind to a valid socket first!")
            return
        while 1:
        # Receive up to 1,024 bytes in a datagram
            data = self.s.recv(self.BUFFER_SIZE)
            data = data.decode("utf-8")
            id, edges, local_dns, shell, exp_path = eval(data)
            ## Unique ID of the node.
            self.id = id
            self.edges = edges            
            self.local_dns = local_dns            
            self.shell = shell
            self.exp_path = exp_path
            self.setup = True
            self.reverse_local_dns = {}
            
            for key, val in self.local_dns.items():
                self.reverse_local_dns[val] = key
            return
    def _send(self, message, port, log=False):
        """!Primitive to send messages.

        Primitive to send given message to specified port. Make sure to increment
        the self.total_messages parameter by 1 if you use this inside your algorithm.

        @param message (str): message to send.
        @param port (int): target port.
        @param log (bool): weather or not to write the operation on log file.

        @return None
        """
        if log:
            self._log(f"Sending to: {self.reverse_local_dns[port]}) this message: "+message)
        forward_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        forward_socket.sendto(message.encode(), ("localhost", port))

    def _send_random(self, message:str):
        """!Primitive that sends given message to a random neighbor.
        @param message (str): message to send.

        @return None
        """
        _, address = list(self.local_dns.items())[0]
        self._send(message, address)
        self.total_messages += 1

    def _send_total_messages(self):
        """!Sends total number of messages sent to the initializer.
        """
        message = self._create_message("Message_count", self.total_messages)
        self._send(message, self.BACK)

    def _send_start_of_protocol(self):
        """!Sends SOP message to the initializer.
        """
        self.listener = MessageListener(self.s, self.message_queue)
        self.listener.start()
        message = self._create_message("SOP", self.PORT)
        self._send(message, self.BACK)

    def _create_message(self, *args):
        """!Utility function to wrap the message in a string.
        """
        return str(list(args))

    def _wake_up_decoder(self, data):
        """!Method used to decode the WAKEUP or START_AT message.

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
        self.total_messages = 0

    def _send_to_other(self, sender: int, message: str, silent=False):        
        """!Primitive that sends given message to the "other" node.

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
                    self._log(f"Sending to: {v}({address}) this message: "+message)
                self._send(message, address)
                break
        self.total_messages += 1

    def _send_to_both(self, message: str, silent=False):
        """!Primitive that sends given message to both neighbors.

        This primitive is used to send the given message to
        both connected nodes (neighbors).

        @param message (str): message to send.

        @return None
        """
        for v, address in self.local_dns.items():
            if not silent:
                self._log(f"Sending to: {v}({address}) this message: "+message)
                self._send(message, address)
                self.total_messages += 1

    def _send_back(self, sender: int, message: str, silent=False):
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
            self._log(f"Sending to: {sender}({port}) this message: "+message)
        self._send(message, port)
        self.total_messages += 1

    def count_protocol(self):
        """!Count nodes in a ring-shaped network."""        
        while 1:
            data = self.receive_message()
            if not data: continue
            origin, sender, counter = eval(data)
            self._log(f"Origin: {origin}, Sender: {sender}, Counter: {counter}")
            if origin == self.id and counter != 0:
                self._log(f"Received back my message! Nodes in network: {counter}")
                break
            forward_message = str([origin, self.id, int(counter)+1])
            self._send_to_other(sender, forward_message)

    def _leader_election_atw_initialize(self):
        """!Primitive for leader_election algorithm."""
        self.count = 1 #
        self.ringsize = 1 # measures
        self.known = False
        message = self._create_message("Election", self.id, self.id, 1)
        _, dest_port = self._get_neighbors()[0]
        self._send(message, dest_port) # need to manually increment the message count
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
                message = self._create_message("TERM", self.id, self.id, 1)
                self._send_random(message)
            else:
                self.state = "FOLLOWER"
            self._log(f"Elected {self.state}")

    def leader_election_atw_protocol(self):
        """!Leader election: All the way version.

        Message format: <command, origin, sender, counter>
        """
        self._send_start_of_protocol()
        self.state = "ASLEEP"
        while True:
            data = self.receive_message()
            if not data: continue
            try: # generic message
                command,origin,sender,counter = eval(data)
            except: # WAKEUP message
                command = self._wake_up_decoder(data)
            if command != "WAKEUP":
                self._log(f"Received {command}, origin: {origin}, sender: {sender}, counter: {counter}")
            else:
                self._log(f"Received {command}")
            if command == "TERM":
                if origin == self.id: self._log("Got back termination message.")
                else:
                    message = self._create_message("TERM", origin, self.id, counter+1)
                    self._send_to_other(sender, message)
                break
            if self.state == "ASLEEP":
                self._leader_election_atw_initialize()
                if command == "WAKEUP":
                    self.state = "AWAKE"
                    continue
                else:
                    message = self._create_message("Election", origin,self.id,counter+1)
                    self._send_to_other(sender, message)
                    self.min = min(self.min, origin)
                    self.count += 1
                    self.state = "AWAKE"
            elif self.state == "AWAKE":
                if self.id != origin:
                    message = self._create_message("Election", origin,self.id,counter+1)
                    self._send_to_other(sender, message)
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
            try:  # generic message
                command, origin, sender = eval(data)
            except:  # WAKEUP message
                command = self._wake_up_decoder(data)
            if command != "WAKEUP":
                self._log(f"Received: {command}, origin: {origin}, sender: {sender}")
            else:
                self._log(f"Received: {command}")
            if self.state == "ASLEEP":
                if command == "WAKEUP":
                    message = self._create_message("Election", self.id, self.id)
                    _, dest_port = self._get_neighbors()[0]
                    self._send(message, dest_port, log=True) # need to manually increment the message count
                    self.total_messages += 1
                    self.min = self.id
                else:
                    self.min = self.id
                    if origin < self.min:
                        message = self._create_message("Election", origin, self.id)
                        self._send_to_other(sender, message)
                        self.min = origin
                    else:
                        message = self._create_message("Election", self.id, self.id)
                        self._send_to_other(sender, message)
                self.state = "AWAKE"
            elif self.state == "AWAKE":
                if command == "Election":
                    if origin < self.min:
                        message = self._create_message("Election", origin, self.id)
                        self._send_to_other(sender, message)
                        self.min = origin
                    elif origin == self.min:
                        message = self._create_message("Notify", origin, self.id)
                        self._send_to_other(sender, message)
                        self.state = "LEADER"
                        self._log(f"Elected {self.state}")
                        break
                if command == "Notify":
                    message = self._create_message("Notify", origin, self.id)
                    self._send_to_other(sender, message)
                    self.state = "FOLLOWER"
                    self._log(f"Elected {self.state}")
                    break
        self._send_total_messages()
        self.cleanup()

    def _leader_election_controlled_distance_initialize(self):
        """!Primtive for the controlled distance algorithm."""
        self.limit = 1
        self.count = 0 # back messages
        message = self._create_message("Forth", self.id, self.id, self.limit)
        self._send_to_both(message)

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
            message = self._create_message("Back", origin, self.id, -1)
            self._send_back(sender, message)
        else:
            message = self._create_message("Forth", origin, self.id, limit)
            self._send_to_other(sender, message)

    def _leader_election_controlled_distance_check(self, origin):
        """!Primitive for the controlled distance algorithm.

        @param origin (int): generator of the message.

        @return None
        """
        self.count += 1
        if self.count == 2:
            self.count = 0
            self.limit = 2 * self.limit
            message = self._create_message("Forth", origin, origin, self.limit)
            self._send_to_both(message)

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
                command, origin, sender, limit = eval(data)
            except: # WAKEUP message
                command = self._wake_up_decoder(data)
            if command != "WAKEUP":
                self._log(f"Received: {command}, origin: {origin}, sender: {sender}, limit:{limit}")
            else:
                self._log(f"Received: {command}")
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
                        message = self._create_message("Notify", self.id, self.id, -1)
                        self._send_to_other(sender, message)
                        self.state = "LEADER"
                        self._log("Elected LEADER")
                        break
                if command == "Back":
                    if origin == self.id:
                        self._leader_election_controlled_distance_check(origin)
            elif self.state == "DEFEATED":
                if command == "Forth":
                    self._leader_election_controlled_distance_process_message(origin, sender, limit)
                elif command == "Back":
                    message = self._create_message("Back", origin, self.id, -1)
                    self._send_to_other(sender, message)
                elif command == "Notify":
                     message = self._create_message("Notify", origin, self.id, -1)
                     self._send_to_other(sender, message)
                     self.state = "FOLLOWER"
                     self._log("Elected FOLLOWER")
                     break
        self._send_total_messages()
        self.cleanup()
        
