import sys
from Nodes.Nodes.Node import Node
from Nodes.Protocols.Shout import Shout
if len(sys.argv) != 4:
    raise ValueError('Please provide HOST, initializer PORT and local PORT NUMBER.')
NODE = Node(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
NODE.print_info()
proto = Shout(NODE)
proto.run()