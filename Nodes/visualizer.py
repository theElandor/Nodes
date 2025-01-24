import socket
from Nodes.nodes import MessageListener

class Visualizer:
    """!Handle visualization of message passing.

    The initializer will take care of setting up the
    visualizer, and it tells the nodes to replicate every
    message, so that the visualizer can see the full network
    traffic. This class renders messages on the graph as
    they are received. For now, this class just renders
    the "command" field of the received messages.
    """
    
    def __init__(self, port:int):
        """!Initialize visualizer."""
        
        self.PORT = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(("", self.PORT))
        self.listener = MessageListener(self.s, self.message_queue)
        self.listener.start()
    
