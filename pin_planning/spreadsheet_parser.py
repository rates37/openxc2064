from __future__ import annotations

import csv
import re
from pathlib import Path


COORDINATE_PATTERN = re.compile(r"\d+G\d+")

import matplotlib.pyplot as plt

    
    
def collect_coordinates_from_csv(csv_path: Path) -> set[str]:
	"""Scan every CSV cell and return unique coordinate-like values (e.g. 156G9)."""
	coordinates: set[str] = set()

	with csv_path.open(newline="", encoding="utf-8") as csv_file:
		reader = csv.reader(csv_file)
		for row in reader:
			for cell in row:
				if "PIP" in cell:
					coordinates.update(COORDINATE_PATTERN.findall(cell))

	return coordinates

def plot_coordinates_from_csv(csv_path: Path, out_path: Path = None):
    coordinates = collect_coordinates_from_csv(csv_path)
    points = [tuple(map(int, coord.split("G"))) for coord in coordinates]
    xs, ys = zip(*points) if points else ([], [])

    plt.figure(figsize=(6, 6))
    plt.scatter(xs, ys, s=10, color='blue')
    plt.title('Spreadsheet Coordinates')
    plt.axis('equal')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.tight_layout()
    if out_path is None:
        out_path = csv_path.with_suffix('.png')
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved plot to {out_path}")

def export_coordinates_to_ts(csv_path: Path, ts_path: Path = None):
    coordinates = collect_coordinates_from_csv(csv_path)
    xy_list = [
        {"x": int(coord.split("G")[0]), "y": int(coord.split("G")[1])}
        for coord in coordinates
    ]
    xy_list.sort(key=lambda c: (c["x"], c["y"]))
    if ts_path is None:
        ts_path = csv_path.with_suffix('.ts')
    with open(ts_path, 'w', encoding='utf-8') as f:
        f.write("// Auto-generated coordinate list\n")
        f.write("export const coordinates = [\n")
        for c in xy_list:
            f.write(f'  {{ x: {c["x"]}, y: {c["y"]} }},\n')
        f.write("];\n")
    print(f"Wrote {len(xy_list)} coordinates to {ts_path}")




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
	plot_coordinates_from_csv(default_csv)
	export_coordinates_to_ts(default_csv)