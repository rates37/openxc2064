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
    assert clbs[0].lut_f_init == 0xAA
    
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
