import matplotlib.pyplot as plt
import networkx as nx
import os
import datetime
def read_graph(file):
    with open(file) as f:
        data = f.read().splitlines()
        nodes = int(data[0])
        edges = []
        for x in data[1:]:
            edges.append(tuple(eval(x)))
        return nodes, edges
    
def get_local_dns(DNS:dict, node:int, edges:list):
    local_dns = {}
    for u,v in edges:        
        for n in (u,v):
            if n != node:
                local_dns[n] = DNS[n]
    return local_dns

def draw_graph(G:nx.Graph):
    nx.draw(G, pos = None, ax = None, with_labels = True,font_size = 20, node_size = 2000, node_color = 'lightgreen')
    plt.show()

def init_logs(path):
    """
    Function used to initialize the directory containing the nodes logs.
    It will be automatically called by the initializer when the "shell"
    parameter is set to false. Otherwise, standard output and error are used for logging.
    Paramters:
        - path (str): path of the directory that will contain the logs of each node.
        If not specified, the initializer will create it in the same directory
        of the client file.
    """
    if not os.path.isdir(path):
        os.makedirs(path)
    experiment = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    experiment_path = os.path.join(path, experiment)
    os.makedirs(experiment_path)
    return experiment_path