from abc import ABC, abstractmethod
from typing import Any
from Nodes.messages import Message, TerminationMessage
from Nodes.Nodes.Node import Node
from Nodes.const import Command
import sys

def error_handler(func):
    """!Send to the initializer a error message in presence of failures."""
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            error_msg = f"Fatal error in node {self.node.id}: {str(e)}"
            self.node.log(error_msg)
            # Send error message to initializer
            error_message = TerminationMessage(Command.ERROR, error_msg, self.node.id)
            self._send(error_message, self.node.back)
            # Clean up resources
            self.cleanup()
            self.node.cleanup()
            sys.exit(1)
    return wrapper

class Protocol(ABC):
    """!Base class for all protocols."""
    
    def __init__(self, node: Node):
        self.node = node
        self.setup()
        self.node._send_start_of_protocol()

    @error_handler
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
    
    def cleanup(self):
        self.node._send_end_of_protocol()
        
