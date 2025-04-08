import sys
from Nodes.Nodes.Node import Node
from Nodes.Protocols.RicardMutualExclusion import RicardMutualExclusion
if len(sys.argv) != 4:
    raise ValueError('Please provide HOST, initializer PORT and local PORT NUMBER.')
NODE = Node(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), fifo=True)
NODE.print_info()
proto = RicardMutualExclusion(NODE)
proto.run()