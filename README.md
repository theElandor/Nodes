# DistributedAlgorithms
Framework to develop distributed algorithms on fixed
graph structures.
## Implemented Algorithms
+ Leader election "All the Way";
+ Leader election "As far as it can";
## Open Issues
+ Add Linux support;
+ Right now we only support "localhost";
+ Need to test on different topologies;
+ Need a way to handle high number of nodes without creating a terminal for each node;
+ Need a way to test algorithms when all of the nodes "simultaneously";
+ Need to encapsulate each protocol and its own helper functions in a Class (requires refactoring);
## Quickstart
```bash
python3 server.py data/example/network.txt
```
