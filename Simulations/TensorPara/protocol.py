import numpy as np
from Nodes.Protocols.Protocol import Protocol
from Nodes.const import Command,State
from Nodes.messages import Message
from Nodes.Nodes import Node
class TensorParallel:
    def __init__(self, node: Node):
        super().__init__(node) 

    def setup():
        pass

    def handle_message():
        pass

    def cleanup():
        super().cleanup()
        pass
