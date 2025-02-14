from Nodes.Protocols.Protocol import Protocol
from Nodes.messages import FloodingMessage, Message
from Nodes.const import Command, State

class Flooding(Protocol):
    """Implementation of the flooding protocol."""
    
    def __init__(self, node):
        super().__init__(node)
    
    def setup(self):        
        self.state = State.ASLEEP
        
    def handle_message(self, message: Message) -> bool:
        command = message.command
        if command == Command.START_AT:
            command = self.node._start_at(message)
            
        if self.state == State.ASLEEP:
            if command in [Command.WAKEUP, Command.INFORM]:
                new_message = FloodingMessage(Command.INFORM, self.node.id)
                if message.command == Command.WAKEUP:
                    self.node.send_to_all(new_message)
                else:
                    self.node.send_to_all_except(message.sender, new_message)
                self.state = State.DONE
                self.node.log("Computation is DONE locally.")
                return True
            else:
                raise ValueError()

    def cleanup(self):        
        self.node._send_total_messages()
    