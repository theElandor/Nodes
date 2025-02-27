from Nodes.Nodes.Node import Node
from Nodes.Protocols.Protocol import Protocol
from Nodes.const import Command, State
from Nodes.messages import Message, LeaderElectionAtwMessage

class RingNode(Node):
    """Node implementation specific to ring topologies."""
    
    def __init__(self, hostname: str, back_port: int, listen_port: int):
        super().__init__(hostname, back_port, listen_port)
        
    def send_to_other(self, sender: int, message: Message):
        """!Send message to the other node in the ring.

        @param sender (int): sender of the previous message. This primitive will
            send the message to the other neighbor.
        @param message (Message): message to send.

        @return None
        """
        for v, address in self.local_dns.items():
            if sender != v:
                self._send(message, address)
                break
        self.total_messages += 1