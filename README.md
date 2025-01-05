# Nodes

This framework aims to streamline research and education in distributed algorithms and distributed AI. 
It provides a simple and intuitive interface for developing distributed algorithms by merely defining the 
behavior of individual nodes and the graph structure. It is also suited for integration with ML and DL libraries
like scikitlearn, TensorFlow or PyTorch.
## Implemented Algorithms
+ Leader election "All the Way";
+ Leader election "As far as it can";
+ Leader election "Controlled Distance";
## Open Issues
### General
+ Add Linux support;
+ Need to improve sync logic;
+ Need to encapsulate each protocol and its own helper functions in a Class (requires refactoring);
+ Must add unidirectional links support;
+ Must add a "run tests" script;
+ Need validation for read_graph function;
+ Find a way to handle different message format, use JSON instead of eval();
### Performance
+ Keep log files opened;
+ Re-use sockets instead of creating new ones;
## Quickstart
Clone/fork the repo and install the Nodes package in developer mode:
```bash
cd Nodes
python3 -m pip install -e .
```
You can find an example (client and server files) contained in the **Tests** directory. Use the following
command to run it:
```bash
cd Tests
python3 server.py ..\data\example\network.txt
```
