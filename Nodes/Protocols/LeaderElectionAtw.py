from Nodes.Protocols.Protocol import Protocol
from Nodes.const import Command, State
from Nodes.messages import Message, LeaderElectionAtwMessage
from Nodes.Nodes.RingNode import RingNode

class LeaderElectionAtwProtocol(Protocol):
    """!Implementation of the leader election protocol."""

    def __init__(self, node: RingNode):
        assert isinstance(node, RingNode), "node has to be of type RingNode."
        super().__init__(node)
    
    def setup(self):
        self.state = State.ASLEEP

    def _leader_election_atw_check(self):
        """!Primitive for leader_election algorithm."""

        self.node.log(f"Count: {self.count}")
        self.node.log(f"Ringsize: {self.ringsize}")
        self.node.log(f"Min: {self.min}")
        if self.count == self.ringsize:
            if self.node.id == self.min:
                self.state = State.LEADER
                new_message = LeaderElectionAtwMessage(Command.TERM, 1, self.node.id, self.node.id)
                self.node.send_random(new_message)
            else:
                self.state = State.FOLLOWER
            self.node.log(f"Elected {self.state}")

        
    def _leader_election_atw_initialize(self):
        """!Primitive for leader_election algorithm."""

        self.count = 1 #
        self.ringsize = 1 # measures
        self.known = False
        new_message = LeaderElectionAtwMessage(Command.ELECTION, 1, self.node.id, self.node.id)
        self.node.send_random(new_message)
        self.min = self.node.id


    def handle_message(self, message: Message) -> bool:
        command = message.command
        if command == Command.START_AT:
            command = self.node._start_at(message)
        if command == Command.TERM:
            if message.origin == self.node.id: self.node.log("Got back termination message.")
            else:
                new_message = LeaderElectionAtwMessage(Command.TERM,
                                                        message.counter+1,
                                                        message.origin,
                                                        self.node.id)
                self.node.send_to_other(message.sender, new_message)
            return True
        if self.state == State.ASLEEP:
            self._leader_election_atw_initialize()
            if command == Command.WAKEUP:
                self.state = State.AWAKE
                return False
            else:
                new_message = LeaderElectionAtwMessage(Command.ELECTION,
                                                        message.counter+1,
                                                        message.origin,
                                                        self.node.id)
                self.node.send_to_other(message.sender, new_message)
                self.min = min(self.min, message.origin)
                self.count += 1
                self.state = State.AWAKE
        elif self.state == State.AWAKE:
            if self.node.id != message.origin:
                new_message = LeaderElectionAtwMessage(Command.ELECTION,
                                                        message.counter+1,
                                                        message.origin,
                                                        self.node.id)
                self.node.send_to_other(message.sender, new_message)
                self.min = min(self.min, message.origin)
                self.count += 1
                if self.known:
                    self._leader_election_atw_check()
            else:
                self.ringsize = message.counter
                self.known = True
                self._leader_election_atw_check()

    def cleanup(self):
        self.node.log("Leader election protocol is done.")
        self.node._send_total_messages()