import sys
from Nodes.nodes import RingNode

if len(sys.argv) != 4:
    raise ValueError('Please provide HOST, initializer PORT and local PORT NUMBER.')
NODE = RingNode(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
NODE.send_RDY()
NODE.bind_to_port()
NODE.wait_for_instructions()
NODE._print_info()
#NODE.leader_election_controlled_distance_protocol()
#NODE.count_protocol()
#NODE.leader_election_AF_protocol()
NODE.leader_election_controlled_distance_protocol()

