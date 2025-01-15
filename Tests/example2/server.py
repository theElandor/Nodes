import networkx as nx
import sys
import Nodes.utils as utils
import Nodes.initializers as initializers
import os

# GRAPH CREATION
G = nx.gnm_random_graph(10, 15)
utils.draw_graph(G)

# FRAMEWORK
client = os.path.abspath("./client.py")
print(client)
init = initializers.Initializer(client, "localhost", 65000, G, shell=False)
init.initialize_clients()
init.setup_clients()
#init.wakeup(1)
#init.wakeup_all(1)
#init.wait_for_number_of_messages()
