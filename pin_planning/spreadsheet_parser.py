from __future__ import annotations

import csv
import re
from pathlib import Path


COORDINATE_PATTERN = re.compile(r"\b\d+G\d+\b")


def collect_coordinates_from_csv(csv_path: Path) -> set[str]:
	"""Scan every CSV cell and return unique coordinate-like values (e.g. 156G9)."""
	coordinates: set[str] = set()

	with csv_path.open(newline="", encoding="utf-8") as csv_file:
		reader = csv.reader(csv_file)
		for row in reader:
			for cell in row:
				coordinates.update(COORDINATE_PATTERN.findall(cell))

	return coordinates


def print_coordinates_from_csv(csv_path: Path) -> None:
	coordinates = collect_coordinates_from_csv(csv_path)
	sorted_coordinates = sorted(
		coordinates,
		key=lambda coordinate: tuple(int(part) for part in coordinate.split("G")),
	)
	x_values = sorted({int(coordinate.split("G")[0]) for coordinate in sorted_coordinates})
	y_values = sorted({int(coordinate.split("G")[1]) for coordinate in sorted_coordinates})

	print("Unique XG Y coordinates:")
	for coordinate in sorted_coordinates:
		print(coordinate)

	print("\nUnique X coordinates:")
	print(len(x_values))

	for x_value in x_values:
		print(x_value)

	print("\nUnique Y coordinates:")
	print(len(y_values))
	for y_value in y_values:
		print(y_value)


if __name__ == "__main__":
	default_csv = Path(__file__).with_name("XC2064-spreadsheet.csv")
	print_coordinates_from_csv(default_csv)
