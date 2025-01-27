import pickle
from Nodes.const import Command

class Message:    
    """!Basic Message Class. All messages should inherit from this class."""
    
    def __init__(self, command:str, sender:int=None):
        self.command = command
        self.sender = sender

    def serialize(self) -> bytes:
        """!Serialize to bytes before network transmission."""
        return pickle.dumps(self)
    
    @staticmethod
    def deserialize(data):
        """!Deserialize data. Used to decode incoming messages."""
        return pickle.loads(data)
        
    def __str__(self):
        return f"{self.command} from {self.sender} "

class WakeUpMessage(Message):
    """!Message used from the initializer to wakeup nodes."""
    
    def __init__(self, command="WAKEUP", sender:int=None):
        super().__init__(command, sender)

    def __str__(self):
        return super().__str__()

class WakeupAllMessage(Message):    
    """!Message used to wake up all nodes at the same time."""
    
    def __init__(self, year, month, day, hour, minute, second, command:str="START_AT", sender=None):
        super().__init__(command, sender)
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        
    def __str__(self):
        rep = super().__str__()
        rep += f"y:{self.year}, mo:{self.month}, d:{self.day}, h:{self.hour}, mi:{self.minute}, s:{self.second}"
        return rep
    
class FloodingMessage(Message):
    """!Message Used in the flooding protocol."""
    
    def __init__(self, command, sender:int=None, origin:int=None, counter:int=None):
        super().__init__(command, sender)
        self.origin = origin
        self.counter = counter
    
    def __str__(self):
        return super().__str__() + f"Origin: {self.origin}, Counter: {self.counter}"
    
class SetupMessage(Message):
    """!Message used by the initializer during the setup procedure."""
    
    def __init__(self, command:str,
                 node:int,
                 edges:list,
                 local_dns:dict,
                 shell:bool,
                 exp_path:str,
                 visualizer_port:int=None,
                 sender:int=None):
        super().__init__(command, sender)
        self.node = node
        self.edges = edges
        self.local_dns = local_dns
        self.shell = shell
        self.exp_path = exp_path
        self.visualizer_port = visualizer_port
    
    def __str__(self):
        return super().__str__() + f"{self.edges}\n{self.local_dns}\n{self.shell}\n{self.exp_path}\n{self.visualizer_port}"

class CountMessage(Message):
    """!Message used in the count protocol."""
    
    def __init__(self, command, counter, sender:int=None):
        super().__init__(command, sender)
        self.counter = counter
    def __str__(self):
        return super().__str__() + f"Sender: {self.sender}, Counter: {self.counter}"

class LeaderElectionAtwMessage(Message):
    """!Message used in the leader election all the way protcol."""
    
    def __init__(self, command:str, counter:int, origin:int, sender:int):
        super().__init__(command, sender)
        self.counter = counter
        self.origin = origin

    def __str__(self):
        rep = super().__str__()
        rep += f"Command: {self.command}, Sender:{self.sender}, "
        rep += f"Origin: {self.origin}, Counter:{self.counter}"
        return rep

class LeaderElectionAFMessage(Message):
    """!Message used in the leader election "as far as it can" protocol."""
    
    def __init__(self, command:str, sender, origin:int):
        super().__init__(command, sender)
        self.origin = origin
    def __str__(self):
        rep = super().__str__()
        rep += f"Origin: {self.origin}"
        return rep
    
class ControlledDistanceMessage(Message):
    """!Message used in the leader election controlled distance protocol."""
    
    def __init__(self, command:str, sender:int, origin:int, limit:int):
        super().__init__(command, sender)
        self.origin = origin
        self.limit = limit

    def __str__(self):
        rep = super().__str__()
        rep += f" Origin: {self.origin} "
        rep += f" Limit: {self.limit}"
        return rep

class VisualizationMessage(Message):
    """!Message used in the leader election controlled distance protocol."""
    def __init__(self, payload:Message, receiver:int):
        super().__init__("VIS", payload.sender)
        self.payload = payload
        self.receiver = receiver

    def __str__(self):
        rep = str(self.payload)
        rep += f" Receiver: {self.receiver} "
        return rep
