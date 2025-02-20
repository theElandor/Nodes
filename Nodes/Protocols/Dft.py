from Nodes.Nodes import Node
from Nodes.Protocols.Protocol import Protocol
from Nodes.messages import Message
from Nodes.const import Command, State

@Message.register
class DftMessageV(Message):
    def __init__(self, command, origin, sender):
        super().__init__(command, sender)
        self.origin = origin
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "origin": self.origin
        })
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(data["command"], data["origin"], data["sender"])

class Dft(Protocol):
    def __init__(self, node: Node):
        super().__init__(node)

    def visit(self):
        """!Primitive used during DFT protocol."""    
        if len(self.unvisited) > 0:
            next_node = self.unvisited.pop()
            new_message = DftMessageV(Command.FORWARD, self.node.id, self.node.id)
            #new_message = Message(Command.FORWARD, self.node.id)
            self.node.send_to(new_message, next_node)
            self.state = State.VISITED
            return False
        else:
            if not self.initiator:
                new_message = DftMessageV(Command.RETURN, self.node.id, self.node.id)
                #new_message = Message(Command.RETURN, self.node.id)
                self.node.send_to(new_message, self.entry)
            return True


    def setup(self):
        self.state = State.IDLE
        self.initiator = False
        self.entry = None
        self.tree_neigs = set()

    def handle_message(self, message: Message) -> bool:
        assert message.command != Command.START_AT, "This protocol supports only 1 initiator."
        if self.state == State.IDLE:
            if message.command == Command.WAKEUP:
                self.unvisited = set(self.node.get_neighbors(id_only=True))
                self.initiator = True
                self.node.log("I am the root!")
                return self.visit()
            elif message.command == Command.FORWARD:
                self.entry = message.sender
                self.unvisited = set(self.node.get_neighbors(id_only=True))
                self.unvisited.remove(self.entry)
                return self.visit()
        elif self.state == State.VISITED:
            if message.command == Command.FORWARD:
                self.unvisited.remove(message.sender)
                new_message = DftMessageV(Command.BACK_EDGE, self.node.id, self.node.id)
                #new_message = Message(Command.BACK_EDGE, self.node.id)
                self.node.send_to(new_message, message.sender)
            if message.command == Command.RETURN:
                self.tree_neigs.add(message.sender)
                return self.visit()
            if message.command == Command.BACK_EDGE:
                return self.visit()
            
    def cleanup(self):
        super().cleanup()
        self.node.send_total_messages()