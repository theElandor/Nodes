import threading
import socket
import queue


class MessageListener(threading.Thread):
    """!Thread that continuously listens for incoming messages and puts them in a queue."""    

    def __init__(self, socket: socket.socket, message_queue: queue.Queue):
        """!Initialize the message listener thread.
        
        @param socket (socket): The socket to listen on.
        @param message_queue (queue): Queue to store received messages.

        @return None
        """
        super().__init__()
        self.socket = socket
        self.message_queue = message_queue
        self.running = True
        self.daemon = True  # Thread will exit when main program exits
        
    def run(self):
        """!Listen for messages."""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)  # Using standard buffer size
                self.message_queue.put(data)
            except socket.error:
                if self.running:  # Only log if we're still meant to be running
                    print("Socket error occurred in listener thread")
                    
    def stop(self):
        """Stop the listener thread."""
        self.running = False
