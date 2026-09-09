"""Pin assignments: a CSV pin file.

`PinConstraints` names physical banks (`AA_IO0`), which means knowing the
device's bank naming and slicing `pad_banks(...)` by hand. A pin assignment
file names edge slots instead. `N[0]` is the leftmost pad along the top
edge, `W[3]` the fourth down the left edge.

    # pin_assignments.csv
    To,Direction,Location
    clk,Input,OSC
    count[0],Output,N[0]
    count[1],Output,N[1]

Ranges are an openxc2064 extension for writing files by hand, your row can
cover a whole bus, in either direction:

    count[15:0],Output,N[0:15]

Reading back is one row per pin.

    plan = PinAssignments.from_file("pin_assignments.csv")
    config, placement, report = build(HDL, "counter", pins=plan)
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path

from openxc2064.device.fabric import Fabric

from .clocking import ClockSource
from .constraints import PinConstraints

EDGES = ("N", "E", "S", "W")
EDGE_NAMES = {"N": "north", "E": "east", "S": "south", "W": "west"}
OSCILLATOR_TOKEN = "OSC"

# column names:
COLUMN_SIGNAL = "to"
COLUMN_DIRECTION = "direction"
COLUMN_LOCATION = "location"
HEADER = ("To", "Direction", "Location")

DIRECTIONS = {"input": "Input", "output": "Output", "bidir": "Bidir"}

_SLOT = re.compile(r"^(?P<name>[A-Za-z_][A-Za-z_0-9]*)\[(?P<a>\d+)(?::(?P<b>\d+))?\]$")


class PinAssignmentError(Exception):
    """A pin file could not be parsed or resolved. Messages carry the source
    line so the file itself can be fixed."""


def _indices(first: int, second: int | None) -> list[int]:
    """The index list a `[a]` or `[a:b]` selector names, either direction."""
    if second is None:
        return [first]
    step = 1 if second >= first else -1
    return list(range(first, second + step, step))


@dataclass(frozen=True)
class PinAssignment:
    """One row of the file."""

    signal: str  # 'count' or 'clk'
    bits: tuple[int, ...] | None  # None when the row named a bare scalar
    location: str  # 'N', 'W', a bank id, or OSCILLATOR_TOKEN
    slots: tuple[int, ...] | None  # edge slot indices, None for OSC/bank ids
    direction: str | None  # 'Input' / 'Output', if the file said
    line: int

    @property
    def is_oscillator(self) -> bool:
        return self.location == OSCILLATOR_TOKEN

    @property
    def pads(self) -> list[str]:
        """The bit-level pad names this row assigns."""
        if self.bits is None:
            return [self.signal]
        return [f"{self.signal}[{bit}]" for bit in self.bits]


@dataclass
class PinAssignments:
    assignments: list[PinAssignment] = field(default_factory=list)
    source: str = "<string>"

    #! reading:
    @classmethod
    def parse(cls, text: str, source: str = "<string>") -> "PinAssignments":
        rows: list[PinAssignment] = []
        columns: dict[str, int] | None = None

        for number, raw in enumerate(text.splitlines(), start=1):
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            fields = next(csv.reader([raw]))
            fields = [f.strip() for f in fields]

            if columns is None:
                columns = cls._header(fields, number, source)
                continue

            signal = fields[columns[COLUMN_SIGNAL]] if len(fields) > columns[COLUMN_SIGNAL] else ""
            location = (
                fields[columns[COLUMN_LOCATION]] if len(fields) > columns[COLUMN_LOCATION] else ""
            )
            index = columns.get(COLUMN_DIRECTION)
            direction = fields[index] if index is not None and len(fields) > index else ""
            if not signal and not location:
                continue
            rows.append(cls._row(signal, location, direction, number, source))

        if columns is None:
            raise PinAssignmentError(
                f"{source}: no header row; expected a line naming at least "
                f"'{HEADER[0]}' and '{HEADER[2]}' columns"
            )

        plan = cls(assignments=rows, source=source)
        plan._check_unique()
        return plan

    @classmethod
    def from_file(cls, path: str | Path) -> "PinAssignments":
        path = Path(path)
        return cls.parse(path.read_text(encoding="utf-8"), source=str(path))

    @staticmethod
    def _header(fields: list[str], line: int, source: str) -> dict[str, int]:
        columns = {
            name.lower(): index
            for index, name in enumerate(fields)
            if name.lower() in (COLUMN_SIGNAL, COLUMN_DIRECTION, COLUMN_LOCATION)
        }
        missing = [
            name
            for name, key in (("To", COLUMN_SIGNAL), ("Location", COLUMN_LOCATION))
            if key not in columns
        ]
        if missing:
            raise PinAssignmentError(
                f"{source}:{line}: header is missing the "
                f"{' and '.join(repr(m) for m in missing)} column; got "
                f"{', '.join(repr(f) for f in fields)}"
            )
        return columns

    @staticmethod
    def _row(
        signal_field: str, location: str, direction: str, line: int, source: str
    ) -> PinAssignment:
        where = f"{source}:{line}"

        signal, bits = signal_field, None
        if (bit_match := _SLOT.match(signal_field)) is not None:
            signal = bit_match["name"]
            bits = tuple(
                _indices(
                    int(bit_match["a"]),
                    None if bit_match["b"] is None else int(bit_match["b"]),
                )
            )
        elif not signal_field.isidentifier():
            raise PinAssignmentError(f"{where}: {signal_field!r} is not a signal name")

        if direction and direction.lower() not in DIRECTIONS:
            raise PinAssignmentError(
                f"{where}: unknown direction {direction!r}; expected one of "
                f"{', '.join(DIRECTIONS.values())}"
            )
        normalised = DIRECTIONS[direction.lower()] if direction else None

        if location.upper() == OSCILLATOR_TOKEN:
            if bits is not None and len(bits) > 1:
                raise PinAssignmentError(
                    f"{where}: {OSCILLATOR_TOKEN} drives one signal, but "
                    f"{signal_field} is {len(bits)} bits"
                )
            return PinAssignment(signal, bits, OSCILLATOR_TOKEN, None, normalised, line)

        slots: tuple[int, ...] | None = None
        place = location
        if (slot_match := _SLOT.match(location)) is not None:
            place = slot_match["name"].upper()
            if place not in EDGES:
                raise PinAssignmentError(
                    f"{where}: unknown edge {slot_match['name']!r}; "
                    f"expected one of {', '.join(EDGES)}"
                )
            slots = tuple(
                _indices(
                    int(slot_match["a"]),
                    None if slot_match["b"] is None else int(slot_match["b"]),
                )
            )

        width = len(bits) if bits is not None else 1
        count = len(slots) if slots is not None else 1
        if width != count:
            raise PinAssignmentError(
                f"{where}: width mismatch — {signal_field} is {width} "
                f"{'bit' if width == 1 else 'bits'}, {location} is {count} "
                f"{'slot' if count == 1 else 'slots'}"
            )
        return PinAssignment(signal, bits, place, slots, normalised, line)

    def _check_unique(self) -> None:
        seen_signal: dict[str, int] = {}
        seen_slot: dict[tuple[str, int], tuple[str, int]] = {}
        for entry in self.assignments:
            for index, pad in enumerate(entry.pads):
                if pad in seen_signal:
                    raise PinAssignmentError(
                        f"{self.source}:{entry.line}: {pad} is assigned twice "
                        f"(also on line {seen_signal[pad]})"
                    )
                seen_signal[pad] = entry.line
                if entry.slots is None:
                    continue
                key = (entry.location, entry.slots[index])
                if key in seen_slot:
                    other, other_line = seen_slot[key]
                    raise PinAssignmentError(
                        f"{self.source}:{entry.line}: {entry.location}"
                        f"[{entry.slots[index]}] is claimed by both {other} "
                        f"(line {other_line}) and {pad}"
                    )
                seen_slot[key] = (pad, entry.line)

    #! resolution:
    def clock_source(self) -> ClockSource | None:
        """OSCILLATOR if a signal is assigned to OSC, else None (meaning the
        file does not care and the default applies)."""
        return (
            ClockSource.OSCILLATOR
            if any(entry.is_oscillator for entry in self.assignments)
            else None
        )

    def oscillator_signals(self) -> list[str]:
        return [entry.signal for entry in self.assignments if entry.is_oscillator]

    def to_constraints(self, fabric: Fabric) -> PinConstraints:
        """Resolve every edge slot against `fabric` into pad -> bank
        constraints. Signals assigned to OSC are skipped."""
        pads: dict[str, str] = {}
        edge_banks = {edge: fabric.pad_banks(edge=edge) for edge in EDGES}

        for entry in self.assignments:
            if entry.is_oscillator:
                continue
            for index, pad in enumerate(entry.pads):
                pads[pad] = self._bank(entry, index, edge_banks, fabric)
        return PinConstraints(pads)

    def direction_problems(self, design) -> list[str]:
        """Rows whose stated Direction disagrees with the design."""
        actual = {}
        for iob in design.iobs.values():
            actual[iob.pad_name] = "Output" if iob.is_output else "Input"

        problems = []
        for entry in self.assignments:
            if entry.direction is None:
                continue
            for pad in entry.pads:
                want = actual.get(pad) or actual.get(f"{pad}[0]")
                if want is not None and want != entry.direction:
                    problems.append(
                        f"{self.source}:{entry.line}: {pad} is declared "
                        f"{entry.direction} but the design has it as {want}"
                    )
        return problems

    def _bank(
        self,
        entry: PinAssignment,
        index: int,
        edge_banks: dict[str, list[str]],
        fabric: Fabric,
    ) -> str:
        if entry.slots is None:  # a literal bank id, the escape hatch
            if entry.location not in fabric.io_banks:
                raise PinAssignmentError(
                    f"{self.source}:{entry.line}: {entry.location!r} is neither "
                    f"an edge slot (like N[0]) nor a bank on this device"
                )
            return entry.location

        banks = edge_banks[entry.location]
        slot = entry.slots[index]
        if slot >= len(banks):
            edge = entry.location
            raise PinAssignmentError(
                f"{self.source}:{entry.line}: {edge}[{slot}] is out of range — "
                f"the {EDGE_NAMES[edge]} edge has {len(banks)} pads "
                f"({edge}[0]..{edge}[{len(banks) - 1}])"
            )
        return banks[slot]

    #! writing:
    def to_csv(self, comment: str | None = None) -> str:
        """One row per pin, the way Quartus writes them."""
        out = io.StringIO()
        if comment:
            for text in comment.splitlines():
                out.write(f"# {text}\n")
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(HEADER)
        for entry in self.assignments:
            for index, pad in enumerate(entry.pads):
                if entry.slots is None:
                    location = entry.location
                else:
                    location = f"{entry.location}[{entry.slots[index]}]"
                writer.writerow([pad, entry.direction or "", location])
        return out.getvalue()

    @classmethod
    def from_placement(cls, placement, design, fabric: Fabric) -> "PinAssignments":
        """Back-annotate: turn a placement's pad assignment into a pin file."""
        from .placement import OSCILLATOR_SITE

        slot_of = {
            bank: (edge, index)
            for edge in EDGES
            for index, bank in enumerate(fabric.pad_banks(edge=edge))
        }

        rows: list[PinAssignment] = []
        for node_id in sorted(design.iobs, key=lambda n: design.iobs[n].pad_name):
            iob = design.iobs[node_id]
            site = placement.iob_sites.get(node_id)
            if site is None:
                continue

            pad = iob.pad_name
            signal, bits = pad, None
            if (m := _SLOT.match(pad)) is not None and m["b"] is None:
                signal, bits = m["name"], (int(m["a"]),)

            direction = "Output" if iob.is_output else "Input"
            if site == OSCILLATOR_SITE:
                location, slots = OSCILLATOR_TOKEN, None
            else:
                edge, index = slot_of[site]
                location, slots = edge, (index,)
            rows.append(PinAssignment(signal, bits, location, slots, direction, len(rows) + 1))

        # bus bits sort lexically above ('count[10]' before 'count[2]').
        # order them numerically so the file reads like the bus does
        rows.sort(key=lambda r: (r.signal, r.bits[0] if r.bits else -1))
        return cls(assignments=rows, source="<placement>")
