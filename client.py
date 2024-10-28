import sys
import socket
import abc

class Node(metaclass=abc.ABCMeta):
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
            return
    @abc.abstractmethod
    def protocol(self):
        """
        Nodes should implement this method
        """
        pass

class RingNode(Node):
    def __init__(self, HOSTNAME, BACK, PORT):
        super().__init__(HOSTNAME, BACK, PORT)
    def protocol(self):
        while 1:
            msg = self.s.recv(self.BUFFER_SIZE)
            data = msg.decode("utf-8")
            origin, sender, counter = eval(data)
            print(f"Origin: {origin}, Sender: {sender}, Counter: {counter}")
            if origin == self.id and counter != 0:
                print(f"Received back my message! Nodes in network: {counter}")
                break    
            for v, address in self.local_dns.items(): # send message in other direction
                if sender != v:            
                    print(f"Sending to: {v}({address}) this message: {str([origin, self.id, int(counter)+1])}")
                    forward_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    forward_message = str([origin, self.id, int(counter)+1]).encode()
                    forward_socket.sendto(forward_message, ("localhost", address))
                    break
    
if len(sys.argv) != 4:
    raise ValueError('Please provide host, initializer PORT and port number.')
NODE = RingNode(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
NODE.send_RDY()
NODE.bind_to_port()
NODE.wait_for_instructions()
print(NODE)
NODE.protocol()