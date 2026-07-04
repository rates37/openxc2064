import pytest
from openxc2064.hdl import parse_hdl
from openxc2064.synthesis import HDLElaborator, Synthesiser, Optimiser
from openxc2064.synthesis.rtl_nodes import Netlist
from openxc2064.synthesis.synthesis import SynthesisException


class TestNetlistNameIndex:
    def test_get_net_returns_the_created_net(self) -> None:
        nl = Netlist("t")
        a = nl.create_net("a", 4)
        assert nl.get_net("a") is a

    def test_get_net_unknown_name_returns_none(self) -> None:
        nl = Netlist("t")
        assert nl.get_net("missing") is None

    def test_duplicate_net_name_raises(self) -> None:
        nl = Netlist("t")
        nl.create_net("a")
        with pytest.raises(ValueError, match="'a'"):
            nl.create_net("a")

    def test_trim_dead_code_keeps_index_in_sync(self) -> None:
        nl = Netlist("t")
        a = nl.create_net("a")
        nl.add_input("a", a)
        nl.inputs.append(a)

        y = nl.create_net("y")
        nl.add_logic("BUF", [a], [y])
        nl.outputs.append(y)

        # dead gate: drives a net that never reaches an output
        dead = nl.create_net("dead")
        nl.add_logic("XOR", [a, a], [dead])

        Optimiser().optimise(nl)

        assert nl.get_net("dead") is None
        assert nl.get_net("y") is y
        assert nl.get_net("a") is a


class TestSynthesiserNameCollisions:
    def test_instance_port_flattened_name_collision_is_loud(self) -> None:
        hdl = """module inv(input in_sig, output out_sig);
    assign out_sig = !in_sig;
endmodule

module top(input a, output z);
    wire u0_out_sig;
    inv u0 (.in_sig(a), .out_sig(u0_out_sig));
    assign z = u0_out_sig;
endmodule
"""
        ast = parse_hdl(hdl)
        library = HDLElaborator(ast).get_library()
        with pytest.raises(SynthesisException, match="u0_out_sig"):
            Synthesiser(library).synthesise("top")
