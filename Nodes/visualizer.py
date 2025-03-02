from Nodes.comunication import ComunicationManager
import matplotlib.pyplot as plt
import socket
import networkx as nx
from Nodes.messages import Message, VisualizationMessage
from Nodes.const import Command, VisualizerState

class Visualizer(ComunicationManager):
    def __init__(self, port: int, G: nx.Graph):
        super().__init__()
        self._PORT = port
        self._G = G
        self._s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._s.bind(("", self.PORT))
        self.start_listener(self.s, self.message_queue)
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(12, 10))
        self.pos = nx.spring_layout(self.G)
        self._eov_received = 0
    
    @property
    def PORT(self) -> int:
        """!Get the port number of the visualizer."""
        return self._PORT
    
    @property
    def G(self) -> nx.Graph:
        """!Get the graph that the visualizer is visualizing."""
        return self._G
    
    @property
    def s(self) -> socket.socket:
        """!Get the socket used by the visualizer."""
        return self._s
    

    def _visualize_queue(self, cycle) -> VisualizerState:
        """!Visualize all messages in the queue at the same time.
        
        This function processes all messages in the queue and draws them on the plot.
        It will draw an arrow from the sender to the receiver for each message.
        This method will also display the command of the message next to the arrow.

        @param cycle: The current cycle of the visualization

        @return None
        """        
        colors = ["red", "blue"]        
        # Clear the plot before drawing all messages
        self.ax.clear()
        # Draw the base graph
        nx.draw(self.G, self.pos, ax=self.ax, with_labels=True,
                node_color='lightblue', node_size=300, font_size=22)

        # Process all messages in the queue
        while not self.message_queue.empty():
            data = self.message_queue.get()  # Get the next message from the queue
            try:
                message = Message.deserialize(data)  # Deserialize the message
                print(f"Processing message: {message}, Queue size: {self.message_queue.qsize()}")

                # Extract sender, receiver, and command from the message
                sender = message.payload.sender
                receiver = message.receiver
                command = message.payload.command
                if command == Command.ERROR:
                    print("Received an error message. Terminating the protocol.")
                    return VisualizerState.EXTERNAL_ERROR
                if command == "EOV":
                    print("Received End of Visualization.")
                    self._eov_received += 1
                    print(self._eov_received, len(self.G))
                    if self._eov_received == len(self.G):
                        plt.draw()
                        plt.pause(0.2)  # Pause briefly to allow the plot to update
                        return VisualizerState.SUCCESS
                    continue
                origin = message.payload.origin

                # Draw the message as an arrow from sender to receiver
                if sender in self.pos and receiver in self.pos:
                    self.ax.annotate(command+f" {origin}",
                                        xy=self.pos[receiver], xycoords='data',
                                        xytext=self.pos[sender], textcoords='data',
                                        arrowprops=dict(arrowstyle="->", color=colors[cycle % len(colors)], lw=2),
                                        fontsize=16, color="red")

            except Exception as e:
                print(f"Error processing message: {e}")
                return VisualizerState.INTERNAL_ERROR
        # Display the final plot with all messages
        plt.draw()
        plt.pause(0.2)  # Pause briefly to allow the plot to update
        return VisualizerState.CONTINUE

    def start_visualization(self) -> VisualizerState:
        """!Start the visualization of the messages in the queue.

        @return current_state: The current state of the visualization
        """
        cycle = 0
        while True:
            if not self.message_queue.empty():  # Only update the plot if there are messages in the queue
                self.ax.clear()  # Clear the plot before redrawing
                current_state = self._visualize_queue(cycle)
                if current_state == VisualizerState.CONTINUE:
                    cycle += 1
                else:
                    return current_state
        