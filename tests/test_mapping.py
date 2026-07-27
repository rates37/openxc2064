import pytest
import itertools
from openxc2064.synthesis.rtl_nodes import Netlist, Constant, LogicGate
from openxc2064.mapping.xc2064_primitives import LUT, CLB, IOB
from openxc2064.mapping.mapper import GreedyMapper
from openxc2064.mapping.packer import GreedyPacker, CapacityError
from openxc2064.simulator.high_level_rtl_simulator import RTLSimulator

def test_mapper_simple_and():
    nl = Netlist("test")
    a = nl.create_net("a", 1)
    b = nl.create_net("b", 1)
    q = nl.create_net("q", 1)

    nl.add_input("a", a)
    nl.add_input("b", b)
    nl.add_logic("AND", [a, b], [q])
    
    nl.outputs.append(q)
    
    mapper = GreedyMapper(k_max=4)
    mapped_nl = mapper.run(nl)
    
    luts = [n for n in mapped_nl.nodes if isinstance(n, LUT)]
    assert len(luts) == 1
    lut = luts[0]
    
    # Truth table for AND is be 1000 in binary (MSB to LSB = bit 3 to 0).
    assert lut.truth_table == 0b1000

    # Verify via Simulator
    sim = RTLSimulator(mapped_nl)
    for a_val, b_val in itertools.product([0, 1], [0, 1]):
        sim.set("a", a_val)
        sim.set("b", b_val)
        sim.step()
        assert sim.get("q") == (a_val & b_val)

def test_mapper_simple_or():
    nl = Netlist("test")
    a = nl.create_net("a", 1)
    b = nl.create_net("b", 1)
    q = nl.create_net("q", 1)

    nl.add_input("a", a)
    nl.add_input("b", b)
    nl.add_logic("OR", [a, b], [q])
    nl.outputs.append(q)
    
    mapper = GreedyMapper(k_max=3)
    mapped_nl = mapper.run(nl)
    
    luts = [n for n in mapped_nl.nodes if isinstance(n, LUT)]
    assert len(luts) == 1
    assert luts[0].truth_table == 0b1110
    
    sim = RTLSimulator(mapped_nl)
    for a_val, b_val in itertools.product([0, 1], [0, 1]):
        sim.set("a", a_val)
        sim.set("b", b_val)
        sim.step()
        assert sim.get("q") == (a_val | b_val)

def test_mapper_simple_xor():
    nl = Netlist("test")
    a = nl.create_net("a", 1)
    b = nl.create_net("b", 1)
    q = nl.create_net("q", 1)

    nl.add_input("a", a)
    nl.add_input("b", b)
    nl.add_logic("XOR", [a, b], [q])
    nl.outputs.append(q)
    
    mapper = GreedyMapper(k_max=3)
    mapped_nl = mapper.run(nl)
    
    luts = [n for n in mapped_nl.nodes if isinstance(n, LUT)]
    assert len(luts) == 1
    assert luts[0].truth_table == 0b0110
    
    sim = RTLSimulator(mapped_nl)
    for a_val, b_val in itertools.product([0, 1], [0, 1]):
        sim.set("a", a_val)
        sim.set("b", b_val)
        sim.step()
        assert sim.get("q") == (a_val ^ b_val)

def test_mapper_simple_not():
    nl = Netlist("test")
    a = nl.create_net("a", 1)
    q = nl.create_net("q", 1)

    nl.add_input("a", a)
    nl.add_logic("NOT", [a], [q])
    nl.outputs.append(q)
    
    mapper = GreedyMapper(k_max=3)
    mapped_nl = mapper.run(nl)
    
    luts = [n for n in mapped_nl.nodes if isinstance(n, LUT)]
    assert len(luts) == 1
    assert luts[0].truth_table == 0b1
    
    sim = RTLSimulator(mapped_nl)
    for a_val in [0, 1]:
        sim.set("a", a_val)
        sim.step()
        assert sim.get("q") == (~a_val & 1)

def test_mapper_4_input_cut():
    # q = (a & b) | (c ^ d)
    nl = Netlist("test")
    a = nl.create_net("a", 1)
    b = nl.create_net("b", 1)
    c = nl.create_net("c", 1)
    d = nl.create_net("d", 1)
    
    and_out = nl.create_net("and_out", 1)
    xor_out = nl.create_net("xor_out", 1)
    q = nl.create_net("q", 1)
    
    nl.add_input("a", a)
    nl.add_input("b", b)
    nl.add_input("c", c)
    nl.add_input("d", d)
    
    nl.add_logic("AND", [a, b], [and_out])
    nl.add_logic("XOR", [c, d], [xor_out])
    nl.add_logic("OR", [and_out, xor_out], [q])
    
    nl.outputs.append(q)
    
    mapper = GreedyMapper(k_max=3)
    mapped_nl = mapper.run(nl)
    
    luts = [n for n in mapped_nl.nodes if isinstance(n, LUT)]
    
    # It should split into 2 LUTs since K=3 is the max constraint.
    assert len(luts) == 2
    for lut in luts:
        assert lut.k <= 3

    sim = RTLSimulator(mapped_nl)
    for a_val, b_val, c_val, d_val in itertools.product([0, 1], repeat=4):
        sim.set("a", a_val)
        sim.set("b", b_val)
        sim.set("c", c_val)
        sim.set("d", d_val)
        sim.step()
        expected = (a_val & b_val) | (c_val ^ d_val)
        assert sim.get("q") == expected

def test_mapper_complex_tree():
    # q = ((a & b) ^ c) | (~d & e)
    nl = Netlist("test")
    a = nl.create_net("a", 1)
    b = nl.create_net("b", 1)
    c = nl.create_net("c", 1)
    d = nl.create_net("d", 1)
    e = nl.create_net("e", 1)
    
    and1 = nl.create_net("and1", 1)
    xor1 = nl.create_net("xor1", 1)
    not_d = nl.create_net("not_d", 1)
    and2 = nl.create_net("and2", 1)
    q = nl.create_net("q", 1)
    
    nl.add_input("a", a)
    nl.add_input("b", b)
    nl.add_input("c", c)
    nl.add_input("d", d)
    nl.add_input("e", e)
    
    nl.add_logic("AND", [a, b], [and1])
    nl.add_logic("XOR", [and1, c], [xor1])
    nl.add_logic("NOT", [d], [not_d])
    nl.add_logic("AND", [not_d, e], [and2])
    nl.add_logic("OR", [xor1, and2], [q])
    nl.outputs.append(q)
    
    mapper = GreedyMapper(k_max=3)
    mapped_nl = mapper.run(nl)
    
    luts = [n for n in mapped_nl.nodes if isinstance(n, LUT)]
    assert len(luts) >= 2 # definitively needs more than 1 due to 5 inputs
    for lut in luts:
        assert lut.k <= 3
        
    sim = RTLSimulator(mapped_nl)
    for vals in itertools.product([0, 1], repeat=5):
        sim.set("a", vals[0])
        sim.set("b", vals[1])
        sim.set("c", vals[2])
        sim.set("d", vals[3])
        sim.set("e", vals[4])
        sim.step()
        
        expected = ((vals[0] & vals[1]) ^ vals[2]) | ((~vals[3] & 1) & vals[4])
        assert sim.get("q") == expected

def test_packer_clustering():
    nl = Netlist("test")
    a = nl.create_net("a", 1)
    b = nl.create_net("b", 1)
    c = nl.create_net("c", 1)
    
    # LUT 1: a AND b
    out1 = nl.create_net("out1", 1)
    nl.add_logic("AND", [a, b], [out1])
    
    # LUT 2: a OR c
    out2 = nl.create_net("out2", 1)
    nl.add_logic("OR", [a, c], [out2])
    
    nl.add_input("a", a)
    nl.add_input("b", b)
    nl.add_input("c", c)
    nl.outputs.extend([out1, out2])
    
    mapper = GreedyMapper(k_max=3)
    mapped_nl = mapper.run(nl)
    
    packer = GreedyPacker(max_clbs=64)
    packed_nl = packer.run(mapped_nl)
    
    clbs = [n for n in packed_nl.nodes if isinstance(n, CLB)]
    # They share 'a' input, total inputs = {a, b, c} = 3 <= 4.
    # Therefore, the packer should have packed both into exactly 1 CLB
    assert len(clbs) == 1

    # Verify via Simulator
    sim = RTLSimulator(packed_nl)
    for a_val, b_val, c_val in itertools.product([0, 1], repeat=3):
        sim.set("a", a_val)
        sim.set("b", b_val)
        sim.set("c", c_val)
        sim.step()
        assert sim.get("out1") == (a_val & b_val)
        assert sim.get("out2") == (a_val | c_val)

def test_packer_dff_pairing():
    nl = Netlist("test")
    a = nl.create_net("a", 1)
    b = nl.create_net("b", 1)
    clk = nl.create_net("clk", 1)
    
    out1 = nl.create_net("out1", 1)
    nl.add_logic("XOR", [a, b], [out1])
    
    q = nl.create_net("q", 1)
    nl.add_dff([out1, clk], [q])
    
    nl.add_input("a", a)
    nl.add_input("b", b)
    nl.add_input("clk", clk)
    nl.outputs.append(q)
    
    mapped_nl = GreedyMapper(k_max=3).run(nl)
    packed_nl = GreedyPacker(max_clbs=64).run(mapped_nl)
    
    clbs = [n for n in packed_nl.nodes if isinstance(n, CLB)]
    
    # The XOR should map perfectly into a single LUT, which also drives the DFF
    assert len(clbs) == 1
    assert clbs[0].dff is not None

    # Verify via Simulator
    sim = RTLSimulator(packed_nl)
    # Clock edge verification
    sim.set("clk", 0)
    sim.set("a", 1)
    sim.set("b", 0)
    sim.step()
    assert sim.get("q") == 0 # No edge yet
    
    sim.set("clk", 1)
    sim.step()
    assert sim.get("q") == 1 # 1 ^ 0 = 1

    sim.set("clk", 0)
    sim.set("a", 1)
    sim.set("b", 1)
    sim.step()
    assert sim.get("q") == 1 # Still 1 (previous state)
    
    sim.set("clk", 1)
    sim.step()
    assert sim.get("q") == 0 # 1 ^ 1 = 0

def test_packer_small_fsm():
    # A tiny state machine: q_next = (a & b) ^ q
    nl = Netlist("complex")
    a = nl.create_net("a", 1)
    b = nl.create_net("b", 1)
    clk = nl.create_net("clk", 1)
    q = nl.create_net("q", 1)
    
    comb_out = nl.create_net("comb_out", 1)
    and_out = nl.create_net("and_out", 1)
    
    nl.add_logic("AND", [a, b], [and_out])
    nl.add_logic("XOR", [and_out, q], [comb_out])
    nl.add_dff([comb_out, clk], [q])
    
    nl.add_input("a", a)
    nl.add_input("b", b)
    nl.add_input("clk", clk)
    nl.outputs.append(q)
    
    mapped_nl = GreedyMapper(k_max=3).run(nl)
    packed_nl = GreedyPacker(max_clbs=64).run(mapped_nl)
    
    clbs = [n for n in packed_nl.nodes if isinstance(n, CLB)]
    # (a & b) ^ q has 3 inputs: a, b, q
    # It should map to 1 LUT and 1 DFF, all inside 1 CLB
    assert len(clbs) == 1
    
    sim = RTLSimulator(packed_nl)
    sim.set("clk", 0)
    sim.set("a", 1)
    sim.set("b", 1)
    # Initial state should be 0
    sim.step()
    
    # Tick 1: (1 & 1) ^ 0 = 1
    sim.set("clk", 1)
    sim.step()
    assert sim.get("q") == 1
    
    # Tick 2: (1 & 1) ^ 1 = 0
    sim.set("clk", 0)
    sim.step()
    sim.set("clk", 1)
    sim.step()
    assert sim.get("q") == 0
    
    # Tick 3 with inputs changed: (0 & 1) ^ 0 = 0
    sim.set("clk", 0)
    sim.set("a", 0)
    sim.step()
    sim.set("clk", 1)
    sim.step()
    assert sim.get("q") == 0


def test_packer_standalone_dff():
    nl = Netlist("standalone")
    a = nl.create_net("a", 1)
    clk = nl.create_net("clk", 1)
    q = nl.create_net("q", 1)
    
    # DFF driven directly by 'a'
    nl.add_dff([a, clk], [q])
    
    nl.add_input("a", a)
    nl.add_input("clk", clk)
    nl.outputs.append(q)
    
    mapped_nl = GreedyMapper(k_max=3).run(nl)
    packed_nl = GreedyPacker(max_clbs=64).run(mapped_nl)
    
    clbs = [n for n in packed_nl.nodes if isinstance(n, CLB)]
    assert len(clbs) == 1
    # buffer of the single input, which routes onto the first LUT mux; in the
    # web simulator's bit order that mux is bit 2 of the truth-table index
    assert clbs[0].lut_f_init == 0xF0
    
    sim = RTLSimulator(packed_nl)
    sim.set("clk", 0)
    sim.set("a", 1)
    sim.step()
    assert sim.get("q") == 0
    
    sim.set("clk", 1)
    sim.step()
    assert sim.get("q") == 1

def test_packer_capacity_error():
    # Create a netlist that definitely requires > 64 CLBs
    nl = Netlist("huge")
    for i in range(70):
        a = nl.create_net(f"a{i}", 1)
        b = nl.create_net(f"b{i}", 1)
        c = nl.create_net(f"c{i}", 1)
        and_out = nl.create_net(f"and{i}", 1)
        q = nl.create_net(f"q{i}", 1)
        
        nl.add_input(f"a{i}", a)
        nl.add_input(f"b{i}", b)
        nl.add_input(f"c{i}", c)
        
        nl.add_logic("AND", [a, b], [and_out])
        nl.add_logic("OR", [and_out, c], [q])
        nl.outputs.append(q)
    
    mapped_nl = GreedyMapper(k_max=3).run(nl)
    # Each (a & b) | c should map to 1 LUT with 3 unique inputs
    # Since inputs are unique (a{i}, b{i}, c{i}), they cannot be merged with others
    # 70 LUTs -> 70 CLBs. This should trigger CapacityError.
    with pytest.raises(CapacityError):
        GreedyPacker(max_clbs=64).run(mapped_nl)


def test_mapper_handles_deep_gate_chains():
    # a long single-input chain is absorbed into one cone; both the cone
    # traversal and the truth-table evaluation must survive depths beyond
    # default recursion limit (~1000)
    nl = Netlist("deep")
    a = nl.create_net("a", 1)
    nl.add_input("a", a)

    prev = a
    for i in range(1500):
        nxt = nl.create_net(f"n{i}", 1)
        nl.add_logic("BUF", [prev], [nxt])
        prev = nxt
    nl.outputs.append(prev)

    mapped = GreedyMapper(k_max=3).run(nl)

    luts = [n for n in mapped.nodes if isinstance(n, LUT)]
    assert len(luts) == 1
    assert luts[0].truth_table == 0b10  # identity of the single input


def _shared_gate_netlist() -> Netlist:
    # g = a & b feeds two cones: y1 = g ^ c and y2 = g | d
    nl = Netlist("shared")
    a = nl.create_net("a", 1)
    b = nl.create_net("b", 1)
    c = nl.create_net("c", 1)
    d = nl.create_net("d", 1)
    for name, net in (("a", a), ("b", b), ("c", c), ("d", d)):
        nl.add_input(name, net)

    g = nl.create_net("g", 1)
    y1 = nl.create_net("y1", 1)
    y2 = nl.create_net("y2", 1)
    nl.add_logic("AND", [a, b], [g])
    nl.add_logic("XOR", [g, c], [y1])
    nl.add_logic("OR", [g, d], [y2])
    nl.outputs.extend([y1, y2])
    return nl


def _check_shared_gate_behaviour(mapped: Netlist) -> None:
    sim = RTLSimulator(mapped)
    for a_val, b_val, c_val, d_val in itertools.product([0, 1], repeat=4):
        sim.set("a", a_val)
        sim.set("b", b_val)
        sim.set("c", c_val)
        sim.set("d", d_val)
        sim.step()
        g_val = a_val & b_val
        assert sim.get("y1") == (g_val ^ c_val)
        assert sim.get("y2") == (g_val | d_val)


def test_mapper_duplicates_shared_gates_by_default():
    # by default the shared AND is duplicated into both consuming LUTs:
    # two LUTs total, and the intermediate net 'g' disappears
    mapped = GreedyMapper(k_max=3).run(_shared_gate_netlist())

    luts = [n for n in mapped.nodes if isinstance(n, LUT)]
    assert len(luts) == 2
    assert mapped.get_net("g") is None
    _check_shared_gate_behaviour(mapped)


def test_mapper_can_keep_multi_sink_gates_shared():
    # with absorb_multi_sink_gates=False the shared AND gets its own LUT,
    # referenced by both consumers through the preserved net 'g'
    mapped = GreedyMapper(k_max=3, absorb_multi_sink_gates=False).run(_shared_gate_netlist())

    luts = [n for n in mapped.nodes if isinstance(n, LUT)]
    assert len(luts) == 3
    g_net = mapped.get_net("g")
    assert g_net is not None
    assert isinstance(g_net.drivers[0], LUT)
    assert len(g_net.sinks) == 2
    _check_shared_gate_behaviour(mapped)


#  connectivity-driven packing:
# Pairing is scored by shared input nets: two LUTs sharing all their inputs
# in one CLB eliminate whole nets from the routing problem. (Producer/consumer
# copacking deliberately earns nothing: the XC2064 input muxes only see
# A/B/C/D/Q, so a paired LUT's output still has to leave via X/Y and re-enter
# through a pin.)


def _lut(nl: Netlist, in_nets, out_name: str, truth_table: int) -> "LUT":
    out = nl.create_net(out_name, 1)
    lut = LUT(
        id=nl.next_node_id("lut"),
        inputs=list(in_nets),
        outputs=[out],
        truth_table=truth_table,
        k=3,
    )
    nl.nodes.append(lut)
    return lut


def test_packer_pairs_luts_by_shared_inputs():
    nl = Netlist("pairing")
    a = nl.create_net("a", 1)
    b = nl.create_net("b", 1)
    c = nl.create_net("c", 1)
    d = nl.create_net("d", 1)
    for name, net in (("a", a), ("b", b), ("c", c), ("d", d)):
        nl.add_input(name, net)

    _lut(nl, [a, b, c], "y1", 0x80)  # y1 = a & b & c
    _lut(nl, [a, d], "y2", 0x8)     # y2 = a & d
    _lut(nl, [a, b, c], "y3", 0xFE) # y3 = a | b | c
    y1, y2, y3 = nl.get_net("y1"), nl.get_net("y2"), nl.get_net("y3")
    nl.outputs.extend([y1, y2, y3])

    packed = GreedyPacker(max_clbs=64).run(nl)

    # y1 and y3 share all three inputs, a first fit packer pairs y1 with y2
    # (1 shared net) instead
    py1, py2, py3 = packed.get_net("y1"), packed.get_net("y2"), packed.get_net("y3")
    assert py1.drivers[0] is py3.drivers[0], "LUTs sharing all inputs should share a CLB"
    assert py2.drivers[0] is not py1.drivers[0]

    # behaviour preserved
    sim = RTLSimulator(packed)
    for a_v, b_v, c_v, d_v in itertools.product([0, 1], repeat=4):
        sim.set("a", a_v)
        sim.set("b", b_v)
        sim.set("c", c_v)
        sim.set("d", d_v)
        sim.step()
        assert sim.get("y1") == (a_v & b_v & c_v)
        assert sim.get("y2") == (a_v & d_v)
        assert sim.get("y3") == (a_v | b_v | c_v)


def test_packer_fills_g_slots_by_shared_inputs():
    from openxc2064.synthesis.rtl_nodes import DFF

    nl = Netlist("gslot")
    a = nl.create_net("a", 1)
    b = nl.create_net("b", 1)
    c = nl.create_net("c", 1)
    d = nl.create_net("d", 1)
    clk = nl.create_net("clk", 1)
    for name, net in (("a", a), ("b", b), ("c", c), ("d", d), ("clk", clk)):
        nl.add_input(name, net)

    # DFF driven by LUT_F(a, b, c) -> occupies a CLB with a free G slot
    f_lut = _lut(nl, [a, b, c], "f_out", 0x80)
    q = nl.create_net("q", 1)
    dff = DFF(id=nl.next_node_id("dff"), inputs=[f_lut.outputs[0], clk], outputs=[q])
    nl.nodes.append(dff)

    # candidates for the G slot: y_x shares 1 input with F, y_y shares all 3
    _lut(nl, [a, d], "y_x", 0x8)      # y_x = a & d
    _lut(nl, [a, b, c], "y_y", 0xFE)  # y_y = a | b | c
    y_x, y_y = nl.get_net("y_x"), nl.get_net("y_y")
    nl.outputs.extend([q, y_x, y_y])

    packed = GreedyPacker(max_clbs=64).run(nl)

    # the G slot of the DFF's CLB should hold y_y (3 shared inputs), not the
    # first-scanned y_x (1 shared input)
    pq, py_y = packed.get_net("q"), packed.get_net("y_y")
    assert pq.drivers[0] is py_y.drivers[0], "G slot should go to the max-shared-input LUT"

    # behaviour preserved (q latches a&b&c on the rising clock edge)
    sim = RTLSimulator(packed)
    for a_v, b_v, c_v, d_v in itertools.product([0, 1], repeat=4):
        sim.set("a", a_v)
        sim.set("b", b_v)
        sim.set("c", c_v)
        sim.set("d", d_v)
        sim.set("clk", 0)
        sim.step()
        sim.set("clk", 1)
        sim.step()
        assert sim.get("y_x") == (a_v & d_v)
        assert sim.get("y_y") == (a_v | b_v | c_v)
        assert sim.get("q") == (a_v & b_v & c_v)
