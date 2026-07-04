/**
 * Exports the fabric config objects to JSON for the Python toolchain.
 *
 * Run from the simulator directory via `npm run export-configs`.
 * Output: ../src/openxc2064/device/data/xc2064_{8x8,3x3}.json
 *
 * The Python fabric model (src/openxc2064/device/fabric.py) treats these
 * files as its source of truth; re-run this after any change to
 * src/configs/configs_8x8.ts or configs_3x3.ts so they cannot drift.
 */
import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { exportAllConfigs as export8x8, NUM_CELLS as NUM_CELLS_8 } from '../src/configs/configs_8x8';
import { exportAllConfigs as export3x3, NUM_CELLS as NUM_CELLS_3 } from '../src/configs/configs_3x3';

// npm always runs scripts with cwd = the package directory (simulator/)
const outDir = join(process.cwd(), '..', 'src', 'openxc2064', 'device', 'data');
mkdirSync(outDir, { recursive: true });

function write(filename: string, configJson: string, numCells: number): void {
	const data = JSON.parse(configJson);
	data.num_cells = numCells;
	const outPath = join(outDir, filename);
	writeFileSync(outPath, JSON.stringify(data, null, '\t') + '\n');
	console.log(`wrote ${outPath} (${numCells}x${numCells})`);
}

write('xc2064_8x8.json', export8x8(), NUM_CELLS_8);
write('xc2064_3x3.json', export3x3(), NUM_CELLS_3);
