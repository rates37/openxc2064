import pytest
import itertools
from openxc2064.synthesis.rtl_nodes import Netlist, Constant, LogicGate
from openxc2064.mapping.xc2064_primitives import LUT, CLB, IOB
from openxc2064.mapping.mapper import GreedyMapper
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

