import networkx as nx
import Nodes.initializers as initializers
import os
import random
import seaborn as sb
import matplotlib.pyplot as plt
import Nodes.utils as utils
import pandas as pd

n_nodes = [5*i for i in range(1,5)]
clients = [
    ("./lamport_client.py", "Lamport"),
    ("./ricard_client.py", "Ricard and Agrawala"),
]
df = pd.DataFrame(columns=["Protocol", "Nodes", "Messages"])
PORT = 65000
for CLIENT_PATH, PROTOCOL_NAME in clients:
    for n in n_nodes:
        node_ids = list(range(n))
        G = nx.complete_graph(node_ids)
        n = G.number_of_nodes()
        m = G.number_of_edges()
        print(f"Nodes: {n}")
        print(f"Edges: {m}")
        client = os.path.abspath(CLIENT_PATH)
        init = initializers.Initializer(client, "localhost", PORT, G, shell=False)
        init.wait_for_termination()
        messages = init.wait_for_number_of_messages()
        df.loc[len(df)] = [PROTOCOL_NAME, n, messages]
        init.close()
print(df)
sb.set_style("whitegrid")
fig, ax = plt.subplots(figsize=(8, 4))
sb.lineplot(data=df, x="Nodes", y="Messages", hue="Protocol",marker='o', ax=ax, color="b")
plt.title("Message Comparison of Mutual Exclusion Algorithms")
plt.savefig("comparison.png", bbox_inches="tight", dpi=300)