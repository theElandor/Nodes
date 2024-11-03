# DistributedAlgorithms
Framework to develop distributed algorithms on fixed
graph structures.
## Open Issues
+ Add Linux support;
+ Right now we only support "localhost";
+ Need to test on different topologies;
+ Missing "turn off nodes" logic after leader election;
+ Need a way to handle high number of nodes without creating a terminal for each node;
+ Write a primitive to send messages in parallel;
## Quickstart
```bash
python3 server.py data/example/network.txt
```
