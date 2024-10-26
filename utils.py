def read_graph(file):
    with open(file) as f:
        data = f.read().splitlines()
        nodes = int(data[0])
        edges = []
        for x in data[1:]:
            edges.append(tuple(eval(x)))
        return nodes, edges