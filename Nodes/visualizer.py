import socket
import queue
import threading
from Nodes.nodes import MessageListener
from Nodes.messages import Message
import networkx as nx
import matplotlib.pyplot as plt


class Visualizer(threading.Thread):
    """!Handle visualization of message passing.

    The initializer will take care of setting up the
    visualizer, and it tells the nodes to replicate every
    message, so that the visualizer can see the full network
    traffic. This class renders messages on the graph as
    they are received. For now, this class just renders
    the "command" field of the received messages.
    """
    
    def __init__(self, G:nx.Graph, port:int):
        """!Initialize visualizer."""

        super().__init__()
        self.running = True
        self.daemon = True
        self.PORT = port
        self.G = G
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(("", self.PORT))
        self.message_queue: queue.Queue = queue.Queue()
        self.listener = MessageListener(self.s, self.message_queue)
        self.listener.start()
        plt.switch_backend('TkAgg')
        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.pos = nx.spring_layout(self.G)
        self.message_display_time = 1000
        
    def receive_message(self, timeout:float=None) -> Message:
        """!Get a message from the queue.

        @param timeout (int): How long to wait for the message.

        @return message (str): The message if one was received, None if timeout occured.        
        """
        try:
            return self.message_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def visualize_message(self, message:Message):
        sender = message.payload.sender
        receiver = message.receiver
        command = message.payload.command
        self.ax.clear()
        nx.draw(self.G, self.pos, ax=self.ax, with_labels=True,
                node_color='lightblue', node_size=500, font_size=10)
        if sender in self.pos and receiver in self.pos:
            self.ax.annotate(command, 
                            xy=self.pos[receiver], xycoords='data',
                            xytext=self.pos[sender], textcoords='data',
                            arrowprops=dict(arrowstyle="->", color="red", lw=2),
                            fontsize=12, color="red")
        plt.draw()
        
    def run(self):
        """!Listen for messages and visualize in graph."""
        while self.running:
            data = self.receive_message()
            if not data: continue            
            try:
                message = Message.deserialize(data)                
                print(message)
                self.visualize_message(message)
            except Exception as e:
                print(f"Error processing message: {e}")
    
    def stop(self):
        """!Stop the listener thread."""
        self.running = False
        plt.close(self.fig)
        
