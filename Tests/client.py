import sys
from Nodes.nodes import RingNode

if len(sys.argv) != 4:
    raise ValueError('Please provide HOST, initializer PORT and local PORT NUMBER.')
NODE = RingNode(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
NODE.send_RDY()
NODE.bind_to_port()
NODE.wait_for_instructions()
print(NODE)
NODE.leader_election_atw_protocol()