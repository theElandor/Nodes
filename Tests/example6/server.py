import networkx as nx
import sys
import Nodes.utils as utils
import Nodes.initializers as initializers
import os

#create any graph you like with networkx
G = nx.complete_graph(5)
client = os.path.abspath("./client.py")
init = initializers.Initializer(client, "localhost", 65000, G, shell=False)
init.wakeup(0)
init.wait_for_termination()
init.wait_for_number_of_messages()