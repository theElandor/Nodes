import numpy as np
from Nodes.Protocols.Protocol import Protocol
from Nodes.const import Command,State
from Nodes.messages import Message
from Nodes.Nodes.Node import Node

@Message.register
class TensorMessage(Message):
    def __init__(self, command, array:list, sender):
        super().__init__(command, sender)
        self.array = np.array(array, dtype="float16")

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "array": self.array.tolist() 
            })
        return data

    @classmethod 
    def from_dict(cls, data):
        return cls(data["command"], data["array"], data["sender"])

class TensorParallel(Protocol):
    def __init__(self, node: Node):
        super().__init__(node)

    def setup(self):
        self.state = State.ASLEEP
        self.master = False 

    def handle_message(self, message:Message) -> bool:
        assert message.command != Command.START_AT, "You must wakeup only the master node." 
        assert message.command in [Command.WAKEUP]
        if self.state == State.ASLEEP:
            if message.command == Command.WAKEUP:
                self.master = True
                # send tensor pieces to other nodes
                # wait for answers from slaves
            elif message.command == "RECEIVE":
                # perform computation and send back
                pass
        return True
      

    def cleanup(self):
        super().cleanup()
        pass
