import json
from Nodes.const import Command

class Message:    
    """!Basic Message Class. All messages should inherit from this class."""
    
    def __init__(self, command:str, sender:int=None):
        self.command = command
        self.sender = sender

    def to_dict(self) -> dict:
        """Convert message to dictionary for JSON serialization."""
        return {
            "type": self.__class__.__name__,
            "command": self.command,
            "sender": self.sender
        }

    def serialize(self) -> bytes:
        """!Serialize to bytes before network transmission."""
        return json.dumps(self.to_dict()).encode('utf-8')
    
    def deserialize(data: bytes):
        """Deserialize JSON data into appropriate message type."""
        json_data = json.loads(data.decode('utf-8'))
        msg_type = json_data.pop("type")
        # Get the appropriate message class
        msg_class = globals()[msg_type]
        return msg_class.from_dict(json_data)
    
    @classmethod
    def from_dict(cls, data: dict):
        """!Create message instance from dictionary."""
        return cls(data["command"], data["sender"])
        
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

    def to_dict(self):
        """!Update the base dictionary with message-specific paramters"""
        data = super().to_dict()
        data.update({
            "year": self.year,
            "month": self.month,
            "day": self.day,
            "hour": self.hour,
            "minute": self.minute,
            "second": self.second
        })
        return data
        
    @classmethod
    def from_dict(cls, data):
        return cls(
            data["year"], data["month"], data["day"],
            data["hour"], data["minute"], data["second"],
            data["command"], data["sender"]
        )
    
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

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "origin": self.origin, 
            "counter": self.counter
        })
        return data
    
    @classmethod
    def from_dict(cls, data):
        return cls(data["command"], data["sender"], data["origin"], data["counter"])
    
    def __str__(self):
        return super().__str__() + f"Origin: {self.origin}, Counter: {self.counter}"
    
class SetupMessage(Message):
    """!Message used by the initializer during the setup procedure."""
    
    def __init__(self,
                 node:int,
                 edges:list,
                 local_dns:dict,
                 shell:bool,
                 exp_path:str,
                 visualizer_port:int=None,
                 sender:int=None,
                 command:str=Command.SETUP):
        super().__init__(command, sender)
        self.node = node
        self.edges = edges
        self.local_dns = local_dns
        self.shell = shell
        self.exp_path = exp_path
        self.visualizer_port = visualizer_port
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "node": self.node,
            "edges": self.edges,
            "local_dns": self.local_dns,
            "shell": self.shell,
            "exp_path": self.exp_path,
            "visualizer_port": self.visualizer_port
        })
        return data

    @classmethod
    def from_dict(cls, data):
        # fix json converting everything to string
        local_dns = {int(key):val for key, val in data["local_dns"].items()}
        return cls(
            data["node"], data["edges"], local_dns,
            data["shell"], data["exp_path"], data["visualizer_port"],
            data["sender"], data["command"]
        )    

    def __str__(self):
        return super().__str__() + f"{self.edges}\n{self.local_dns}\n{self.shell}\n{self.exp_path}\n{self.visualizer_port}"

class CountMessage(Message):
    """!Message used in the count protocol."""
    
    def __init__(self, command, counter, sender:int=None):
        super().__init__(command, sender)
        self.counter = counter

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "counter": self.counter
        })
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(data["command"], data["counter"], data["sender"])

    def __str__(self):
        return super().__str__() + f"Sender: {self.sender}, Counter: {self.counter}"


# TODO
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

# TODO
class LeaderElectionAFMessage(Message):
    """!Message used in the leader election "as far as it can" protocol."""
    
    def __init__(self, command:str, sender, origin:int):
        super().__init__(command, sender)
        self.origin = origin
    def __str__(self):
        rep = super().__str__()
        rep += f"Origin: {self.origin}"
        return rep
    
# TODO
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
    def __init__(self, payload: Message, receiver: int):
        super().__init__("VIS", payload.sender)
        self.payload = payload
        self.receiver = receiver

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "payload": self.payload.to_dict(),
            "receiver": self.receiver
        })        
        return data
    
    @classmethod
    def from_dict(cls, data):
        payload_data = data["payload"]
        payload_type = globals()[payload_data["type"]]
        payload = payload_type.from_dict(payload_data)
        return cls(payload, data["receiver"])
    
    def __str__(self):
        rep = str(self.payload)
        rep += f" Receiver: {self.receiver} "
        return rep

# TODO
class MinFindingMessage(Message):
    """!Message used in the count protocol."""
    
    def __init__(self, command, value: int, sender:int=None):
        super().__init__(command, sender)
        self.value = value
        
    def __str__(self):
        return super().__str__() + f"Sender: {self.sender}, Counter: {self.counter}"
    
# TODO
class EndOfVisualizationMessage(Message):
    """!Message used to terminate the live visualization."""
    
    def __init__(self, command="EOV", sender:int = None):
        super().__init__(command, sender)
        
    def __str__(self):
        return super().__str__()

class TerminationMessage(Message):
    """!Termination message used by nodes to comunicate end of computation."""
    def __init__(self, command:str, payload:str, sender:int = None):
        super().__init__(command, sender)
        self.command = command
        self.payload = payload

    def to_dict(self) ->dict:
        data = super().to_dict()
        data.update({
            "payload": self.payload
        })
        return data
    
    @classmethod
    def from_dict(cls, data):
        return cls(data["command"], data["payload"], data["sender"])

    def __str__(self):
        base = super().__str__()
        return base + "\n" + self.payload