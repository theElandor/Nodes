<p align="center">
  <img src="https://theelandor.github.io/NodesLogo.JPG" alt="Nodes" width=400/>
</p>

This framework aims at helping researchers and developers who want to test and play with distributed algorithms.
It provides a simple and intuitive interface to define the
behavior of individual nodes and the graph structure, and it takes care of the rest. Because of its simplicity, it is easily extendible in its capabilities. It is also suited for integration with ML and DL libraries
like scikitlearn, TensorFlow or PyTorch.
## Implemented Algorithms
+ Lamport's Mutual Exclusion;
+ Flooding on connected graph;
+ Spanning tree "Shout";
+ Spanning tree "Dft" (Depth First Traversal);
+ Leader election "Bully";
+ Leader election "All the Way";
+ Leader election "As far as it can";
+ Leader election "Controlled Distance";
## Quickstart
Clone/fork the repo and install the Nodes package in developer mode:
```bash
cd Nodes
python3 -m pip install -e .
```
You can find several examples (client and server files) contained in the **Tests** directory. You can find the full documentation in the docs/ folder. To run the first example:
```bash
cd Tests\example1
python3 server.py network.txt
```
Below you can find another example (example3) with some comments to help you become
familiar with the framework.
## Server

```python
import networkx as nx
import sys
import Nodes.utils as utils
import Nodes.initializers as initializers
import os

#create any graph you like with networkx
G = nx.erdos_renyi_graph(7, 0.5, seed=1, directed=False)

#print some metrics of interest
n = G.number_of_nodes()
m = G.number_of_edges()
print(f"Nodes: {n}")
print(f"Edges: {m}")
print(f"Expected n. of messages: {(4*m)-(2*n)+2}")

#specify the path of the client absolute path
client = os.path.abspath("./client.py")

#create the initializer object
init = initializers.Initializer(client, "localhost", 65000, G, shell=False)

#wakeup node with ID=5
init.wakeup(5)

#wait for protocol termination
init.wait_for_termination()

#wait for messages containing total messages used during the protocol.
init.wait_for_number_of_messages()
```

## Client
Here's an example client.py file. In this case, we want to create a node running the **Shout** protocol, which is alredy implemented in the **Protocols** package. Alternatively, you can define your custom protocol directly in the client.py file for convenience.

```python
import sys
from Nodes.Nodes.Node import Node
from Nodes.Protocols.Shout import Shout
if len(sys.argv) != 4:
    raise ValueError('Please provide HOST, initializer PORT and local PORT NUMBER.')
NODE = Node(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))

#create the protocol object
proto = Shout(NODE)

#run the protocol
proto.run()
```

## Protocol
This is a possibile implementation of the Shout protocol, used to create a spanning tree in a undirected graph in a distributed way. As you can see, it is similar to pseudo-code.
To create your custom protocol, always override these 3 methods:

- ```setup()```: setup procedure that each node executes at the beginning of the        protocol. It is usefull to initialize variables or start parallel threads (see example5);

- ```handle_message()```: this method should be the core of the protocol. You have to specify for each possibile combination of state and message what the node should do. Remember that you can find some useful tokens in the ```Nodes.const``` package to avoid typos in strings.
When the node has locally terminated the computation, just return ```True```.

- ```cleanup()```: you can optionally override this method to send extra information or log variables at the end of the protocol. In this case, we send the total number of messages sent by the node during the computation.


```python
from Nodes.Protocols.Protocol import Protocol
from Nodes.messages import Message
from Nodes.const import Command, State
from Nodes.Nodes.Node import Node

class Shout(Protocol):
    def __init__(self, node: Node):
        super().__init__(node)

    def setup(self):
        self.state = State.IDLE        
        self.counter = None
        self.parent = None
        self.tree_neigs = set()

    def handle_message(self, message: Message) -> bool:
        assert message.command != Command.START_AT, "This protocol supports only 1 initiator."
        if self.state == State.IDLE:
            if message.command == Command.WAKEUP:                
                self.node.log("I am the root.")
                self.counter = 0
                self.state = State.ACTIVE
                self.node.send_to_all(Message(Command.Q, self.node.id))
            if message.command == Command.Q:
                self.node.log("I am a child.")
                self.parent = message.sender
                self.tree_neigs.add(message.sender)
                self.counter = 1
                self.node.send_to(Message(Command.YES, self.node.id), self.parent)
                if self.counter == len(self.node.get_neighbors()):
                    self.state = State.DONE
                    self.node.log("Computation Done.")
                    self.node.log(str(self.tree_neigs))
                    self.node.log(str(self.parent))
                    return True
                else:
                    self.node.send_to_all_except(message.sender, Message(Command.Q, self.node.id))
                    self.state = State.ACTIVE
        elif self.state == State.ACTIVE:
            if message.command == Command.Q:                
                self.node.send_to(Message(Command.NO, self.node.id), message.sender)
            if message.command == Command.YES:
                self.tree_neigs.add(message.sender)
                self.counter += 1
                if self.counter == len(self.node.get_neighbors()):
                    self.state = State.DONE
                    self.node.log("Computation Done.")
                    self.node.log(str(self.tree_neigs))
                    self.node.log(str(self.parent))
                    return True
            if message.command == Command.NO:
                self.counter += 1
                if self.counter == len(self.node.get_neighbors()):
                    self.state = State.DONE
                    self.node.log("Computation Done.")
                    self.node.log(str(self.tree_neigs))
                    self.node.log(str(self.parent))
                    return True
                
    def cleanup(self):
        super().cleanup()
        self.node.send_total_messages()
```