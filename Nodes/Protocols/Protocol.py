from abc import ABC, abstractmethod
from typing import Any
from Nodes.messages import Message
from Nodes.Nodes.Node import Node

class Protocol(ABC):
    """!Base class for all protocols."""
    
    def __init__(self, node: Node):
        self.node = node
        self.setup()
        self.node._send_start_of_protocol()
    
    def run(self):
        """!Run the specified protocol."""        
        try:
            while True:
                data = self.node.receive_message()
                if not data:
                    continue
                try:
                    message = Message.deserialize(data)
                except Exception as e:
                    self.node.log("Error while deserializing message: {e}")
                    continue
                self.node.log(str(message))
                if self.handle_message(message):
                    break
        finally:
            self.cleanup()
            self.node.cleanup()

    @abstractmethod
    def setup(self):
        """!Setup protocol-specific state."""
        pass
    
    @abstractmethod
    def handle_message(self, message: Any) -> bool:
        """!Handle incoming message. Return True if computation is terminated."""
        pass
    
    @abstractmethod
    def cleanup(self):
        """!Cleanup protocol-specific resources."""
        pass
