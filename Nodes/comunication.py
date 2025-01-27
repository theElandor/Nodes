from Nodes.messages import Message
from Nodes.message_handler import MessageListener
import socket
import queue


class ComunicationManager:
    """!Encapsulate comunication utilities."""
    
    def __init__(self):
        # Queue used by the listener to add incoming messages.
        self.message_queue: queue.Queue = queue.Queue()
        # Message listener that handles the message queue.
        self.listener: MessageListener = None        
    
    def receive_message(self, timeout: float = None, Q: queue.Queue = None) -> Message:
        """!Get a message from the queue.
        
        @param timeout (int): How long to wait for the message.
        
        @return message (str): The message if one was received, None if timeout occured.        
        """
        if not Q:
            Q = self.message_queue
        try:
            return Q.get(timeout=timeout)
        except Q.Empty:
            return None
        
    def start_listener(self, s: socket.socket, message_queue: queue.Queue):
        self.listener = MessageListener(s, message_queue)
        self.listener.start()
