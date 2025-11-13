# Rough notes on the implementation plan for this project (subject to change)

At a high level, HDL will be taken through the following path to be converted into a bitstream:

1. HDL gets parsed into an AST representation (via `src/openxc2064/hdl`)

2. AST gets converted into a netlist (elaboration), hierarchy is flattened, connections resolved (via `src/openxc2064/hdl/elaborator.py`)

3. Netlist is mapped to XC2064 primitives (LUTs/CLBs/etc) (via `src/openxc2064/netlist/primitives.py`)

4. Each CLB is assigned to a location on the XC2064 (via `src/openxc2064/synthesis` and `src/openxc2064/placement`)

5. Perform routing between CLBs (via `src/openxc2064/placement` and `src/openxc2064/routing`)

6. Representative bitstream is generated (via `src/openxc2064/bitstream`)
