import networkx as nx
import sys
import Nodes.utils as utils
import Nodes.initializers as initializers
import os

# GRAPH CREATION
G = nx.erdos_renyi_graph(7, 0.5, seed=1, directed=False)
n = G.number_of_nodes()
m = G.number_of_edges()
#utils.draw_graph(G)
print(f"Nodes: {n}")
print(f"Edges: {m}")
print(f"Expected n. of messages: {(4*m)-(2*n)+2}")

# FRAMEWORK
client = os.path.abspath("./client.py")
init = initializers.Initializer(client, "localhost", 65000, G, shell=False)
init.wakeup(5)
init.wait_for_termination()
init.wait_for_number_of_messages()