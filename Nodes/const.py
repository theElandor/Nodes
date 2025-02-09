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
