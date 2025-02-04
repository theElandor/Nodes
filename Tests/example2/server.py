import networkx as nx
import sys
import Nodes.utils as utils
import Nodes.initializers as initializers
import os

# GRAPH CREATION
G = nx.erdos_renyi_graph(10, 0.5, seed=123, directed=False)
n = G.number_of_nodes()
m = G.number_of_edges()
#utils.draw_graph(G)
print(f"Nodes: {n}")
print(f"Edges: {m}")
print(f"With flood algorithm, we expect {(2*m)-(n-1)} messages.")

# FRAMEWORK
client = os.path.abspath("./client.py")
print(client)
init = initializers.Initializer(client, "localhost", 65000, G, shell=False)
init.initialize_clients()
init.setup_clients()
init.wakeup(5)
#init.wakeup_all(2)
init.wait_for_number_of_messages()
