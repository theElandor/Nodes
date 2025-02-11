from Nodes.Protocols.Protocol import Protocol
from Nodes.const import Command, State
from Nodes.messages import Message, LeaderElectionAFMessage
from Nodes.Nodes.RingNode import RingNode

class LeaderElectionAsFar(Protocol):
    def __init__(self, node: RingNode):
        assert isinstance(node, RingNode), "node has to be of type RingNode."
        super().__init__(node)

    def setup(self):
        self.state = State.ASLEEP
    
    def handle_message(self, message: Message) -> bool:
        command = message.command
        if command == Command.START_AT:
            command = self.node._start_at(message)
        if self.state == State.ASLEEP:
            if command == Command.WAKEUP:
                new_message = LeaderElectionAFMessage(Command.ELECTION, self.node.id, self.node.id)
                self.node.send_random(new_message)
                self.min = self.node.id
            else:
                self.min = self.node.id
                if message.origin < self.min:
                    new_message = LeaderElectionAFMessage(Command.ELECTION, self.node.id, message.origin)
                    self.node.send_to_other(message.sender, new_message)
                    self.min = message.origin
                else:
                    new_message = LeaderElectionAFMessage(Command.ELECTION, self.node.id, self.node.id)
                    self.node.send_to_other(message.sender, new_message)
            self.state = State.AWAKE
        elif self.state == State.AWAKE:
            if command == Command.ELECTION:
                if message.origin < self.min:
                    new_message = LeaderElectionAFMessage(Command.ELECTION, self.node.id, message.origin)
                    self.node.send_to_other(message.sender, new_message)
                    self.min = message.origin
                elif message.origin == self.min:
                    new_message = LeaderElectionAFMessage(Command.NOTIFY, self.node.id, message.origin)
                    self.node.send_to_other(message.sender, new_message)
                    self.state = State.LEADER
                    self.node.log(f"Elected {self.state}")
                    return True
            if command == Command.NOTIFY:
                new_message = LeaderElectionAFMessage(Command.NOTIFY, self.node.id, message.origin)
                self.node.send_to_other(message.sender, new_message)
                self.state = State.FOLLOWER
                self.node.log(f"Elected {self.state}")
                return True
            
    def cleanup(self):
        self.node._send_total_messages()