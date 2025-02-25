import sys
from Nodes.Nodes.Node import Node
from Nodes.Protocols.Dft import Dft
if len(sys.argv) != 4:
    raise ValueError('Please provide HOST, initializer PORT and local PORT NUMBER.')
NODE = Node(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), fifo=True)
NODE.print_info()
proto = Dft(NODE)
proto.run()