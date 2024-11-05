import socket

class Node:
    def __init__(self, HOSTNAME, BACK, PORT):
        """
        Paramters:
            HOSTNAME: (IP address) IP of the initalizer
            BACK: Port where the initalizer is listening for confirmation
            PORT: Port on which this node has to listen
        """
        self.HOSTNAME = HOSTNAME
        self.BACK = BACK
        self.PORT = PORT
        self.BUFFER_SIZE = 4096
        self.setup = False
    def __str__(self):
        res = ""
        res += f"Hostname: {self.HOSTNAME}\n"
        res += f"Invoker port: {self.BACK}\n"
        res += f"Listening on port {self.PORT}\n"
        if self.setup:
            res += (f"ID: {self.id}\n")
            res += (f"Edges: {self.edges}\n")
            res += (f"DNS: {self.local_dns}")            
        return res
    def _get_neighbors(self):
        return [(key,val) for key, val in self.local_dns.items()]
    def send_RDY(self):
        """
        This method will send a "RDY" message to the initializer,
        confirming that this node is ready to receive instructions.
        """
        message = str(f"RDY {self.PORT}").encode()
        confirmation_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        confirmation_socket.sendto(message, (self.HOSTNAME, self.BACK))
    def bind_to_port(self):
        """
        Method to create a socket where the node can listen for setup messages
        """
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Accept UDP datagrams, on the given port, from any sender
        self.s.bind(("", self.PORT))
    def wait_for_instructions(self):
        """
        This method is used to start listening for setup messages.
        """
        if not self.s:
            print("You need to bind to a valid socket first!")
            return
        while 1:
        # Receive up to 1,024 bytes in a datagram
            data = self.s.recv(self.BUFFER_SIZE)
            data = data.decode("utf-8")
            self.id, self.edges, self.local_dns = eval(data) # eval(data) is probably super unsafe
            self.setup = True # end of setup
            self.reverse_local_dns = {}
            for key, val in self.local_dns.items():
                self.reverse_local_dns[val] = key
            return
    def _send(self, message, port, log=False):
        if log:
            print(f"Sending to: {self.reverse_local_dns[port]}) this message: "+message)
        forward_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        forward_socket.sendto(message.encode(), ("localhost", port))
    def _create_message(self, *args):
        return str(list(args)) 
        

class RingNode(Node):
    def __init__(self, HOSTNAME, BACK, PORT):
        super().__init__(HOSTNAME, BACK, PORT)
        self.total_messages = 0

    def _send_to_other(self,sender:int, message:str, silent=False):
        """        
        Primitive that sends given message to the "other" node, so
        the only node in the local DNS which is != sender.
        This implies that the node only has 2 neighbors (RingNode structure)
        Parameters:
            sender: node to exclude
            message: message to forward
        """
        for v, address in self.local_dns.items(): # send message in other direction
            if sender != v:                
                if not silent:
                    print(f"Sending to: {v}({address}) this message: "+message)
                self._send(message, address)
                break
        self.total_messages += 1

    def _send_total_messages(self):
        message = self._create_message("Message_count", self.total_messages)        
        self._send(message, self.BACK)

    def count_protocol(self):
        """
        Simple distributed algorithm to count nodes in a ring network.
        """
        while 1:
            msg = self.s.recv(self.BUFFER_SIZE)
            data = msg.decode("utf-8")
            origin, sender, counter = eval(data)
            print(f"Origin: {origin}, Sender: {sender}, Counter: {counter}")
            if origin == self.id and counter != 0:
                print(f"Received back my message! Nodes in network: {counter}")
                break
            forward_message = str([origin, self.id, int(counter)+1])
            self._send_to_other(sender, forward_message)

    def _leader_election_atw_initialize(self):
        """
        Primitive for leader_election algorithm to initialize nodes.
        """
        self.count = 1 #         
        self.ringsize = 1 # measures
        self.known = False
        message = self._create_message("Election", self.id, self.id, 1)
        _, dest_port = self._get_neighbors()[0]        
        self._send(message, dest_port) # need to manually increment the message count
        self.total_messages += 1
        self.min = self.id

    def _leader_election_atw_check(self):
        """
        Primitive for leader_election algorithm.
        """
        print(f"Count: {self.count}")
        print(f"Ringsize: {self.ringsize}")
        print(f"Min: {self.min}")
        if self.count == self.ringsize:
            if self.id == self.min:
                self.state = "LEADER"
            else:
                self.state = "FOLLOWER"
            print(f"Elected {self.state}")
            self._send_total_messages()

    def leader_election_atw_protocol(self):
        """
        Leader election: All the way version
        Message format: <command, origin, sender, counter>
        """        
        self.state = "ASLEEP"
        while True:
            msg = self.s.recv(self.BUFFER_SIZE)
            data = msg.decode("utf-8")
            command,origin,sender,counter = eval(data)
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

    def leader_election_AF_protocol(self):
        """
        Leader election "As Far as it can" protocol.
        Message format: <command, origin, sender>
        """
        self.state = "ASLEEP"
        while True:
            msg = self.s.recv(self.BUFFER_SIZE)
            data = msg.decode("utf-8")
            command,origin,sender = eval(data)
            print(f"Received: {command}, origin: {origin}, sender: {sender}")
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
                        print(f"Elected {self.state}")
                        self._send_total_messages()
                if command == "Notify":
                    message = self._create_message("Notify", origin, self.id)
                    self._send_to_other(sender, message)
                    self.state = "FOLLOWER"
                    print(f"Elected {self.state}")
                    self._send_total_messages()
