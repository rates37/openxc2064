# Netlist Lowering and Bit-Separation

The **lowering pass** is an intermediate stage in the OpenXC2064 synthesis pipeline. It is the stage that transforms a high-level, behavioural netlist (like writing `a + b`) into a low-level, primitive netlist (using only low-level hardware primitives like gates, DFFs, and MUXes).

This document will describe the lowering process and bit-separation in detail.

---

## Bit-Separation (AND, OR, XOR, NOT)

The simplest translation involves separating logical operations into their bit-level counterparts. For example, a 2-bit AND operation can be translated into two 1-bit AND operations, one for each bit.

If the user writes `assign q[3:0] = a[3:0] & b[3:0];`, the lowering pass will translate this into four 1-bit AND operations, one for each bit. The output will be `q[3:0] = a[3] & b[3]; q[2] = a[2] & b[2]; q[1] = a[1] & b[1]; q[0] = a[0] & b[0];`.


## Arithmetic Operations (ADD, SUB, NEG)

Addition is not an independent operation, as lower bits influence the result of the higher bits. To account for this, the lowering pass replaces addition nodes with an equivalent ripple carry adder (RCA).

For a width `w`, the lowering pass generates the logic for a chain of `w` Full Adders (FAs), and incorporates this into the netlist accordingly. 

For a given bit `i`, the equations are:

- `sum[i] = a[i] ^ b[i] ^ cin[i]`
- `cout[i] = (a[i] & b[i]) | (cin[i] & (a[i] ^ b[i]))`

Where `cout[i]` is the carry-out of the `i`th bit, and `cin[i]` is the carry-in of the `i`th bit. The carry-in of the first bit is `cin[0] = 0`, and the carry-out of the last bit is `cout[w-1] = 0`.

### Subtraction

For **subtraction**, Two's complement arithmetic is used. The relation `A - B = A + (~B) + 1` allows the RCA logic from above to be re-used, with the `cin[0]` being set to `1`.


## Comparators (EQ, NEQ)

To evaluate `A == B`, we must verify that every bit in both `A` and `B` are equal. This can be done by using XOR gates, as `A == B` is true if and only if `A ^ B = 0`.

To aggregate this into a single Boolean answer, we build a balanced binary `OR`-tree that pairs and combines the output of every `XOR` wire. Rather than creating a deep linear $O(N)$ cascade, the tree recursively clusters pairs of wires into a single `OR` gate, halving the layer width successively until only 1 top-level `OR` gate remains. This minimizes signal propagation delay by reducing the physical hardware depth from $N-1$ down to $\lceil \log_2 N \rceil$. If the final output of the `OR` tree is `1`, it means equality failed. We finally invert the output with a `NOT` gate to properly represent `EQ` (`1` if match on all bits).

## Multiplexing

For multi-bit buses, the lowering pass translates a single `MUX(SEL, A, B)` node into an independent parallel layer of 1-bit `MUX` primitives, where the exact same `SEL` control wire is broadcast to every single `MUX` primitive.

## Bitwise Shifting

Parametric bit-shifting (e.g., `A << S` or `A >> S`) is a distinctly non-trivial operation to translate to physical hardware. The logic generated highly diverges depending on whether `S` is a *dynamic* runtime signal or a *constant* compile-time integer.

### Dynamic Shifts

If `S` changes at runtime, the lowering pass must generate logic for a **Barrel Shifter** capable of dynamically sweeping data across varying geometric powers of 2. It builds this using cascades of nested `MUX` layers:
- The `0`-th bit of the shift control vector (`S[0]`) drives a `MUX` layer that shifts the entire data bus by exactly $2^0 = 1$ bit (or passes it through unshifted).
- The `1`-st bit (`S[1]`) drives a sequential `MUX` layer that takes the result and shifts it by exactly $2^1 = 2$ bits.
- This continues recursively, meaning an $N$-bit shift control signal generates exactly $N$ hardware layers of MUX routing elements


### Constant Shifts

If the HDL declares a static shift amount (e.g., `A << 2`), the lowering pass can generate a much simpler logic structure by simply using direct buffers (wires) to connect input wires to corresponding output wires, and generating a barrel shifter is a waste of logic.
