from Nodes.Protocols.Protocol import Protocol
from Nodes.const import Command, State
from Nodes.messages import Message, LeaderElectionAtwMessage
from Nodes.Nodes.RingNode import RingNode

class Count(Protocol):
    """Implementation of the count protocol."""
    
    def __init__(self, node: RingNode):
        assert isinstance(node, RingNode), "node has to be of type RingNode."
        super().__init__(node)
    
    def setup(self):
        self.state = State.ASLEEP
        self.count = 0
        self.leader = None
        
    def handle_message(self, message: Message) -> bool:
        command = message.command
        if command == Command.START_AT:
            command = self.node._start_at(message)

        if command == Command.WAKEUP:
            new_message = LeaderElectionAtwMessage(Command.FORWARD,1, self.node.id, self.node.id)
            self.node.send_random(new_message)
        elif message.command == Command.FORWARD:
            if message.origin == self.node.id:
                self.node.log(f"Received back my message! Nodes in network: {message.counter}")
                new_message = LeaderElectionAtwMessage(Command.END, message.counter, self.node.id, self.node.id)
                self.node.send_random(new_message)
                return True
            else:
                new_message = LeaderElectionAtwMessage(Command.FORWARD, message.counter+1, message.origin, self.node.id)
                self.node.send_to_other(message.sender,  new_message)
        elif message.command == Command.END:
            self.node.log(f"{message.origin} discovered that there are {message.counter} nodes in the network.")
            new_message = LeaderElectionAtwMessage(Command.END, message.counter, message.origin, self.node.id)
            self.node.send_to_other(message.sender, new_message)
            return True
        
    def cleanup(self):
        super().cleanup()
        self.node.send_total_messages()