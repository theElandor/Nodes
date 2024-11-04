# DistributedAlgorithms
Framework to develop distributed algorithms on fixed
graph structures.
## Open Issues
+ Add Linux support;
+ Right now we only support "localhost";
+ Need to test on different topologies;
+ Missing "turn off nodes" logic after leader election;
+ Need a way to handle high number of nodes without creating a terminal for each node;
+ Need a way to test algorithms when all of the nodes "simultaneously" start the computation,
  so the most correct way possibile to wake up all of them "in parallel".
## Quickstart
```bash
python3 server.py data/example/network.txt
```
