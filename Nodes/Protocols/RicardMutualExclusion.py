from Nodes.Protocols.Protocol import Protocol
from Nodes.Nodes import Node
from Nodes.const import Command,State
from Nodes.messages import Message
import heapq
import threading
import time
import random

@Message.register
class MutualExclusionMessage(Message):
    def __init__(self, command,timestamp:int, sender):
        super().__init__(command, sender)
        self.timestamp = timestamp

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "timestamp": self.timestamp
        })
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(data["command"], data["timestamp"], data["sender"])
    
class RicardMutualExclusion(Protocol):
    """
    Ricard and Agrawala's mutual exclusion algorithm.
    It's an optimization of the Lamport's mutual exclusion. It avoids
    using the RELEASE messages, and instead uses REPLY messages only.
    The number of messages used is 2(n-1), while Lamport uses 3(n-1).
    This means that asyntotically ,the number of messages is the same.
    https://en.wikipedia.org/wiki/Ricart%E2%80%93Agrawala_algorithm
    """
    def __init__(self, node: Node, silent=False):
        """
        @param silent (bool): if set to False, disables the debugging prints.
        """
        self.silent = silent
        super().__init__(node)

    def request_CS(self, t:int):
        # request CS when I am IDLE
        while True:
            time.sleep(t)            
            if self.state in [State.REQUESTING, State.CS]:
                continue
            else:
                break
        self.LC += 1 #increment logical clock
        new_message = MutualExclusionMessage(Command.REQUEST, self.LC, self.node.id)
        self.received_replies.clear()
        self.state = State.REQUESTING
        self.current_request_lc = self.LC
        self.node.send_to_all(new_message)
    
    def access_CS(self):
        # ============== SIMULATE ACCESS TO CS ==============
        self.state = State.CS
        if not self.silent:
            print(f"{self.node.id} accessed CS...")
        t = random.randint(1,2)
        self.LC += 1 # increment logical clock
        time.sleep(t)
        if not self.silent:
            print(f"{self.node.id} released CS...")
        # ============== RELEASE CS ==============
        self.state = State.IDLE
        self.CS_counter += 1
        # instead of sending release, send REPLY to all delayed requests
        self.empty_delayed()
        # ================ TERM condition ================
        if self.CS_counter == 2:
            new_message = Message(Command.END, self.node.id)
            self.node.send_to_all(new_message, count=False)
    
    def empty_delayed(self):
        if len(self.delayed) == 0: return
        # pop all delayed requests and send REPLY messages
        for i in range(len(self.delayed)):
            message = self.delayed.pop(0)
            new_message = MutualExclusionMessage(Command.REPLY, self.LC, self.node.id)
            self.node.send_to(new_message, message.sender)

    def setup(self):
        random.seed((self.node.id +1)*32)
        self.LC = 0
        self.CS_counter = 0
        self.state = State.IDLE
        self.current_request_lc = -1
        
        self.received_replies = set()
        self.delayed = [] # stores delayed requests
        self.ends = set()

        t1 = random.randint(1,3)
        t2 = random.randint(5,8)
        if not self.silent:
            print(t1,t2)
        x1 = threading.Thread(target = self.request_CS, args=(t1,))
        x2 = threading.Thread(target = self.request_CS, args=(t2,))
        x1.start()
        x2.start()
    
    def access_check(self):
        if self.state != State.REQUESTING: return
        for node in self.node.get_neighbors(id_only=True):
            if node not in self.received_replies: return
        self.access_CS()

    def handle_message(self, message:Message) -> bool:
        assert message.command != Command.START_AT, "This protocol does not support simultaneous wakeup."
        assert message.command in [Command.REQUEST, Command.REPLY, Command.END], "Unknown message type."
        if message.command == Command.END:
            self.ends.add(message.sender)
            if len(self.ends) == len(self.node.get_neighbors(id_only=True)):
                return True
        else:
            self.LC = max(self.LC, message.timestamp)+1 # update logical clock
        if message.command == Command.REQUEST:
            # If I am in the critical section, delay the reply
            if self.state == State.CS:
                self.delayed.append(message)
            # If I am requesting, compare my current request timestamp with the one in the message
            elif self.state == State.REQUESTING:
                if self.current_request_lc == message.timestamp: # tie-breaker, use node id
                    if self.node.id < message.sender: # I win
                        self.delayed.append(message)
                    else: # I lose
                        new_message = MutualExclusionMessage(Command.REPLY, self.LC, self.node.id)
                        self.node.send_to(new_message, message.sender)
                elif self.current_request_lc < message.timestamp: # I win, so I just delay
                    self.delayed.append(message)
                else: # I lose, so I reply
                    new_message = MutualExclusionMessage(Command.REPLY, self.LC, self.node.id)
                    self.node.send_to(new_message, message.sender)
            elif self.state == State.IDLE:
                new_message = MutualExclusionMessage(Command.REPLY, self.LC, self.node.id)
                self.node.send_to(new_message, message.sender)
        elif message.command == Command.REPLY:
            self.received_replies.add(message.sender)
            self.access_check()
    def cleanup(self):
        super().cleanup()
        self.node.send_total_messages()