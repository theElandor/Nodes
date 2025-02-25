import networkx as nx
import sys
import Nodes.utils as utils
import Nodes.initializers as initializers
import os

# GRAPH CREATION
G = nx.complete_graph(3)
utils.draw_graph(G)

# FRAMEWORK
client = os.path.abspath("./client.py")
init = initializers.Initializer(client, "localhost", 65000, G, shell=False)
init.wait_for_termination()
init.wait_for_number_of_messages()