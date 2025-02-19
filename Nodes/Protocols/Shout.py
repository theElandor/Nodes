from Nodes.Protocols.Protocol import Protocol
from Nodes.messages import Message
from Nodes.const import Command, State
from Nodes.Nodes.Node import Node

class Shout(Protocol):
    def __init__(self, node: Node):
        super().__init__(node)

    def setup(self):
        self.state = State.IDLE        
        self.counter = None
        self.parent = None
        self.tree_neigs = set()

    def handle_message(self, message: Message) -> bool:
        assert message.command != Command.START_AT, "This protocol supports only 1 initiator."
        if self.state == State.IDLE:
            if message.command == Command.WAKEUP:                
                self.node.log("I am the root.")
                self.counter = 0
                self.state = State.ACTIVE
                self.node.send_to_all(Message(Command.Q, self.node.id))
            if message.command == Command.Q:
                self.node.log("I am a child.")
                self.parent = message.sender
                self.tree_neigs.add(message.sender)
                self.counter = 1
                self.node.send_to(Message(Command.YES, self.node.id), self.parent)
                if self.counter == len(self.node.get_neighbors()):
                    self.state = State.DONE
                    self.node.log("Computation Done.")
                    self.node.log(str(self.tree_neigs))
                    self.node.log(str(self.parent))
                    return True
                else:
                    self.node.send_to_all_except(message.sender, Message(Command.Q, self.node.id))
                    self.state = State.ACTIVE
        elif self.state == State.ACTIVE:
            if message.command == Command.Q:                
                self.node.send_to(Message(Command.NO, self.node.id), message.sender)
            if message.command == Command.YES:
                self.tree_neigs.add(message.sender)
                self.counter += 1
                if self.counter == len(self.node.get_neighbors()):
                    self.state = State.DONE
                    self.node.log("Computation Done.")
                    self.node.log(str(self.tree_neigs))
                    self.node.log(str(self.parent))
                    return True
            if message.command == Command.NO:
                self.counter += 1
                if self.counter == len(self.node.get_neighbors()):
                    self.state = State.DONE
                    self.node.log("Computation Done.")
                    self.node.log(str(self.tree_neigs))
                    self.node.log(str(self.parent))
                    return True

    def cleanup(self):
        self.node._send_total_messages()