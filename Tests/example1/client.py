import sys
from Nodes.Nodes.RingNode import RingNode
from Nodes.Protocols.LeaderElectionControlledDistance import LeaderElectionControlledDistance

if len(sys.argv) != 4:
    raise ValueError('Please provide HOST, initializer PORT and local PORT NUMBER.')
NODE = RingNode(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
NODE.print_info()
proto = LeaderElectionControlledDistance(NODE)
proto.run()