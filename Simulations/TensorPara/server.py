import numpy as np
import Nodes.initializers as init
import os
import networkx as nx

CLIENT_PATH = "./client.py"
PORT = 6500
# 1 master and 4 workers
NODES = 5
G = nx.complete_graph(NODES)
client = os.path.abspath(CLIENT_PATH)
I = init.Initializer(client, "localhost", PORT, G, shell=False)
# wakeup master node that will take care of coordinating
# other workers. When using this framework, it's adivsable
# to put the logic in the Nodes and use the server just
# for termination purposes.
I.wakeup(1) 
I.wait_for_termination()
