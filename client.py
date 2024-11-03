import sys
from nodes import RingNode

if len(sys.argv) != 4:
    raise ValueError('Please provide host, initializer PORT and port number.')
NODE = RingNode(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
NODE.send_RDY()
NODE.bind_to_port()
NODE.wait_for_instructions()
print(NODE)
NODE.leader_election_AF_protocol()