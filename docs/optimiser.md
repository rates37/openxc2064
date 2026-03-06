# Optimisation Process

This document provides a short overview of the algorithms / processes used for the logic optimisation phase in the `openxc2064` tool chain. 

After the HDL is synthesised into a generic Netlist (a representation of the computational graph), it often contains redundancies and unreachable / unused logic. Eliminating these saves valuable space on the FPGA, and can reduce propagation delay in a design.

In the [`Optimiser`](/src/openxc2064/synthesis/optimiser.py) class, three simplification techniques are implemented; **Dead Code Elimination(DCE)**, **Constant Folding**, and **Structural Boolean Simplification**.


The `Optimiser` class iteratively applies all three of these reduction techniques repeatedly, until no more changes are made in a single pass, which marks the point where the Netlist is in its simplest form*.

\* By 'simplest', we mean simplest form that can be achieved by using the simplification techniques implemented. The reduction techniques currently used here are not guaranteed to produce an optimally minimal netlist.

---


## 1. Dead Code Elimination

In the context of hardware, "Dead Code" refers to any logic gate, register or net that does not eventually drive an output. This can easily happen if a user defines a multi-bit register, but only actively reads from a subset of its bits.

### The algorithm

DCE operates on the computational graph (the `Netlist`), treating it as a Directed Acyclic Graph (DAG). It follows the steps below:

1. **Live Set**: Initialise a set of "Live" nodes.

2. **Port collection**: Examine every top-level output port of the netlist. THe nodes that directly drive these output ports are inherrently useful, so we add them to the "live" set. Input ports are also unconditionally added.

3. **Netlist traversal**: For every node that gets added to the "live" set, inspect its drivers. Any node that drives a node in the live set must also be added to the "live" set. This process is effectively a BFS of the computational graph.

4. **Node pruning**: Once the traversal finished, we have the transitive closure of all nodes that are necessary to compute the module's outputs. Any node that is **not** in the "live" set is removed, as it is not necessary to compute the module's outputs.

5. **Netlist reconstruction**: After removing the dead nodes, we need to clean up the connecting wires (`Net`s). A net is considered "live" if it belongs to any remaining live node or is an input/output port. We collect all live nets and rebuild the netlist's internal net registry.

### Visualising DCE

To visualise the DCE process, we can use the following example. Suppose we start with the HDL below:

```verilog
module example(input a, input b, output y);
    wire unused_wire;
    wire unused_reg;
    
    // The live pathway
    assign y = a & b;
    
    // The dead pathway (never read by any outputs)
    assign unused_wire = a | b;
    
    always @(posedge a) begin
        unused_reg <= unused_wire;
    end
endmodule
```

**Circuit Before DCE:**

Notice how the `OR` gate and the `DFF` are structurally valid, but they ultimately do not cascade into the module output `y`.

```mermaid
graph LR
    InA[Input: a] --> NetA(Net: a)
    InB[Input: b] --> NetB(Net: b)
    
    NetA --> AND1(Gate: AND)
    NetB --> AND1
    
    NetA --> OR1(Gate: OR)
    NetB --> OR1
    
    AND1 --> NetY(Net: y)
    NetY --> OutY[Output: y]
    
    OR1 --> NetUW(Net: unused_wire)
    NetUW --> DFF1(DFF: unused_reg)
    NetA -. clock .-> DFF1
```

**After the Sweep (Nodes removed)**

After the pass, we identify that only `Gate: AND`, `Input: a`, and `Input: b` are required. The unvisited `OR` Gate and `DFF` are completely deleted from the node registry. However, the live nets (`Net: a` and `Net: b`) temporarily retain dangling `sink` references to the ghosts of these deleted nodes.

```mermaid
graph LR
    InA[Input: a] --> NetA(Net: a)
    InB[Input: b] --> NetB(Net: b)
    
    NetA --> AND1(Gate: AND)
    NetB --> AND1
    
    AND1 --> NetY(Net: y)
    NetY --> OutY[Output: y]
    
    NetA -. dangling sink .-> DEAD1[Deleted Nodes]
    NetB -. dangling sink .-> DEAD1
```

** Netlist reconstruction**

In the final step, we rebuild the netlist by removing the dangling sinks and reassigning the drivers of each node to their new locations. The live nets iterate through their `sink` lists and sever any invalid connections to dead components, leaving a minimised graph.

```mermaid
graph LR
    InA[Input: a] --> NetA(Net: a)
    InB[Input: b] --> NetB(Net: b)
    
    NetA --> AND1(Gate: AND)
    NetB --> AND1
    
    AND1 --> NetY(Net: y)
    NetY --> OutY[Output: y]
```
