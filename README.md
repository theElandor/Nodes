# Nodes
This framework aims to streamline research and education in distributed algorithms and distributed AI. 
It provides a simple and intuitive interface for developing distributed algorithms by merely defining the 
behavior of individual nodes and the graph structure. It is also suited for integration with ML and DL libraries
like scikitlearn, TensorFlow or PyTorch.
## Implemented Algorithms
+ Flooding on connected graph;
+ Spanning tree "Shout";
+ Spanning tree "Dft" (Depth First Traversal);
+ Leader election "All the Way";
+ Leader election "As far as it can";
+ Leader election "Controlled Distance";
## Open Issues
### General
+ Must add and test on Linux, only tested for Windows now;
+ Fix can't escape problem;
+ Add non-live visualization of algorithm;
## Quickstart
Clone/fork the repo and install the Nodes package in developer mode:
```bash
cd Nodes
python3 -m pip install -e .
```
You can find an example (client and server files) contained in the **Tests** directory. To run the first example:
```bash
cd Tests\example1
python3 server.py network.txt
```