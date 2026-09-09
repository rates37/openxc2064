"""Optional pin (pad) assignment constraints for placement.

By default the placer is free to put every top-level port on any pad bank,
which minimises wire length but scatters multibit wires across the device. A
`PinConstraints` map pins chosen pads to chosen banks; everything left
unconstrained still anneals exactly as before.

Pad names are the bit-level port names the front end produces: a scalar port
`clk` becomes the pad `clk[0]`, and a bus `count` becomes `count[0]`..`count[n]`.
A bare scalar name is accepted as a convenience when it is unambiguous.

    pins = PinConstraints({"clk": "AA_IO0"})
    pins.assign_bus("count", fabric.pad_banks(edge="N")[4:12])
    config, placement, report = build(hdl, "counter", fabric=fabric, pins=pins)
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from openxc2064.device.fabric import Fabric

from .design_view import DesignView


class PinConstraintError(Exception):
    """Error for when a pin constraint cannot be honoured,
    either an unknown pad or bank, a bank with no physical pad,
    or two pads competing for one bank."""


@dataclass
class PinConstraints:
    """Maps top-level pad names to IO bank IDs. An empty instance means
    'place every pad freely', i.e. the default behaviour."""

    pins: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.pins = dict(self.pins)

    def __bool__(self) -> bool:
        return bool(self.pins)

    #! building:
    def assign(self, pad: str, bank: str) -> "PinConstraints":
        """Pin one pad to one bank. Returns self so calls can chain."""
        self.pins[pad] = bank
        return self

    def assign_bus(self, port: str, banks: Sequence[str]) -> "PinConstraints":
        """Pin `port[i]` to `banks[i]` — the usual way to lay a bus out along a
        physical row of pads. Returns self so calls can chain."""
        for index, bank in enumerate(banks):
            self.pins[f"{port}[{index}]"] = bank
        return self

    def assign_buses(
        self, buses: Sequence[tuple[str, int]], banks: Sequence[str]
    ) -> "PinConstraints":
        """Lay several buses out over one pool of banks, each taking the next
        contiguous run. `buses` is (port, width) pairs. A pool built from
        `fabric.pad_banks(edge=...)` slices keeps each bus in pad order.

            pins.assign_buses([("a", 8), ("b", 8)], fabric.pad_banks(edge="N"))

        Raises PinConstraintError if the pool is too small to hold them all.
        Returns self so calls can chain."""
        needed = sum(width for _, width in buses)
        if needed > len(banks):
            names = ", ".join(f"{port}[{width}]" for port, width in buses)
            raise PinConstraintError(
                f"{needed} pads needed for {names}, but only {len(banks)} banks "
                "were given; pass a larger pool (e.g. more edges) or narrow the buses"
            )
        offset = 0
        for port, width in buses:
            self.assign_bus(port, banks[offset : offset + width])
            offset += width
        return self

    #! serialisation:
    def to_json(self) -> str:
        return json.dumps(self.pins, indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> "PinConstraints":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise PinConstraintError("pin constraints json must be a dict")
        return cls({str(k): str(v) for k, v in data.items()})

    #! resolution:
    def resolve(self, design: DesignView, fabric: Fabric) -> dict[str, str]:
        """Validate against the design and fabric, returning IOB node id ->
        bank id. Raises PinConstraintError with an actionable message."""
        by_pad: dict[str, list[str]] = {}
        for node_id, iob in design.iobs.items():
            by_pad.setdefault(iob.pad_name, []).append(node_id)

        resolved: dict[str, str] = {}
        claimed: dict[str, str] = {}  # bank -> pad, to spot collisions
        for pad, bank in sorted(self.pins.items()):
            target = self._resolve_pad(pad, by_pad)

            if bank not in fabric.io_banks:
                raise PinConstraintError(
                    f"pad '{pad}' is pinned to unknown IO bank '{bank}'"
                )
            if not fabric.io_banks[bank].has_pad:
                raise PinConstraintError(
                    f"pad '{pad}' is pinned to bank '{bank}', which has no "
                    "physical pad"
                )
            if bank in claimed:
                raise PinConstraintError(
                    f"IO bank '{bank}' is claimed by both '{claimed[bank]}' and "
                    f"'{pad}'; each bank drives one pad"
                )

            claimed[bank] = pad
            node_ids = by_pad[target]
            if len(node_ids) > 1:
                raise PinConstraintError(
                    f"pad name '{target}' maps to {len(node_ids)} IOB nodes; "
                    "cannot pin it unambiguously"
                )
            if node_ids[0] in resolved:
                raise PinConstraintError(
                    f"pad '{target}' is pinned more than once (to "
                    f"'{resolved[node_ids[0]]}' and '{bank}')"
                )
            resolved[node_ids[0]] = bank
        return resolved

    @staticmethod
    def _resolve_pad(pad: str, by_pad: dict[str, list[str]]) -> str:
        if pad in by_pad:
            return pad

        # scalar convenience: 'clk' -> 'clk[0]', but only when unambiguous
        bits = sorted(name for name in by_pad if name.startswith(f"{pad}["))
        if len(bits) == 1:
            return bits[0]
        if len(bits) > 1:
            raise PinConstraintError(
                f"'{pad}' is {len(bits)} bits wide ({bits[0]}..{bits[-1]}); pin "
                f"each bit by name or use assign_bus('{pad}', banks)"
            )
        available = ", ".join(sorted(by_pad)) or "(none)"
        raise PinConstraintError(
            f"no top-level pad named '{pad}' in this design; available pads: "
            f"{available}"
        )


def coerce_pins(
    pins: "PinConstraints | Mapping[str, str] | None",
) -> PinConstraints:
    """Accept a PinConstraints, a plain {pad: bank} mapping, or None."""
    if pins is None:
        return PinConstraints()
    if isinstance(pins, PinConstraints):
        return pins
    return PinConstraints(dict(pins))
