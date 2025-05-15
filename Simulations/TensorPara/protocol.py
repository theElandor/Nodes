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
    def __init__(self, node: Node, slaves:int):
        """
        @param slaves int: number of slaves available to the master node.
        """
        super().__init__(node)
        self.slaves = slaves

    def send_arrays(self):
        """
        This function is used by the master node to initialize:
        1) A random input tensor (x) which will be sent to every other node.
        2) N-1 random weight matrices that will be distributed among other slaves;
        # 6x6 * 6*4 -> 6x5
        # the 6x4 matrix will be split by columns (6x1, 6x1, ..., 6x1)
        # and each part will be given to a node.
        Args:
        @slaves int: number of slaves available to work. 
        """
        self.x = np.random.rand(6,self.slaves)
        self.W = np.random.rand(self.slaves,4)
        self.splits = [self.W[:,i] for i in range(self.slaves)]
    
    def inform_slaves(self):
        new_message = Message(Command.Q, self.node.id)
        self.node.send_to_all(new_message)


    def setup(self):
        self.state = State.ASLEEP
        self.master = False 
        self.ready_slaves = 0

    def handle_message(self, message:Message) -> bool:
        assert message.command != Command.START_AT, "Wakeup only the master node." 
        assert message.command in [Command.WAKEUP]
        if self.state == State.ASLEEP:
            if message.command == Command.WAKEUP:
                self.master = True
                self.inform_slaves()
                self.state = State.IDLE
                #self.init_array()
                # send tensor pieces to other nodes
                # wait for answers from slaves
            elif message.command == Command.Q:
                # I am a slave and I must notify my availability
                # to the master node
                new_message = Message(Command.REPLY, self.node.id)
                self.node.send_to(new_message, message.sender)
                self.state = State.IDLE
            elif message.command == "RECEIVE":
                # perform computation and send back
                pass
        elif self.state == State.IDLE and self.master:
            if message.command == Command.REPLY:
                self.ready_slaves += 1
                if self.ready_slaves == self.slaves:
                    self.state = "WAITING"
                    self.send_arrays()
        elif self.state == State.IDLE and not self.master:
            # we can only receive arrays from the master
            pass
        return True
      

    def cleanup(self):
        super().cleanup()
        pass
