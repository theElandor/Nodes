import pickle

class Message:
    def __init__(self, command:str, sender:int=None):
        self.command = command
        self.sender = sender

    def serialize(self) -> bytes:
        """!Serialize to bytes before network transmission."""
        return pickle.dumps(self)
    
    @staticmethod
    def deserialize(data):
        return pickle.loads(data)
        
    def __str__(self):
        return f"{self.command} from {self.sender}"

class WakeUpMessage(Message):
    def __init__(self, command:str="WAKEUP", sender:int=None):
        super().__init__(command, sender)        
    def __str__(self):
        return super().__str__()
    
class FloodingMessage(Message):
    def __init__(self, command, sender:int=None, origin:int=None, counter:int=None):
        super().__init__(command, sender)
        self.origin = origin
        self.counter = counter
    def __str__(self):
        return super().__str__() + f"Origin: {self.origin}, Counter: {self.counter}"
    
class SetupMessage(Message):
    def __init__(self, command:str, node:int, edges:list, local_dns:dict, shell:bool, exp_path:str, sender:int=None):
        super().__init__(command, sender)
        self.node = node
        self.edges = edges
        self.local_dns = local_dns
        self.shell = shell
        self.exp_path = exp_path
    def __str__(self):
        return super().__str__() + f"{self.edges}\n{self.local_dns}\n{self.shell}\n{self.exp_path}"

class CountMessage(Message):
    def __init__(self, command, counter, sender:int=None):
        super().__init__(command, sender)
        self.counter = counter
    def __str__(self):
        return super().__str__() + f"Sender: {self.sender}, Counter: {self.counter}"

class LeaderElectionAtwMessage(Message):
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
    def __init__(self, command:str, sender, origin:int):
        super().__init__(command, sender)
        self.origin = origin
    def __str__(self):
        rep = super().__str__()
        rep += f"Origin: {self.origin}"
        return rep
