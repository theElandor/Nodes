from Nodes.comunication import ComunicationManager
import matplotlib.pyplot as plt
import socket
import networkx as nx
from Nodes.messages import Message, VisualizationMessage
from Nodes.const import Command, VisualizerState

class Visualizer(ComunicationManager):
    def __init__(self, port: int, G: nx.Graph):
        super().__init__()
        self.PORT = port
        self.G = G
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(("", self.PORT))
        self.start_listener(self.s, self.message_queue)
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(12, 10))
        self.pos = nx.spring_layout(self.G)
        self._eov_received = 0        
        
    def _visualize_queue(self, cycle) -> VisualizerState:
        colors = ["red", "blue"]
        """!Visualize all messages in the queue at the same time."""
        # Clear the plot before drawing all messages
        self.ax.clear()

        # Draw the base graph
        nx.draw(self.G, self.pos, ax=self.ax, with_labels=True,
                node_color='lightblue', node_size=300, font_size=10)

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
                        return VisualizerState.SUCCESS
                    continue
                origin = message.payload.origin

                # Draw the message as an arrow from sender to receiver
                if sender in self.pos and receiver in self.pos:
                    self.ax.annotate(command+f" {origin}",
                                        xy=self.pos[receiver], xycoords='data',
                                        xytext=self.pos[sender], textcoords='data',
                                        arrowprops=dict(arrowstyle="->", color=colors[cycle % len(colors)], lw=2),
                                        fontsize=8, color="red")

            except Exception as e:
                print(f"Error processing message: {e}")
                return VisualizerState.INTERNAL_ERROR
        # Display the final plot with all messages
        plt.draw()
        plt.pause(0.1)  # Pause briefly to allow the plot to update
        return VisualizerState.CONTINUE

    def start_visualization(self) -> VisualizerState:
        cycle = 0
        while True:
            if not self.message_queue.empty():  # Only update the plot if there are messages in the queue
                self.ax.clear()  # Clear the plot before redrawing
                current_state = self._visualize_queue(cycle)
                if current_state == VisualizerState.CONTINUE:
                    cycle += 1
                else:
                    return current_state
        