from Nodes.Protocols.Protocol import Protocol
from Nodes.const import Command, State
from Nodes.messages import Message
from Nodes.Nodes.Node import Node
import threading
import time

class BullyProtocol(Protocol):
    def __init__(self, node: Node):
        super().__init__(node)

    def setup(self):
        self.state = State.ASLEEP
        self.waiting = False
        self.role = None
        self._stop_event = threading.Event()        
        
    def wait(self, t:int=5):
        time_passed = 0
        while (not self._stop_event.is_set()) and time_passed < t:            
            time.sleep(0.1)
            time_passed += 0.1
        self.role = "LEADER" if time_passed >= t else "FOLLOWER"
        new_message = Message(Command.TERM, self.node.id)
        self.node.send_to_me(new_message)
            
    def broadcast(self):
        for ID in self.node.get_neighbors(id_only=True):
            if ID > self.node.id:                
                new_message = Message(Command.ELECTION, self.node.id)
                self.node.send_to(new_message, ID)
        #create the waiting thread
        if not self.waiting:
            self.waiting = True
            x1 = threading.Thread(target = self.wait)
            x1.start()
    
    def ack(self, target:int):
        new_message = Message(Command.REPLY, self.node.id)
        self.node.send_to(new_message, target)

    def handle_message(self, message: Message) -> bool:
        assert message.command != Command.START_AT, "This wakeup is not supported"
        if message.command == Command.WAKEUP:
            if self.state == State.ASLEEP:
                self.state = State.ACTIVE
                self.broadcast()
        elif message.command == Command.ELECTION:
            if self.state == State.DONE:
                pass
            elif self.state == State.ASLEEP:
                self.state = State.ACTIVE
                self.ack(message.sender)
                self.broadcast()
            elif self.state == State.ACTIVE:
                self.ack(message.sender)
            else:
                raise RuntimeError(f"Unexpected message-state combination. {message.command}-{self.state}")
        elif message.command == Command.REPLY:
            if self.state == State.ACTIVE:
                self.state = State.DONE
                self.node.log("I am follower")
                self._stop_event.set()
            elif self.state == State.DONE:
                pass
            else:
                raise RuntimeError(f"Unexpected message-state combination. {message.command}-{self.state}")
        elif message.command == Command.TERM:            
            self.node.log("Finished")
            self.node.log(self.role)
            return True
        else:
            raise RuntimeError(f"Unexpected message-state combination. {message.command}-{self.state}")            

    def cleanup(self):
        super().cleanup()
        self.node.send_total_messages()