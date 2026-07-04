import pytest
from openxc2064.hdl import parse_hdl
from openxc2064.synthesis import HDLElaborator, Synthesiser, Optimiser
from openxc2064.synthesis.rtl_nodes import Constant, Netlist
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


class TestNodeIdUniqueness:
    def test_ids_stay_unique_after_node_removal(self) -> None:
        nl = Netlist("t")
        a = nl.create_net("a")
        b = nl.create_net("b")
        c = nl.create_net("c")
        g0 = nl.add_logic("BUF", [a], [b])
        g1 = nl.add_logic("BUF", [b], [c])

        # a pass removes a node
        nl.nodes.remove(g0)

        # then a later-minted node must not reuse a live node's ID
        d = nl.create_net("d")
        g2 = nl.add_logic("BUF", [a], [d])
        assert g2.id != g1.id

    def test_optimiser_constant_fold_does_not_reuse_live_node_id(self) -> None:
        # Constructed so that, with IDs minted from len(nodes), the constant created
        # by folding `a & 0` collides with the ID of the still-live zero constant:
        # trimming the two dead gates first shrinks nodes back to 3 elements, so the
        # fold mints "const3" while the original "const3" is still in the netlist.
        # The colliding dead node is then wrongly kept alive by ID-based liveness.
        nl = Netlist("t")
        a = nl.create_net("a")
        nl.add_input("a", a)  # node 0
        nl.inputs.append(a)

        dead1 = nl.create_net("dead1")
        nl.add_logic("NOT", [a], [dead1])  # node 1, dead
        dead2 = nl.create_net("dead2")
        nl.add_logic("NOT", [a], [dead2])  # node 2, dead

        zero = nl.create_net("zero")
        nl.add_const(0, zero)  # node 3

        y = nl.create_net("y")
        nl.add_logic("AND", [a, zero], [y])  # node 4, folds to const 0
        nl.outputs.append(y)

        Optimiser().optimise(nl)

        ids = [n.id for n in nl.nodes]
        assert len(ids) == len(set(ids)), f"duplicate node ids after optimise: {ids}"

        # y should have collapsed to a constant 0, with the AND and the original zero-constant trimmed away
        assert len(y.drivers) == 1
        assert isinstance(y.drivers[0], Constant)
        assert y.drivers[0].value == 0
        assert len(nl.nodes) == 2  # the input and the folded constant


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
