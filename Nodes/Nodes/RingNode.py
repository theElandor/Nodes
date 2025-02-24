from Nodes.Nodes.Node import Node
from Nodes.Protocols.Protocol import Protocol
from Nodes.const import Command, State
from Nodes.messages import Message, LeaderElectionAtwMessage

class RingNode(Node):
    """Node implementation specific to ring topologies."""
    
    def __init__(self, hostname: str, back_port: int, listen_port: int):
        super().__init__(hostname, back_port, listen_port)
        
    def send_to_other(self, sender: int, message: Message, silent: bool = False):
        """Send message to the other node in the ring."""
        for v, address in self.local_dns.items():
            if sender != v:
                if not silent:
                    self.log(f"Sending to: {v}({address}) this message: {message}")
                self._send(message, address)
                break
        self.total_messages += 1