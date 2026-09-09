"""The examples are the first thing a reader runs, so run them here too."""

import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLES = Path(__file__).parent.parent / "examples"


@pytest.mark.parametrize(
    "script, expected",
    [
        ("counter/counter.py", ["Pads used:   55 of 58", "counting:   1 2 3 4 5 6 7 8"]),
        ("six_counters/six_counters.py", ["saved "]),
    ],
)
def test_example_runs(script, expected, tmp_path):
    # from an unrelated cwd: the scripts must find their own pin files
    result = subprocess.run(
        [sys.executable, str(EXAMPLES / script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, result.stderr
    for line in expected:
        assert line in result.stdout, f"{script}: missing {line!r}\n{result.stdout}"


def test_examples_are_listed_in_the_readme():
    readme = (EXAMPLES / "README.md").read_text(encoding="utf-8")
    for script in EXAMPLES.glob("*/*.py"):
        assert script.name in readme, f"{script.name} is not mentioned in examples/README.md"


def test_each_example_is_self_contained():
    """One directory per example: a script and the pin file it reads."""
    for directory in sorted(p for p in EXAMPLES.iterdir() if p.is_dir()):
        assert (directory / "pin_assignments.csv").is_file(), directory
        assert list(directory.glob("*.py")), directory
