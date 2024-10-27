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