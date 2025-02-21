from enum import Enum

class Command(str, Enum):
    """!Enumerator for commands used in protocols."""
    
    WAKEUP = "WAKEUP"
    START_AT = "START_AT"
    READY = "RDY"
    SETUP = "SETUP"
    START_PROTOCOL = "SOP"
    COUNT = "COUNT"
    INFORM = "I"
    ELECTION = "Election"
    NOTIFY = "Notify"
    FORTH = "Forth"
    BACK = "Back"
    TERM = "TERM"
    END = "END"
    FORWARD = "FWD"
    SAT = "SAT"
    Q = "Q"
    YES = "YES"
    NO = "NO"
    COUNT_M = "COUNT_M"
    RETURN = "RETURN"
    BACK_EDGE = "BACK_EDGE"
    
    ERROR = "ERROR"
    END_PROTOCOL = "EOP"


class State(str, Enum):
    """!Enumerator for states used in protocols."""
    
    ASLEEP = "ASLEEP"
    AWAKE = "AWAKE"
    CANDIDATE = "CANDIDATE"
    DEFEATED = "DEFEATED"
    LEADER = "LEADER"
    FOLLOWER = "FOLLOWER"
    DONE = "DONE"
    PROCESSING = "PROCESSING"
    SATURATED = "SATURATED"
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"    
    VISITED = "VISITED"

class VisualizerState(str, Enum):
    INTERNAL_ERROR = "INTERNAL_ERROR"
    EXTERNAL_ERROR = "EXTERNAL_ERROR"
    SUCCESS = "SUCCESS"
    CONTINUE = "CONTINUE"
    