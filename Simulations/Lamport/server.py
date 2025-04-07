import networkx as nx
import Nodes.initializers as initializers
import os
import pandas as pd
import seaborn as sb
import matplotlib.pyplot as plt
n_nodes = [5*i for i in range(1,11)]
CLIENT_PATH = "./client.py"
df = pd.DataFrame(columns=["Nodes", "Messages"])
PORT = 65000
for i,n in enumerate(n_nodes):
    print(f"{i}/{len(n_nodes)} simulations done.")
    G = nx.complete_graph(n)
    client = os.path.abspath(CLIENT_PATH)
    init = initializers.Initializer(client, "localhost", PORT, G, shell=False)
    init.wait_for_termination()
    messages = init.wait_for_number_of_messages()
    df.loc[len(df)] = [n, messages]
    init.close()
print(df)
sb.set_style("whitegrid")
fig, ax = plt.subplots(figsize=(8, 4))
sb.lineplot(data=df, x="Nodes", y="Messages", marker='o', ax=ax, color="b")
plt.title("Number of Messages vs Number of Nodes in LME")
plt.savefig("lamport.png", bbox_inches="tight", dpi=300)