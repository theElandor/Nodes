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
    
class LamportMutualExclusion(Protocol):
    """
    In this simulation, each node wants to have access twice to the 
    critical section. To simulate this, in the setup phase, each node
    starts two threads that perform 1) wait random time 2) send request
    for 2 times. Each node when granted the access to the critical section
    starts a thread that waits for X seconds and sends the release at
    the end of the waiting time, simulating access to the critical section.
    With Lamport's mutual exclusion algorithm, nodes should be able to coordinate
    to not access the CS at the same time.
    https://www.cs.fsu.edu/~xyuan/cop5611/lecture8.html
    """
    def __init__(self, node: Node, silent=False):
        """
        @param silent (bool): if set to False, disables the debugging prints.
        """
        self.silent = silent
        super().__init__(node)

    def request_CS(self, t:int):
        time.sleep(t)
        self.LC += 1 #increment logical clock
        new_message = MutualExclusionMessage(Command.REQUEST, self.LC, self.node.id)
        heapq.heappush(self.CS_requests, (self.LC, self.node.id))
        self.node.send_to_all(new_message)
    
    def access_CS(self):
        self.using_CS = True
        if not self.silent:
            print(f"{self.node.id} accessed CS...")
        t = random.randint(1,2)
        self.LC += 1 # increment logical clock
        time.sleep(t)
        if not self.silent:
            print(f"{self.node.id} released CS...")
        self.using_CS = False
        self.CS_counter += 1
        new_message = MutualExclusionMessage(Command.RELEASE, self.LC, self.node.id)
        heapq.heappop(self.CS_requests) # top element is my request if I accessed the resource
        self.node.send_to_all(new_message)
        if self.CS_counter == 2:
            new_message = Message(Command.END, self.node.id)
            self.node.send_to_all(new_message, count=False)

    def setup(self):
        random.seed((self.node.id +1)*32)
        self.LC = 0
        self.CS_counter = 0
        self.using_CS = False
        # priority queue used to store CS requests
        self.CS_requests = []
        # stores Reply and Release messages from other nodes
        self.history = {n:[] for n in self.node.get_neighbors(id_only=True)}
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
        if len(self.CS_requests) == 0:
            return
        heapq.heapify(self.CS_requests)
        top_timestamp, top_id = self.CS_requests[0]
        if top_id != self.node.id: return
        for node, timestamps in self.history.items():
            largers = [t for t in timestamps if t > top_timestamp]
            if len(largers) == 0: return
        # if we found at least 1 larger timestamps in every list, access
        self.access_CS()

    def handle_message(self, message:Message) -> bool:
        assert message.command != Command.START_AT, "This protocol does not support simultaneous wakeup."
        assert message.command in [Command.REQUEST, Command.RELEASE, Command.REPLY, Command.END], "Unknown message type."
        if message.command == Command.END:
            self.ends.add(message.sender)
            if len(self.ends) == len(self.node.get_neighbors(id_only=True)):
                return True
        else:
            self.LC = max(self.LC, message.timestamp)+1 # update logical clock
        if message.command == Command.REQUEST:        
            heapq.heappush(self.CS_requests, (message.timestamp, message.sender))
            if not self.using_CS:
                new_message = MutualExclusionMessage(Command.REPLY, self.LC, self.node.id)
                self.node.send_to(new_message, message.sender)
        if message.command == Command.RELEASE:
            # If I receive a release, then for sure the coresponding request
            # is the top of the priority queue
            self.history[message.sender].append(message.timestamp)
            heapq.heappop(self.CS_requests)
            self.access_check()
        if message.command == Command.REPLY:
            self.history[message.sender].append(message.timestamp)
            self.access_check()

    def cleanup(self):
        super().cleanup()
        self.node.send_total_messages()