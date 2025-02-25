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
            # Send error message to initializer
            error_message = TerminationMessage(Command.ERROR, error_msg, self.node.id)
            self.node.send_back(error_message)
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
        """!Main loop of the node that decodes messages."""
        try:
            while True:
                data = self.node.receive_message()
                if not data:
                    continue
                try:
                    message = Message.deserialize(data)
                    if message.command == Command.ERROR:
                        # received termination from server
                        self.node.log("Exiting since I decoded a error message from the initializer.")
                        exit(0)
                except Exception as e:
                    self.node.log("Error while deserializing message: {e}")
                    continue
                self.node.log(str(message))                
                # ========= FIFO mode check ===========
                # usually server-node messages have a Null Sender.
                # We want don't want to check those.
                if self.node.fifo and message.sender is not None:
                    sender_id = message.sender
                    if sender_id not in self.node.recv_sequence:
                        self.node.recv_sequence[sender_id] = 0
                    expected_sequence_number = self.node.recv_sequence[sender_id]
                    if message.seq_number != expected_sequence_number:
                        self.node.log(f"Out of order message received. Expected {expected_sequence_number}, got {message.seq_number}. Requeueing.")
                        # Put the message back in the queue for later processing
                        self.node.insert_message(data)
                        continue
                    else:
                        self.node.recv_sequence[sender_id] += 1
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
        """!Send end of protocol to the initializer.
        
        Override this method if you want more control on the cleanup phase,
        for example if you want to send some stats to the server at the 
        end of the computation.
        """
        self.node._send_end_of_protocol()
        
