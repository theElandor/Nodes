<p align="center">
  <img src="https://theelandor.github.io/NodesLogo.JPG" alt="Nodes" width=150/>
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
+ Leader election "All the Way";
+ Leader election "As far as it can";
+ Leader election "Controlled Distance";
## Open Issues
If you want to become a contributor, here's a list of possible improvements:
### General
+ Must add and test on Linux, only tested for Windows now;
+ Add non-live visualization of algorithm;
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
