import networkx as nx
import sys
import Nodes.utils as utils
import Nodes.initializers as initializers
import os
from Nodes.const import Command

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
#utils.draw_graph(G)

# FRAMEWORK
client = os.path.abspath("./client.py")
print(client)
init = initializers.Initializer(client, "localhost", 65000, G, shell=False, visualizer=True)
init.initialize_clients()
init.setup_clients()
init.wakeup(3)
init.start_visualization()
#init.wakeup_all(2)
init.wait_for_number_of_messages()
