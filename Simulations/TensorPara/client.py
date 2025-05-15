import sys
from Nodes.Nodes.Node import Node
from protocol import TensorParallel
NODE = Node(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), fifo=True)
NODE.print_info()
proto = TensorParallel(NODE)
proto.run()
