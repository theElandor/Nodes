import networkx as nx
import sys
import utils
import initializer
G = nx.Graph()
if len(sys.argv) != 2:
    raise ValueError('Please provide exactly one argument.')
N, edges = utils.read_graph(sys.argv[1])
print("Graph info")
print(f"Nodes: {N} \nEdges: {len(edges)}")
nodes = [x+1 for x in range(N)]
G.add_nodes_from(nodes)
G.add_edges_from(edges)

init = initializer.RingNetworkInitializer("localhost", 65000, G)
print(init)
init.initialize_clients()
init.setup_clients()
#count_wakeup_message = str([3, -1, 0]).encode()
LE_wakeup_message = str(["WAKEUP", -0,0,0])
init.wakeup(3, LE_wakeup_message.encode())
init.wait_for_number_of_messages()