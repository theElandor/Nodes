from Nodes.Protocols.Protocol import Protocol
from Nodes.const import Command, State
from Nodes.messages import Message, ControlledDistanceMessage
from Nodes.Nodes.RingNode import RingNode

class LeaderElectionControlledDistance(Protocol):
    def __init__(self, node: RingNode):
        assert isinstance(node, RingNode), "node has to be of type RingNode."
        super().__init__(node)

    def setup(self):
        self.state = State.ASLEEP
        
    def _leader_election_controlled_distance_initialize(self):
        """!Primtive for the controlled distance algorithm."""        
        self.limit = 1
        self.count = 0 # back messages
        new_message = ControlledDistanceMessage(Command.FORTH, self.node.id, self.node.id, self.limit)
        self.node.send_to_all(new_message)

    def _leader_election_controlled_distance_process_message(self, origin:int, sender:int, limit:int):
        """!Primitive for the controlled distance algorithm.

        @param origin (int): generator of the message.
        @param sender (int): sender of the message.
        @param limit (int): hops left for this message.

        @return None
        """
        limit = limit - 1
        self.node.log(f"Process message received {limit}")
        if limit == 0:# end of travel
            new_message = ControlledDistanceMessage(Command.BACK, self.node.id, origin, -1)
            self.node.send_back(sender, new_message)
        else:
            new_message = ControlledDistanceMessage(Command.FORTH, self.node.id, origin, limit)
            self.node.send_to_other(sender, new_message)

    def _leader_election_controlled_distance_check(self, origin:int):
        """!Primitive for the controlled distance algorithm.

        @param origin (int): generator of the message.

        @return None
        """
        self.count += 1
        if self.count == 2:
            self.count = 0
            self.limit = 2 * self.limit
            new_message = ControlledDistanceMessage(Command.FORTH, origin, origin, self.limit)
            self.node.send_to_all(new_message)

    def handle_message(self, message: Message) -> bool:
        command = message.command
        if command == Command.START_AT:
            command = self.node._start_at(message)

        if self.state == State.ASLEEP:
            if command == Command.WAKEUP:
                self.state = State.CANDIDATE
                self._leader_election_controlled_distance_initialize()
            elif command == Command.FORTH:
                if message.origin < self.node.id:
                    self._leader_election_controlled_distance_process_message(message.origin,
                                                                                message.sender,
                                                                                message.limit)
                    self.state = State.DEFEATED
                else:
                    self._leader_election_controlled_distance_initialize()
                    self.state = State.CANDIDATE
        elif self.state == State.CANDIDATE:
            if command == Command.FORTH:
                if message.origin < self.node.id:
                    self._leader_election_controlled_distance_process_message(message.origin,
                                                                                message.sender,
                                                                                message.limit)
                    self.state = State.DEFEATED
                elif message.origin == self.node.id:
                    new_message = ControlledDistanceMessage(Command.NOTIFY, self.node.id, self.node.id, -1)
                    self.node.send_to_other(message.sender, new_message)
                    self.state = State.LEADER
                    self.node.log("Elected LEADER")
                    return True
            if command == Command.BACK:
                if message.origin == self.node.id: # don't really know if this is necessary
                    self._leader_election_controlled_distance_check(message.origin)
        elif self.state == State.DEFEATED:
            if command == Command.FORTH:
                self._leader_election_controlled_distance_process_message(message.origin,
                                                                            message.sender,
                                                                            message.limit)
            elif command == Command.BACK:
                new_message = ControlledDistanceMessage(Command.BACK, self.node.id, message.origin, -1)
                self.node.send_to_other(message.sender, new_message)
            elif command == Command.NOTIFY:
                new_message = ControlledDistanceMessage(Command.NOTIFY, self.node.id, message.origin, -1)
                self.node.send_to_other(message.sender, new_message)
                self.state = State.FOLLOWER
                self.node.log("Elected FOLLOWER")
                return True            
            
    def cleanup(self):
        super().cleanup()
        self.node.send_total_messages()