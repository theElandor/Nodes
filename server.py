import networkx as nx
import sys
import utils
import initializers

# GRAPH CREATION
G = nx.Graph()
if len(sys.argv) != 2:
    raise ValueError('Please provide exactly one argument.')
N, edges = utils.read_graph(sys.argv[1])
print("Graph info")
print(f"Nodes: {N} \nEdges: {len(edges)}")
nodes = [x+1 for x in range(N)]
G.add_nodes_from(nodes)
G.add_edges_from(edges)
utils.draw_graph(G)

# FRAMEWORK
init = initializers.Initializer("localhost", 65000, G)
print(init)
init.initialize_clients()
init.setup_clients()
init.wakeup(1)
init.wait_for_number_of_messages()