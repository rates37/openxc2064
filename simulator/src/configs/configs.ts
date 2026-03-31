import { Net, Pip } from '../types';
import { CELL_WIDTH, CELL_HEIGHT, MATRIX_WIDTH, MATRIX_HEIGHT, IO_WIDTH, IO_HEIGHT, CLK_TOP } from './constants';

export type ConfigTypes = 'logic_cell' | 'bus' | 'switch_matrix' | 'io';

export default function getConfig(device: ConfigTypes, id: string): any {
	switch (device) {
		case 'logic_cell': {
			const matches = logic_cell_config.filter((config) => config.ids.includes(id));
			if (matches.length === 0) return undefined;
			const allNets = matches.flatMap((m) => m.nets);
			const netMap = new Map<string, Net>();
			for (const net of allNets) {
				netMap.set(net.id, net);
			}
			const nets = Array.from(netMap.values());
			return {
				nets: nets.map((net) => ({ ...net, points: net.points.map((p) => ({ ...p })) })),
				pips: matches.flatMap((m) => m.pips).map((pip) => ({ ...pip, pos: { ...pip.pos } })),
			};
		}
		case 'bus':
			return bus_config;
		case 'switch_matrix': {
			const matches = switch_matrix_config.filter((config) => config.ids.includes(id));
			if (matches.length === 0) return undefined;
			const allMatrices = matches.flatMap((m) => m.matrices);
			return allMatrices.map((matrix) => ({
				nets: matrix?.nets.map((net) => ({ ...net, points: net.points.map((p) => ({ ...p })) })),
				pos: matrix?.pos ? { ...matrix.pos } : undefined,
			}));
		}
		case 'io': {
			const matches = io_config.filter((config) => config.ids.includes(id));
			if (matches.length === 0) return undefined;
			const allIoBanks = matches.flatMap((m) => m.io_bank);
			return allIoBanks.map((io_bank) => ({
				nets: io_bank?.nets.map((net) => ({ ...net, points: net.points.map((p) => ({ ...p })) })),
				pos: io_bank?.pos ? { ...io_bank.pos } : undefined,
				size: io_bank?.size ? { ...io_bank.size } : undefined,
				pads: io_bank?.pads ? io_bank.pads.map((pad) => ({ pos: { ...pad.pos }, size: { ...pad.size } })) : undefined,
			}));
		}
		default:
			throw new Error(`Unknown device type: ${device}`);
	}
}

function id_range(expr: string): string[] {
	const parts: string[][] = [];
	let i = 0;

	while (i < expr.length) {
		if (expr[i] === '[') {
			const end = expr.indexOf(']', i);
			const inside = expr.slice(i + 1, end); // e.g. A-H
			const [a, b] = inside.split('-');

			const start = a.charCodeAt(0);
			const stop = b.charCodeAt(0);

			const chars: string[] = [];
			for (let c = start; c <= stop; c++) {
				chars.push(String.fromCharCode(c));
			}

			parts.push(chars);
			i = end + 1;
		} else {
			parts.push([expr[i]]);
			i++;
		}
	}

	// cartesian product
	return parts.reduce<string[]>((acc, set) => acc.flatMap((a) => set.map((b) => a + b)), ['']);
}

const range = (start: number, end: number): number[] => {
	const arr: number[] = [];
	for (let i = start; i <= end; i++) {
		arr.push(i);
	}
	return arr;
};

const logic_cell_config: { ids: string[]; nets: Net[]; pips: Pip[] }[] = [
	{
		/**
		 *
		 * DEFAULT CONFIG
		 *
		 */
		// "Defualt" config for all cells. Only needed because the internals of each CLB (muxes, luts, clks, etc) need to be initialised for the simulation to work.
		ids: id_range('[A-H][A-H]'),
		nets: [
			// Init all nets
			{ id: 'net_A', value: false, points: [] },
			{ id: 'net_B', value: false, points: [] },
			{ id: 'net_C', value: false, points: [] },
			{ id: 'net_D', value: false, points: [] },
			{ id: 'net_E', value: false, points: [] },
			{ id: 'net_F', value: false, points: [] },
			{ id: 'net_G', value: false, points: [] },
			{ id: 'net_K', value: false, points: [] },
			{ id: 'net_Q', value: false, points: [] },
			{ id: 'net_R', value: false, points: [] },
			{ id: 'net_S', value: false, points: [] },
			{ id: 'net_X', value: false, points: [] },
			{ id: 'net_Y', value: false, points: [] },
			{ id: 'net_gnd', value: false, points: [] },
			{ id: 'net_m6_out', value: false, points: [] },
			{ id: 'net_m8_out', value: false, points: [] },
			{ id: 'net_m13_out', value: false, points: [] },
			{ id: 'net_m18_out', value: false, points: [] },
			{ id: 'net_m20_out', value: false, points: [] },
			{ id: 'net_m24_out', value: false, points: [] },
			{ id: 'net_clk_1_out', value: false, points: [] },
			{ id: 'net_clk_2_out', value: false, points: [] },
		],
		pips: [],
	},

	/**
	 *
	 * PIN A CONFIGURATION
	 *
	 */
	{
		// All cells with standard pin A),
		// exluding top side because their pin As connect to the IO banks,
		// and exclduing the left side, because the pin As connect to M2 and M3 of the northern cell, not the north west cell
		ids: id_range('[B-H][B-H]'),
		nets: [
			{
				id: 'net_A',
				value: false,
				points: [
					{ x: 60, y: -CELL_HEIGHT / 2 },
					{ x: 60, y: -(CELL_HEIGHT / 2 + 160) },
				],
			},
		],
		pips: [
			{ id: 'pip_0', source: 'NW_M0.net_2', destination: 'net_A', enabled: false, pos: { x: 160, y: -160 }, bidirectional: false },
			{ id: 'pip_1', source: 'NW_M0.net_3', destination: 'net_A', enabled: false, pos: { x: 160, y: -140 }, bidirectional: false },
			{ id: 'pip_2', source: 'NW_M1.net_2', destination: 'net_A', enabled: false, pos: { x: 160, y: -120 }, bidirectional: false },
			{ id: 'pip_3', source: 'NW_M1.net_3', destination: 'net_A', enabled: false, pos: { x: 160, y: -100 }, bidirectional: false },
			{ id: 'pip_4', source: 'global_HU.net_0', destination: 'net_A', enabled: false, pos: { x: 160, y: -60 }, bidirectional: false },
		],
	},
	{
		// Port A, for all cells on the left edge except the top left corner (AA).
		ids: id_range('[B-H]A'),
		nets: [
			{
				id: 'net_A',
				value: false,
				points: [
					{ x: 60, y: -CELL_HEIGHT / 2 },
					{ x: 60, y: -(CELL_HEIGHT / 2 + 160) },
				],
			},
		],
		pips: [
			{ id: 'pip_0', source: 'N_M2.net_2', destination: 'net_A', enabled: false, pos: { x: 160, y: -160 }, bidirectional: false },
			{ id: 'pip_1', source: 'N_M2.net_3', destination: 'net_A', enabled: false, pos: { x: 160, y: -140 }, bidirectional: false },
			{ id: 'pip_2', source: 'N_M3.net_2', destination: 'net_A', enabled: false, pos: { x: 160, y: -120 }, bidirectional: false },
			{ id: 'pip_3', source: 'N_M3.net_3', destination: 'net_A', enabled: false, pos: { x: 160, y: -100 }, bidirectional: false },
			{ id: 'pip_4', source: 'global_HU.net_0', destination: 'net_A', enabled: false, pos: { x: 160, y: -60 }, bidirectional: false },
		],
	},

	/**
	 *
	 * PIN B CONFIGURATION
	 *
	 */

	{
		// All cells with the standard pin B,
		// only excludes the left edge, as the wires are extended to meet with the IO channels
		ids: id_range('[A-H][B-H]'),
		nets: [
			{
				id: 'net_B',
				value: false,
				points: [
					{ x: -CELL_WIDTH / 2, y: -40 },
					{ x: -CELL_WIDTH / 2 - 240, y: -40 },
				],
			},
		],
		pips: [
			{ id: 'pip_4', source: 'W_M0.net_0', destination: 'net_B', enabled: false, pos: { x: -240, y: 120 }, bidirectional: false },
			{ id: 'pip_5', source: 'W_M0.net_1', destination: 'net_B', enabled: false, pos: { x: -220, y: 120 }, bidirectional: false },
			{ id: 'pip_6', source: 'W_M1.net_0', destination: 'net_B', enabled: false, pos: { x: -200, y: 120 }, bidirectional: false },
			{ id: 'pip_7', source: 'W_M1.net_1', destination: 'net_B', enabled: false, pos: { x: -180, y: 120 }, bidirectional: false },
			{
				id: 'pip_v2_0',
				source: 'global_VL.net_0',
				destination: 'net_B',
				enabled: false,
				pos: { x: -CELL_WIDTH / 2, y: 120 },
				bidirectional: false,
			},
			{
				id: 'pip_v2_0',
				source: 'global_VL.net_1',
				destination: 'net_B',
				enabled: false,
				pos: { x: -CELL_WIDTH / 2 + 20, y: 120 },
				bidirectional: false,
			},
			{
				id: 'pip_v2_0',
				source: 'global.net_clk',
				destination: 'net_B',
				enabled: false,
				pos: { x: -CELL_WIDTH / 2 + 40, y: 120 },
				bidirectional: false,
			},
		],
	},
	{
		// Port B, for all cells on the left edge
		ids: id_range('[A-G]A'),
		nets: [
			{
				id: 'net_B',
				value: false,
				points: [
					{ x: -CELL_WIDTH / 2, y: -40 },
					{ x: -CELL_WIDTH / 2 - 240 - 60, y: -40 },
				],
			},
		],
		pips: [
			{ id: 'pip_4', source: 'T_M2.net_0', destination: 'net_B', enabled: false, pos: { x: -240 - 60, y: 120 }, bidirectional: false },
			{ id: 'pip_5', source: 'T_M2.net_1', destination: 'net_B', enabled: false, pos: { x: -220 - 60, y: 120 }, bidirectional: false },
			{ id: 'pip_6', source: 'T_M3.net_0', destination: 'net_B', enabled: false, pos: { x: -200 - 60, y: 120 }, bidirectional: false },
			{ id: 'pip_7', source: 'T_M3.net_1', destination: 'net_B', enabled: false, pos: { x: -180 - 60, y: 120 }, bidirectional: false },
			{ id: 'pip_12', source: 'global_VL.net_0', destination: 'net_B', enabled: false, pos: { x: -140 - 60, y: 120 }, bidirectional: false },
			{ id: 'pip_12', source: 'global_VL.net_1', destination: 'net_B', enabled: false, pos: { x: -120 - 60, y: 120 }, bidirectional: false },
			{ id: 'pip_12', source: 'global.net_clk', destination: 'net_B', enabled: false, pos: { x: -100 - 60, y: 120 }, bidirectional: false },
			{ id: 'pip_8', source: 'global_VIOL.net_0', destination: 'net_B', enabled: false, pos: { x: -260 - 60, y: 120 }, bidirectional: false },
		],
	},
	{
		// Port B, for the bespoke bottom left corner :(
		ids: id_range('HA'),
		nets: [
			{
				id: 'net_B',
				value: false,
				points: [
					{ x: -CELL_WIDTH / 2, y: -40 },
					{ x: -CELL_WIDTH / 2 - 240 - 60, y: -40 },
				],
			},
		],
		pips: [
			{ id: 'pip_4', source: 'N_M2.net_5', destination: 'net_B', enabled: false, pos: { x: -240 - 60, y: 120 }, bidirectional: false },
			{ id: 'pip_5', source: 'N_M2.net_4', destination: 'net_B', enabled: false, pos: { x: -220 - 60, y: 120 }, bidirectional: false },
			{ id: 'pip_6', source: 'N_M3.net_5', destination: 'net_B', enabled: false, pos: { x: -200 - 60, y: 120 }, bidirectional: false },
			{ id: 'pip_7', source: 'N_M3.net_4', destination: 'net_B', enabled: false, pos: { x: -180 - 60, y: 120 }, bidirectional: false },
			{ id: 'pip_12', source: 'global_VL.net_0', destination: 'net_B', enabled: false, pos: { x: -140 - 60, y: 120 }, bidirectional: false },
			{ id: 'pip_12', source: 'global_VL.net_1', destination: 'net_B', enabled: false, pos: { x: -120 - 60, y: 120 }, bidirectional: false },
			{ id: 'pip_12', source: 'global.net_clk', destination: 'net_B', enabled: false, pos: { x: -100 - 60, y: 120 }, bidirectional: false },
			{ id: 'pip_8', source: 'global_VIOL.net_0', destination: 'net_B', enabled: false, pos: { x: -260 - 60, y: 120 }, bidirectional: false },
		],
	},

	/**
	 *
	 * PIN C CONFIGURATION
	 *
	 */
	{
		// All cells with the standard pin C,
		ids: id_range('[A-H][B-H]'),
		nets: [
			{
				id: 'net_C',
				value: false,
				points: [
					{ x: -CELL_WIDTH / 2, y: 20 },
					{ x: -CELL_WIDTH / 2 - 240, y: 20 },
				],
			},
		],
		pips: [
			{ id: 'pip_8', source: 'W_M0.net_0', destination: 'net_C', enabled: false, pos: { x: -240, y: 180 }, bidirectional: false },
			{ id: 'pip_9', source: 'W_M0.net_1', destination: 'net_C', enabled: false, pos: { x: -220, y: 180 }, bidirectional: false },
			{ id: 'pip_10', source: 'W_M1.net_0', destination: 'net_C', enabled: false, pos: { x: -200, y: 180 }, bidirectional: false },
			{ id: 'pip_11', source: 'W_M1.net_1', destination: 'net_C', enabled: false, pos: { x: -180, y: 180 }, bidirectional: false },
			{
				id: 'pip_v2_0',
				source: 'global_VL.net_0',
				destination: 'net_C',
				enabled: false,
				pos: { x: -CELL_WIDTH / 2, y: 180 },
				bidirectional: false,
			},
			{
				id: 'pip_v2_0',
				source: 'global_VL.net_1',
				destination: 'net_C',
				enabled: false,
				pos: { x: -CELL_WIDTH / 2 + 20, y: 180 },
				bidirectional: false,
			},
		],
	},
	{
		// Port C, for all cells on the left edge
		ids: id_range('[A-G]A'),
		nets: [
			{
				id: 'net_C',
				value: false,
				points: [
					{ x: -CELL_WIDTH / 2, y: 20 },
					{ x: -CELL_WIDTH / 2 - 240 - 60, y: 20 },
				],
			},
		],
		pips: [
			{ id: 'pip_8', source: 'T_M2.net_0', destination: 'net_C', enabled: false, pos: { x: -240 - 60, y: 180 }, bidirectional: false },
			{ id: 'pip_9', source: 'T_M2.net_1', destination: 'net_C', enabled: false, pos: { x: -220 - 60, y: 180 }, bidirectional: false },
			{ id: 'pip_10', source: 'T_M3.net_0', destination: 'net_C', enabled: false, pos: { x: -200 - 60, y: 180 }, bidirectional: false },
			{ id: 'pip_11', source: 'T_M3.net_1', destination: 'net_C', enabled: false, pos: { x: -180 - 60, y: 180 }, bidirectional: false },
			{ id: 'pip_12', source: 'global_VL.net_0', destination: 'net_C', enabled: false, pos: { x: -140 - 60, y: 180 }, bidirectional: false },
			{ id: 'pip_12', source: 'global_VL.net_1', destination: 'net_C', enabled: false, pos: { x: -120 - 60, y: 180 }, bidirectional: false },
			{ id: 'pip_12', source: 'global_VIOL.net_0', destination: 'net_C', enabled: false, pos: { x: -260 - 60, y: 180 }, bidirectional: false },
		],
	},
	{
		// Port C, for the bottom left bespoke case
		ids: id_range('HA'),
		nets: [
			{
				id: 'net_C',
				value: false,
				points: [
					{ x: -CELL_WIDTH / 2, y: 20 },
					{ x: -CELL_WIDTH / 2 - 240 - 60, y: 20 },
				],
			},
		],
		pips: [
			{ id: 'pip_8', source: 'N_M2.net_5', destination: 'net_C', enabled: false, pos: { x: -240 - 60, y: 180 }, bidirectional: false },
			{ id: 'pip_9', source: 'N_M2.net_4', destination: 'net_C', enabled: false, pos: { x: -220 - 60, y: 180 }, bidirectional: false },
			{ id: 'pip_10', source: 'N_M3.net_5', destination: 'net_C', enabled: false, pos: { x: -200 - 60, y: 180 }, bidirectional: false },
			{ id: 'pip_11', source: 'N_M3.net_4', destination: 'net_C', enabled: false, pos: { x: -180 - 60, y: 180 }, bidirectional: false },
			{ id: 'pip_12', source: 'global_VL.net_0', destination: 'net_C', enabled: false, pos: { x: -140 - 60, y: 180 }, bidirectional: false },
			{ id: 'pip_12', source: 'global_VL.net_1', destination: 'net_C', enabled: false, pos: { x: -120 - 60, y: 180 }, bidirectional: false },
			{ id: 'pip_12', source: 'global_VIOL.net_0', destination: 'net_C', enabled: false, pos: { x: -260 - 60, y: 180 }, bidirectional: false },
		],
	},

	/**
	 *
	 * PIN D CONFIGURATION
	 *
	 */
	{
		// All standard pin D cells. doesn't include bottom because of the extra length on the wire, and doesnt include left + right sides because they connect to the M2/M3 extra switches.
		ids: id_range('[A-G][A-H]'),
		nets: [
			{
				id: 'net_D',
				value: false,
				points: [
					{ x: 0, y: CELL_HEIGHT / 2 },
					{ x: 0, y: CELL_HEIGHT / 2 + 180 },
				],
			},
		],
		pips: [
			{
				id: 'pip_12',
				source: 'W_M0.net_2',
				destination: 'net_D',
				enabled: false,
				pos: { x: CELL_WIDTH / 2, y: CELL_HEIGHT + 80 },
				bidirectional: false,
			},
			{
				id: 'pip_13',
				source: 'W_M0.net_3',
				destination: 'net_D',
				enabled: false,
				pos: { x: CELL_WIDTH / 2, y: CELL_HEIGHT + 100 },
				bidirectional: false,
			},
			{
				id: 'pip_14',
				source: 'W_M1.net_2',
				destination: 'net_D',
				enabled: false,
				pos: { x: CELL_WIDTH / 2, y: CELL_HEIGHT + 120 },
				bidirectional: false,
			},
			{
				id: 'pip_15',
				source: 'W_M1.net_3',
				destination: 'net_D',
				enabled: false,
				pos: { x: CELL_WIDTH / 2, y: CELL_HEIGHT + 140 },
				bidirectional: false,
			},
			{
				id: 'pip_v2_0',
				source: 'global_HD.net_0',
				destination: 'net_D',
				enabled: false,
				pos: { x: 100, y: 500 },
				bidirectional: false,
			},
		],
	},
	{
		// Bottom Side M2/M3 connections
		ids: id_range('H[A-H]'),
		nets: [
			{
				id: 'net_D',
				value: false,
				points: [
					{ x: 0, y: CELL_HEIGHT / 2 },
					{ x: 0, y: CELL_HEIGHT / 2 + 220 },
				],
			},
		],
		pips: [],
	},

	/**
	 *
	 * PIN K CONFIGURATION
	 *
	 */
	{
		// All cells but the left edge
		ids: id_range('[A-H][B-H]'),
		nets: [
			{
				id: 'net_K',
				value: false,
				points: [
					{ x: -CELL_WIDTH / 2, y: 80 },
					{ x: -CELL_WIDTH / 2 - 80, y: 80 },
				],
			},
		],
		pips: [
			{
				id: 'pip_clk',
				source: 'global.net_clk',
				destination: 'net_K',
				enabled: false,
				pos: { x: -60, y: 240 },
				bidirectional: false,
			},
		],
	},
	{
		// Left edge
		ids: id_range('[A-H]A'),
		nets: [
			{
				id: 'net_K',
				value: false,
				points: [
					{ x: -CELL_WIDTH / 2, y: 80 },
					{ x: -CELL_WIDTH / 2 - 180, y: 80 },
				],
			},
		],
		pips: [
			{
				id: 'pip_clk',
				source: 'global.net_clk',
				destination: 'net_K',
				enabled: false,
				pos: { x: -160, y: 240 },
				bidirectional: false,
			},
			{
				id: 'pip_clk',
				source: 'global_VL.net_1',
				destination: 'net_K',
				enabled: false,
				pos: { x: -180, y: 240 },
				bidirectional: false,
			},
		],
	},

	/**
	 *
	 * PIN X CONFIGURATION
	 *
	 */
	{
		// Everything but the top and bottom because there are no local cell connections above/below them, as well as the right edge needing custom IO connections
		ids: id_range('[B-G][A-G]'),
		nets: [
			{
				id: 'net_X',
				value: false,
				points: [
					{ x: CELL_WIDTH / 2, y: 20 },
					{ x: CELL_WIDTH / 2 + 40, y: 20 },
					{ x: CELL_WIDTH / 2 + 40, y: -100 },
					{ x: CELL_WIDTH / 2 + 220, y: -100 },
					{ x: CELL_WIDTH / 2 + 40, y: -100 },
					{ x: CELL_WIDTH / 2 + 40, y: -360 },
					{ x: -CELL_WIDTH / 2 - 40, y: -360 },
					{ x: -CELL_WIDTH / 2 - 40, y: -540 },
					{ x: CELL_WIDTH / 2 + 40, y: 20, continuous: false },
					{ x: CELL_WIDTH / 2 + 40, y: 180 },
					{ x: CELL_WIDTH / 2, y: 180 },
					{ x: CELL_WIDTH / 2, y: 360 },
					{ x: CELL_WIDTH / 2 - 240, y: 360 },
					{ x: CELL_WIDTH / 2 - 240, y: 520 },
				],
			},
		],
		pips: [
			{ id: 'pip_16', source: 'net_X', destination: 'T_M0.net_1', enabled: false, pos: { x: 300, y: 60 }, bidirectional: false },
			{ id: 'pip_17', source: 'net_X', destination: 'T_M1.net_1', enabled: false, pos: { x: 340, y: 60 }, bidirectional: false },
			{ id: 'pip_20', source: 'net_X', destination: 'N.net_D', enabled: false, pos: { x: CELL_WIDTH / 2, y: -200 }, bidirectional: false },
			{ id: 'pip_21', source: 'net_X', destination: 'N.net_C', enabled: false, pos: { x: -40, y: -380 }, bidirectional: false },
			{ id: 'pip_21', source: 'net_X', destination: 'S.net_A', enabled: false, pos: { x: CELL_HEIGHT / 2 + 0, y: 520 }, bidirectional: false },
			{ id: 'pip_21', source: 'net_X', destination: 'S.net_B', enabled: false, pos: { x: -40, y: 680 }, bidirectional: false },
			{ id: 'pip_v2_0', source: 'net_X', destination: 'global_VR.net_0', enabled: false, pos: { x: 420, y: 60 }, bidirectional: false },
		],
	},
	{
		// Bottom row of CLBS with that are missing the bottom local CLB interconnect
		ids: id_range('H[A-G]'),
		nets: [
			{
				id: 'net_X',
				value: false,
				points: [
					{ x: CELL_WIDTH / 2, y: 20 },
					{ x: CELL_WIDTH / 2 + 40, y: 20 },
					{ x: CELL_WIDTH / 2 + 40, y: -100 },
					{ x: CELL_WIDTH / 2 + 220, y: -100 },
					{ x: CELL_WIDTH / 2 + 40, y: -100 },
					{ x: CELL_WIDTH / 2 + 40, y: -360 },
					{ x: -CELL_WIDTH / 2 - 40, y: -360 },
					{ x: -CELL_WIDTH / 2 - 40, y: -540 },
					{ x: CELL_WIDTH / 2 + 40, y: 20, continuous: false },
					{ x: CELL_WIDTH / 2 + 40, y: 240 },
				],
			},
		],
		pips: [
			{ id: 'pip_16', source: 'net_X', destination: 'T_M0.net_1', enabled: false, pos: { x: 300, y: 60 }, bidirectional: false },
			{ id: 'pip_17', source: 'net_X', destination: 'T_M1.net_1', enabled: false, pos: { x: 340, y: 60 }, bidirectional: false },
			{ id: 'pip_20', source: 'net_X', destination: 'N.net_D', enabled: false, pos: { x: CELL_WIDTH / 2, y: -200 }, bidirectional: false },
			{ id: 'pip_21', source: 'net_X', destination: 'N.net_C', enabled: false, pos: { x: -40, y: -380 }, bidirectional: false },
			{ id: 'pip_v2_0', source: 'net_X', destination: 'global_VR.net_0', enabled: false, pos: { x: 420, y: 60 }, bidirectional: false },
			{ id: 'pip_v2_0', source: 'net_X', destination: 'T_IO1.net_O', enabled: false, pos: { x: 240, y: 400 }, bidirectional: false },
		],
	},

	/**
	 *
	 * PIN Y CONFIGURATION
	 *
	 */
	{
		// Everything but the right edge
		ids: id_range('[A-H][A-G]'),
		nets: [
			{
				id: 'net_Y',
				value: false,
				points: [
					{ x: CELL_WIDTH / 2, y: 100 },
					{ x: CELL_WIDTH / 2 + 240, y: 100 },
					{ x: CELL_WIDTH / 2 + 200, y: 100 },
					{ x: CELL_WIDTH / 2 + 200, y: -40 },
				],
			},
		],
		pips: [
			{ id: 'pip_18', source: 'net_Y', destination: 'T_M0.net_0', enabled: false, pos: { x: 280, y: 260 }, bidirectional: false },
			{ id: 'pip_19', source: 'net_Y', destination: 'T_M1.net_0', enabled: false, pos: { x: 320, y: 260 }, bidirectional: false },
			{
				id: 'pip_21',
				source: 'net_Y',
				destination: 'E.net_B',
				enabled: false,
				pos: { x: 400, y: CELL_HEIGHT / 2 - 40 },
				bidirectional: false,
			},
			{
				id: 'pip_v2_0',
				source: 'net_Y',
				destination: 'global_VR.net_1',
				enabled: false,
				pos: { x: 440, y: 260 },
				bidirectional: false,
			},
		],
	},

	/**
	 *
	 * GLOBAL LONG LINE CONFIGURATION
	 *
	 */

	{
		ids: [...id_range('[B-G][A-G]')],
		nets: [],
		pips: [
			{ id: 'pip_v2_0', source: 'global_VL.net_1', destination: 'net_K', enabled: false, pos: { x: -CELL_WIDTH / 2 + 20, y: 240 }, bidirectional: false },
			{ id: 'pip_v2_0', source: 'T_M0.net_2', destination: 'global_VR.net_1', enabled: false, pos: { x: 440, y: 400 }, bidirectional: true },
			{ id: 'pip_v2_0', source: 'T_M0.net_3', destination: 'global_VR.net_0', enabled: false, pos: { x: 420, y: 420 }, bidirectional: true },
			{ id: 'pip_v2_0', source: 'T_M1.net_2', destination: 'global_VR.net_1', enabled: false, pos: { x: 440, y: 440 }, bidirectional: true },
			{ id: 'pip_v2_0', source: 'T_M1.net_3', destination: 'global_VR.net_0', enabled: false, pos: { x: 420, y: 460 }, bidirectional: true },
			{ id: 'pip_v2_0', source: 'T_M1.net_1', destination: 'global_HU.net_0', enabled: false, pos: { x: 340, y: -60 }, bidirectional: true },
			{ id: 'pip_v2_0', source: 'T_M0.net_0', destination: 'global_HU.net_0', enabled: false, pos: { x: 280, y: -60 }, bidirectional: true },
		],
	},

	/**
	 * BIDIRECTIONAL PARTIAL VERTICAL LONG LINES.
	 */
	{
		ids: id_range('[B-G][A-G]'),
		nets: [
			{
				id: 'net_rhl',
				value: false,
				points: [
					{ x: 280, y: -340 },
					{ x: 300, y: -340 },
					{ x: 300, y: -200 },
					{ x: 280, y: -200 },
					{ x: 280, y: 280 },
				],
			},
		],
		pips: [
			{ id: 'pip_v2_0', source: 'T.net_rhl', destination: 'S.net_rhl', enabled: false, pos: { x: 380, y: 380 }, bidirectional: true },
			{ id: 'pip_v2_0', source: 'T.net_rhl', destination: 'T_M0.net_3', enabled: false, pos: { x: 380, y: 420 }, bidirectional: true },
			{ id: 'pip_v2_0', source: 'T.net_rhl', destination: 'T_M1.net_2', enabled: false, pos: { x: 380, y: 440 }, bidirectional: true },
			{ id: 'pip_v2_0', source: 'T.net_rhl', destination: 'N_M0.net_3', enabled: false, pos: { x: 400, y: -140 }, bidirectional: true },
			{ id: 'pip_v2_0', source: 'T.net_rhl', destination: 'N_M1.net_2', enabled: false, pos: { x: 400, y: -120 }, bidirectional: true },
			{ id: 'pip_v2_0', source: 'W.net_rhl', destination: 'net_B', enabled: false, pos: { x: -CELL_WIDTH / 2 - 40, y: 120 }, bidirectional: false },
			{ id: 'pip_v2_0', source: 'W.net_rhl', destination: 'net_C', enabled: false, pos: { x: -CELL_WIDTH / 2 - 40, y: 180 }, bidirectional: false },
			{ id: 'pip_v2_0', source: 'net_Y', destination: 'T.net_rhl', enabled: false, pos: { x: 380, y: 260 }, bidirectional: false },
		],
	},

	{
		// Bottom Rows
		ids: id_range('H[A-G]'),
		nets: [
			{
				id: 'net_rhl',
				value: false,
				points: [
					{ x: 280, y: -340 },
					{ x: 300, y: -340 },
					{ x: 300, y: -200 },
					{ x: 280, y: -200 },
					{ x: 280, y: 340 },
				],
			},
		],
		pips: [
			{ id: 'pip_v2_0', source: 'T.net_rhl', destination: 'N_M0.net_3', enabled: false, pos: { x: 400, y: -140 }, bidirectional: true },
			{ id: 'pip_v2_0', source: 'T.net_rhl', destination: 'N_M1.net_2', enabled: false, pos: { x: 400, y: -120 }, bidirectional: true },
			{ id: 'pip_v2_0', source: 'W.net_rhl', destination: 'net_B', enabled: false, pos: { x: -CELL_WIDTH / 2 - 40, y: 120 }, bidirectional: false },
			{ id: 'pip_v2_0', source: 'W.net_rhl', destination: 'net_C', enabled: false, pos: { x: -CELL_WIDTH / 2 - 40, y: 180 }, bidirectional: false },
			{ id: 'pip_v2_0', source: 'net_Y', destination: 'T.net_rhl', enabled: false, pos: { x: 380, y: 260 }, bidirectional: false },
		],
	},
	/**
	 *
	 * IO BANK CONFIGURATIONS
	 *
	 */

	/**
	 * LEFT BANKS
	 */
	{
		// bottom of the two banks, DA doesnt have a bottom one
		ids: [...id_range('[A-C]A'), ...id_range('[E-F]A')],
		nets: [],
		pips: [
			{ id: 'pip_0', source: 'T_IO1.net_I', destination: 'T_M3.net_3', enabled: false, pos: { x: -140, y: 460 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO1.net_I', destination: 'global_VL.net_0', enabled: false, pos: { x: -200, y: 580 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO1.net_I', destination: 'S_M3.net_0', enabled: false, pos: { x: -260, y: 580 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO1.net_I', destination: 'S_M2.net_0', enabled: false, pos: { x: -300, y: 580 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO1.net_I', destination: 'global_VIOL.net_0', enabled: false, pos: { x: -320, y: 580 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_VL.net_0', destination: 'T_IO1.net_T', enabled: false, pos: { x: -200, y: 540 }, bidirectional: false },
			{ id: 'pip_0', source: 'S_M3.net_0', destination: 'T_IO1.net_T', enabled: false, pos: { x: -260, y: 540 }, bidirectional: false },
			{ id: 'pip_0', source: 'S_M2.net_0', destination: 'T_IO1.net_T', enabled: false, pos: { x: -300, y: 540 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_VIOL.net_0', destination: 'T_IO1.net_T', enabled: false, pos: { x: -320, y: 540 }, bidirectional: false },
			{ id: 'pip_0', source: 'S_M2.net_1', destination: 'T_IO1.net_O', enabled: false, pos: { x: -280, y: 620 }, bidirectional: false },
			{ id: 'pip_0', source: 'S_M3.net_1', destination: 'T_IO1.net_O', enabled: false, pos: { x: -240, y: 620 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_VL.net_1', destination: 'T_IO1.net_O', enabled: false, pos: { x: -180, y: 620 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M2.net_2', destination: 'T_IO1.net_O', enabled: false, pos: { x: -100, y: 400 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M3.net_2', destination: 'T_IO1.net_O', enabled: false, pos: { x: -100, y: 440 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_HD.net_0', destination: 'T_IO1.net_O', enabled: false, pos: { x: -100, y: 500 }, bidirectional: false },
		],
	},
	{
		// Top of the two banks (so all of the left side cells)
		ids: id_range('[A-F]A'),
		nets: [],
		pips: [
			{ id: 'pip_0', source: 'T_IO0.net_I', destination: 'net_B', enabled: false, pos: { x: -60, y: 120 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO0.net_I', destination: 'T_M3.net_2', enabled: false, pos: { x: -60, y: 440 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO0.net_I', destination: 'global_HD.net_0', enabled: false, pos: { x: -60, y: 500 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO0.net_I', destination: 'T_M2.net_1', enabled: false, pos: { x: -280, y: 320 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO0.net_I', destination: 'T_M3.net_1', enabled: false, pos: { x: -240, y: 320 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO0.net_I', destination: 'global_VL.net_1', enabled: false, pos: { x: -180, y: 320 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M2.net_3', destination: 'T_IO0.net_O', enabled: false, pos: { x: -80, y: 420 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M3.net_3', destination: 'T_IO0.net_O', enabled: false, pos: { x: -80, y: 460 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_VIOL.net_0', destination: 'T_IO0.net_O', enabled: false, pos: { x: -320, y: 360 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M2.net_0', destination: 'T_IO0.net_O', enabled: false, pos: { x: -300, y: 360 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M3.net_0', destination: 'T_IO0.net_O', enabled: false, pos: { x: -260, y: 360 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_VL.net_0', destination: 'T_IO0.net_O', enabled: false, pos: { x: -200, y: 360 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_VIOL.net_0', destination: 'T_IO0.net_T', enabled: false, pos: { x: -320, y: 280 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M2.net_0', destination: 'T_IO0.net_T', enabled: false, pos: { x: -300, y: 280 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M3.net_0', destination: 'T_IO0.net_T', enabled: false, pos: { x: -260, y: 280 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_VL.net_0', destination: 'T_IO0.net_T', enabled: false, pos: { x: -200, y: 280 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_VIOL.net_0', destination: 'global_HD.net_0', enabled: false, pos: { x: -320, y: 500 }, bidirectional: true },
			{ id: 'pip_0', source: 'S_M2.net_0', destination: 'global_HD.net_0', enabled: false, pos: { x: -300, y: 500 }, bidirectional: true },
			{ id: 'pip_0', source: 'S_M3.net_1', destination: 'global_HD.net_0', enabled: false, pos: { x: -240, y: 500 }, bidirectional: true },
			{ id: 'pip_0', source: 'global_VL.net_0', destination: 'global_HD.net_0', enabled: false, pos: { x: -200, y: 500 }, bidirectional: true },
			{ id: 'pip_0', source: 'global_VL.net_1', destination: 'global_HD.net_0', enabled: false, pos: { x: -180, y: 500 }, bidirectional: true },
			{ id: 'pip_0', source: 'global_VL.net_1', destination: 'T_M2.net_3', enabled: false, pos: { x: -180, y: 420 }, bidirectional: true },
			{ id: 'pip_0', source: 'global_VL.net_0', destination: 'T_M2.net_2', enabled: false, pos: { x: -200, y: 400 }, bidirectional: true },
		],
	},
	{
		// bottom of the two banks, DA doesnt have a bottom one
		ids: ['GA'],
		nets: [],
		pips: [
						{ id: 'pip_0', source: 'T_IO0.net_I', destination: 'net_B', enabled: false, pos: { x: -60, y: 120 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO0.net_I', destination: 'T_M3.net_2', enabled: false, pos: { x: -60, y: 440 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO0.net_I', destination: 'global_HD.net_0', enabled: false, pos: { x: -60, y: 500 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO0.net_I', destination: 'T_M2.net_1', enabled: false, pos: { x: -280, y: 320 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO0.net_I', destination: 'T_M3.net_1', enabled: false, pos: { x: -240, y: 320 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO0.net_I', destination: 'global_VL.net_1', enabled: false, pos: { x: -180, y: 320 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M2.net_3', destination: 'T_IO0.net_O', enabled: false, pos: { x: -80, y: 420 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M3.net_3', destination: 'T_IO0.net_O', enabled: false, pos: { x: -80, y: 460 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_VIOL.net_0', destination: 'T_IO0.net_O', enabled: false, pos: { x: -320, y: 360 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M2.net_0', destination: 'T_IO0.net_O', enabled: false, pos: { x: -300, y: 360 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M3.net_0', destination: 'T_IO0.net_O', enabled: false, pos: { x: -260, y: 360 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_VL.net_0', destination: 'T_IO0.net_O', enabled: false, pos: { x: -200, y: 360 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_VIOL.net_0', destination: 'T_IO0.net_T', enabled: false, pos: { x: -320, y: 280 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M2.net_0', destination: 'T_IO0.net_T', enabled: false, pos: { x: -300, y: 280 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M3.net_0', destination: 'T_IO0.net_T', enabled: false, pos: { x: -260, y: 280 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_VL.net_0', destination: 'T_IO0.net_T', enabled: false, pos: { x: -200, y: 280 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO1.net_I', destination: 'T_M3.net_3', enabled: false, pos: { x: -140, y: 460 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO1.net_I', destination: 'global_VL.net_0', enabled: false, pos: { x: -200, y: 580 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO1.net_I', destination: 'T_M3.net_5', enabled: false, pos: { x: -260, y: 580 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO1.net_I', destination: 'T_M2.net_5', enabled: false, pos: { x: -300, y: 580 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_IO1.net_I', destination: 'global_VIOL.net_0', enabled: false, pos: { x: -320, y: 580 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_VL.net_0', destination: 'T_IO1.net_T', enabled: false, pos: { x: -200, y: 540 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M3.net_5', destination: 'T_IO1.net_T', enabled: false, pos: { x: -260, y: 540 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M2.net_5', destination: 'T_IO1.net_T', enabled: false, pos: { x: -300, y: 540 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_VIOL.net_0', destination: 'T_IO1.net_T', enabled: false, pos: { x: -320, y: 540 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M2.net_6', destination: 'T_IO1.net_O', enabled: false, pos: { x: -280, y: 620 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M3.net_6', destination: 'T_IO1.net_O', enabled: false, pos: { x: -240, y: 620 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_VL.net_1', destination: 'T_IO1.net_O', enabled: false, pos: { x: -180, y: 620 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M2.net_2', destination: 'T_IO1.net_O', enabled: false, pos: { x: -100, y: 400 }, bidirectional: false },
			{ id: 'pip_0', source: 'T_M3.net_2', destination: 'T_IO1.net_O', enabled: false, pos: { x: -100, y: 440 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_HD.net_0', destination: 'T_IO1.net_O', enabled: false, pos: { x: -100, y: 500 }, bidirectional: false },
			{ id: 'pip_0', source: 'global_VIOL.net_0', destination: 'global_HD.net_0', enabled: false, pos: { x: -320, y: 500 }, bidirectional: true },
			{ id: 'pip_0', source: 'T_M2.net_5', destination: 'global_HD.net_0', enabled: false, pos: { x: -300, y: 500 }, bidirectional: true },
			{ id: 'pip_0', source: 'T_M3.net_4', destination: 'global_HD.net_0', enabled: false, pos: { x: -240, y: 500 }, bidirectional: true },
			{ id: 'pip_0', source: 'global_VL.net_0', destination: 'global_HD.net_0', enabled: false, pos: { x: -200, y: 500 }, bidirectional: true },
			{ id: 'pip_0', source: 'global_VL.net_1', destination: 'global_HD.net_0', enabled: false, pos: { x: -180, y: 500 }, bidirectional: true },
			{ id: 'pip_0', source: 'global_VL.net_1', destination: 'T_M2.net_3', enabled: false, pos: { x: -180, y: 420 }, bidirectional: true },
			{ id: 'pip_0', source: 'global_VL.net_0', destination: 'T_M2.net_2', enabled: false, pos: { x: -200, y: 400 }, bidirectional: true },
		],
	},

	/**
	 *
	 * CORNER CELL HANDLING
	 *
	 */
	{
		// Bottom left corner
		ids: ['HA'],
		nets: [],
		pips: [
			{ id: 'pip_0', source: 'global_VIOL.net_0', destination: 'T_IO0.net_O', enabled: false, pos: { x: -320, y: 380 }, bidirectional: false },
			{ id: 'pip_0', source: 'N_M2.net_5', destination: 'T_IO0.net_O', enabled: false, pos: { x: -300, y: 380 }, bidirectional: false },
			{ id: 'pip_0', source: 'N_M3.net_5', destination: 'T_IO0.net_O', enabled: false, pos: { x: -260, y: 380 }, bidirectional: false },
		],
	},
];

const switch_matrix_config: { ids: string[]; matrices: { nets: Net[]; pos: { x: number; y: number } }[] }[] = [
	{
		// Main switch matrices. All cells that have the standard bottom right cells.
		ids: id_range('[A-G][A-G]'),
		matrices: [
			{
				pos: { x: CELL_WIDTH / 2 + 90, y: 250 },
				nets: [
					{
						id: 'net_0',
						value: false,
						points: [
							{ x: -10, y: -MATRIX_HEIGHT / 2 },
							{ x: -10, y: -MATRIX_HEIGHT / 2 - 520 },
						],
					},
					{
						id: 'net_1',
						value: false,
						points: [
							{ x: 10, y: -MATRIX_HEIGHT / 2 },
							{ x: 10, y: -MATRIX_HEIGHT / 2 - 520 },
						],
					},
					{
						id: 'net_2',
						value: false,
						points: [
							{ x: MATRIX_WIDTH / 2, y: -10 },
							{ x: MATRIX_WIDTH / 2 + 520, y: -10 },
						],
					},
					{
						id: 'net_3',
						value: false,
						points: [
							{ x: MATRIX_WIDTH / 2, y: 10 },
							{ x: MATRIX_WIDTH / 2 + 520, y: 10 },
						],
					},
				],
			},
			{
				pos: { x: CELL_WIDTH / 2 + 90 + MATRIX_WIDTH, y: 250 + MATRIX_HEIGHT },
				nets: [
					{
						id: 'net_0',
						value: false,
						points: [
							{ x: -10, y: -MATRIX_HEIGHT / 2 },
							{ x: -10, y: -MATRIX_HEIGHT / 2 - 520 },
						],
					},
					{
						id: 'net_1',
						value: false,
						points: [
							{ x: 10, y: -MATRIX_HEIGHT / 2 },
							{ x: 10, y: -MATRIX_HEIGHT / 2 - 520 },
						],
					},
					{
						id: 'net_2',
						value: false,
						points: [
							{ x: MATRIX_WIDTH / 2, y: -10 },
							{ x: MATRIX_WIDTH / 2 + 520, y: -10 },
						],
					},
					{
						id: 'net_3',
						value: false,
						points: [
							{ x: MATRIX_WIDTH / 2, y: 10 },
							{ x: MATRIX_WIDTH / 2 + 520, y: 10 },
						],
					},
				],
			},
		],
	},

	{
		// M2/M3 Matrices for the left edge, since each cell there is responsible for 4, not 2 matrices.
		ids: id_range('[B-F]A'),
		matrices: [
			{
				pos: { x: CELL_WIDTH / 2 - 490, y: 250 },
				nets: [
					{
						id: 'net_0',
						value: false,
						points: [
							{ x: -10, y: -MATRIX_HEIGHT / 2 },
							{ x: -10, y: -MATRIX_HEIGHT / 2 - 520 },
						],
					},
					{
						id: 'net_1',
						value: false,
						points: [
							{ x: 10, y: -MATRIX_HEIGHT / 2 },
							{ x: 10, y: -MATRIX_HEIGHT / 2 - 520 },
						],
					},
					{
						id: 'net_2',
						value: false,
						points: [
							{ x: MATRIX_WIDTH / 2, y: -10 },
							{ x: MATRIX_WIDTH / 2 + 540, y: -10 },
						],
					},
					{
						id: 'net_3',
						value: false,
						points: [
							{ x: MATRIX_WIDTH / 2, y: 10 },
							{ x: MATRIX_WIDTH / 2 + 540, y: 10 },
						],
					},
				],
			},
			{
				pos: { x: CELL_WIDTH / 2 - 490 + MATRIX_WIDTH, y: 250 + MATRIX_HEIGHT },
				nets: [
					{
						id: 'net_0',
						value: false,
						points: [
							{ x: -10, y: -MATRIX_HEIGHT / 2 },
							{ x: -10, y: -MATRIX_HEIGHT / 2 - 520 },
						],
					},
					{
						id: 'net_1',
						value: false,
						points: [
							{ x: 10, y: -MATRIX_HEIGHT / 2 },
							{ x: 10, y: -MATRIX_HEIGHT / 2 - 520 },
						],
					},
					{
						id: 'net_2',
						value: false,
						points: [
							{ x: MATRIX_WIDTH / 2, y: -10 },
							{ x: MATRIX_WIDTH / 2 + 540, y: -10 },
						],
					},
					{
						id: 'net_3',
						value: false,
						points: [
							{ x: MATRIX_WIDTH / 2, y: 10 },
							{ x: MATRIX_WIDTH / 2 + 540, y: 10 },
						],
					},
				],
			},
		],
	},
	{
		// M2/M3 Matrices for the bottom left corner because its unique :(
		ids: id_range('GA'),
		matrices: [
			{
				pos: { x: CELL_WIDTH / 2 - 490, y: 250 },
				nets: [
					{
						id: 'net_0',
						value: false,
						points: [
							{ x: -10, y: -MATRIX_HEIGHT / 2 },
							{ x: -10, y: -MATRIX_HEIGHT / 2 - 520 },
						],
					},
					{
						id: 'net_1',
						value: false,
						points: [
							{ x: 10, y: -MATRIX_HEIGHT / 2 },
							{ x: 10, y: -MATRIX_HEIGHT / 2 - 520 },
						],
					},
					{
						id: 'net_2',
						value: false,
						points: [
							{ x: MATRIX_WIDTH / 2, y: -10 },
							{ x: MATRIX_WIDTH / 2 + 540, y: -10 },
						],
					},
					{
						id: 'net_3',
						value: false,
						points: [
							{ x: MATRIX_WIDTH / 2, y: 10 },
							{ x: MATRIX_WIDTH / 2 + 540, y: 10 },
						],
					},
					{
						id: 'net_4',
						value: false,
						points: [
							{ x: 10, y: MATRIX_HEIGHT / 2 },
							{ x: 10, y: MATRIX_HEIGHT / 2 + 630 },
						],
					},
					{
						id: 'net_5',
						value: false,
						points: [
							{ x: -10, y: MATRIX_HEIGHT / 2 },
							{ x: -10, y: MATRIX_HEIGHT / 2 + 670 },
						],
					},
				],
			},
			{
				pos: { x: CELL_WIDTH / 2 - 490 + MATRIX_WIDTH, y: 250 + MATRIX_HEIGHT },
				nets: [
					{
						id: 'net_0',
						value: false,
						points: [
							{ x: -10, y: -MATRIX_HEIGHT / 2 },
							{ x: -10, y: -MATRIX_HEIGHT / 2 - 520 },
						],
					},
					{
						id: 'net_1',
						value: false,
						points: [
							{ x: 10, y: -MATRIX_HEIGHT / 2 },
							{ x: 10, y: -MATRIX_HEIGHT / 2 - 520 },
						],
					},
					{
						id: 'net_2',
						value: false,
						points: [
							{ x: MATRIX_WIDTH / 2, y: -10 },
							{ x: MATRIX_WIDTH / 2 + 540, y: -10 },
						],
					},
					{
						id: 'net_3',
						value: false,
						points: [
							{ x: MATRIX_WIDTH / 2, y: 10 },
							{ x: MATRIX_WIDTH / 2 + 540, y: 10 },
						],
					},
					{
						id: 'net_4',
						value: false,
						points: [
							{ x: 10, y: MATRIX_HEIGHT / 2 },
							{ x: 10, y: MATRIX_HEIGHT / 2 + 550 },
						],
					},
					{
						id: 'net_5',
						value: false,
						points: [
							{ x: -10, y: MATRIX_HEIGHT / 2 },
							{ x: -10, y: MATRIX_HEIGHT / 2 + 570 },
						],
					},
				],
			},
		],
	},
	{
		// M1/M0 matrices for the bottom of the chip, same purpose as the M1/0 of the middle, but slightly different location.
		ids: id_range('H[B-H]'),
		matrices: [
			{
				pos: { x: CELL_WIDTH / 2 + 90, y: CELL_HEIGHT / 2 + 190 },
				nets: [
					{
						id: 'net_0',
						value: false,
						points: [
							{ x: -10, y: -MATRIX_HEIGHT / 2 },
							{ x: -10, y: -MATRIX_HEIGHT / 2 - 630 },
						],
					},
					{
						id: 'net_1',
						value: false,
						points: [
							{ x: 10, y: -MATRIX_HEIGHT / 2 },
							{ x: 10, y: -MATRIX_HEIGHT / 2 - 630 },
						],
					},
					{
						id: 'net_2',
						value: false,
						points: [
							{ x: 20, y: -MATRIX_HEIGHT / 2 + 10 },
							{ x: 500, y: -MATRIX_HEIGHT / 2 + 10 },
						],
					},
					{
						id: 'net_3',
						value: false,
						points: [
							{ x: 20, y: -MATRIX_HEIGHT / 2 + 30 },
							{ x: 500, y: -MATRIX_HEIGHT / 2 + 30 },
						],
					},
				],
			},
			{
				pos: { x: CELL_WIDTH / 2 + 130, y: CELL_HEIGHT / 2 + 150 },
				nets: [
					{
						id: 'net_0',
						value: false,
						points: [
							{ x: -10, y: -MATRIX_HEIGHT / 2 },
							{ x: -10, y: -MATRIX_HEIGHT / 2 - 540 },
						],
					},
					{
						id: 'net_1',
						value: false,
						points: [
							{ x: 10, y: -MATRIX_HEIGHT / 2 },
							{ x: 10, y: -MATRIX_HEIGHT / 2 - 630 },
						],
					},
					{
						id: 'net_2',
						value: false,
						points: [
							{ x: 20, y: -MATRIX_HEIGHT / 2 + 10 },
							{ x: 500, y: -MATRIX_HEIGHT / 2 + 10 },
						],
					},
					{
						id: 'net_3',
						value: false,
						points: [
							{ x: 20, y: -MATRIX_HEIGHT / 2 + 30 },
							{ x: 500, y: -MATRIX_HEIGHT / 2 + 30 },
						],
					},
				],
			},
		],
	},
	{
		// M1/M0 matrices for the bottom left cell as it needs to keep track of its onl left nets, unlike every other switch.
		ids: id_range('HA'),
		matrices: [
			{
				pos: { x: CELL_WIDTH / 2 + 90, y: CELL_HEIGHT / 2 + 190 },
				nets: [
					{
						id: 'net_0',
						value: false,
						points: [
							{ x: -10, y: -MATRIX_HEIGHT / 2 },
							{ x: -10, y: -MATRIX_HEIGHT / 2 - 630 },
						],
					},
					{
						id: 'net_1',
						value: false,
						points: [
							{ x: 10, y: -MATRIX_HEIGHT / 2 },
							{ x: 10, y: -MATRIX_HEIGHT / 2 - 630 },
						],
					},
					{
						id: 'net_2',
						value: false,
						points: [
							{ x: 20, y: -MATRIX_HEIGHT / 2 + 10 },
							{ x: 500, y: -MATRIX_HEIGHT / 2 + 10 },
						],
					},
					{
						id: 'net_3',
						value: false,
						points: [
							{ x: 20, y: -MATRIX_HEIGHT / 2 + 30 },
							{ x: 500, y: -MATRIX_HEIGHT / 2 + 30 },
						],
					},
					{
						id: 'dummy',
						value: false,
						points: [],
					},
					{
						id: 'dummy',
						value: false,
						points: [],
					},
					{
						id: 'net_6',
						value: false,
						points: [
							{ x: -20, y: -MATRIX_HEIGHT / 2 + 30 },
							{ x: -610, y: -MATRIX_HEIGHT / 2 + 30 },
						],
					},
					{
						id: 'net_7',
						value: false,
						points: [
							{ x: -20, y: -MATRIX_HEIGHT / 2 + 10 },
							{ x: -570, y: -MATRIX_HEIGHT / 2 + 10 },
						],
					},
				],
			},
			{
				pos: { x: CELL_WIDTH / 2 + 130, y: CELL_HEIGHT / 2 + 150 },
				nets: [
					{
						id: 'net_0',
						value: false,
						points: [
							{ x: -10, y: -MATRIX_HEIGHT / 2 },
							{ x: -10, y: -MATRIX_HEIGHT / 2 - 540 },
						],
					},
					{
						id: 'net_1',
						value: false,
						points: [
							{ x: 10, y: -MATRIX_HEIGHT / 2 },
							{ x: 10, y: -MATRIX_HEIGHT / 2 - 630 },
						],
					},
					{
						id: 'net_2',
						value: false,
						points: [
							{ x: 20, y: -MATRIX_HEIGHT / 2 + 10 },
							{ x: 500, y: -MATRIX_HEIGHT / 2 + 10 },
						],
					},
					{
						id: 'net_3',
						value: false,
						points: [
							{ x: 20, y: -MATRIX_HEIGHT / 2 + 30 },
							{ x: 500, y: -MATRIX_HEIGHT / 2 + 30 },
						],
					},
					{
						id: 'dummy',
						value: false,
						points: [],
					},
					{
						id: 'dummy',
						value: false,
						points: [],
					},
					{
						id: 'net_6',
						value: false,
						points: [
							{ x: -20, y: -MATRIX_HEIGHT / 2 + 30 },
							{ x: -590, y: -MATRIX_HEIGHT / 2 + 30 },
						],
					},
					{
						id: 'net_7',
						value: false,
						points: [
							{ x: -20, y: -MATRIX_HEIGHT / 2 + 10 },
							{ x: -570, y: -MATRIX_HEIGHT / 2 + 10 },
						],
					},
				],
			},
		],
	},
];

const io_config: { ids: string[]; io_bank: { nets: Net[]; pos: { x: number; y: number }; size: { width: number; height: number }; pads?: { pos: { x: number; y: number }; size: { width: number; height: number } }[] }[] }[] = [
	/**
	 *
	 * LEFT SIDE IO BANKS
	 *
	 */

	{
		// Main chunk of left IO banks, except the one in the middle that shares a slot with VCC
		ids: [...id_range('[A-C]A'), ...id_range('[E-G]A')],
		io_bank: [
			{
				pos: { x: -510, y: 140 },
				size: { width: IO_WIDTH, height: IO_HEIGHT },
				nets: [
					{ id: `net_ts_mux`, value: false, points: [] },
					{ id: `net_io_clk`, value: false, points: [] },
					{ id: `net_in_q`, value: false, points: [] },
					{
						id: 'net_O',
						value: false,
						points: [
							{ x: IO_WIDTH / 2, y: 60 },
							{ x: IO_WIDTH / 2 + 260, y: 60 },
							{ x: IO_WIDTH / 2 + 260, y: 160 },
						],
					},
					{
						id: 'net_I',
						value: false,
						points: [
							{ x: IO_WIDTH / 2, y: 20 },
							{ x: IO_WIDTH / 2 + 280, y: 20 },
							{ x: IO_WIDTH / 2 + 280, y: 200 },
							{ x: IO_WIDTH / 2 + 280, y: 20, continuous: false },
							{ x: IO_WIDTH / 2 + 280, y: -180 },
						],
					},
					{
						id: 'net_T',
						value: false,
						points: [
							{ x: IO_WIDTH / 2, y: -20 },
							{ x: IO_WIDTH / 2 + 140, y: -20 },
						],
					},
					{
						id: 'net_pad',
						value: false,
						points: [
							{ x: -IO_WIDTH / 2, y: 0 },
							{ x: -IO_WIDTH / 2 - 150, y: 0 },
						],
					},
				],
				pads: [
					{
						pos: { x: -IO_WIDTH / 2 - 125, y: IO_HEIGHT / 2 - 25 },
						size: { width: 50, height: 50 },
					},
				],
			},
			{
				pos: { x: -510, y: 400 },
				size: { width: IO_WIDTH, height: IO_HEIGHT },
				nets: [
					{ id: `net_ts_mux`, value: false, points: [] },
					{ id: `net_io_clk`, value: false, points: [] },
					{ id: `net_in_q`, value: false, points: [] },
					{
						id: 'net_O',
						value: false,
						points: [
							{ x: IO_WIDTH / 2, y: 60 },
							{ x: IO_WIDTH / 2 + 240, y: 60 },
							{ x: IO_WIDTH / 2 + 240, y: -160 },
						],
					},
					{
						id: 'net_I',
						value: false,
						points: [
							{ x: IO_WIDTH / 2, y: 20 },
							{ x: IO_WIDTH / 2 + 200, y: 20 },
							{ x: IO_WIDTH / 2 + 200, y: -100 },
						],
					},
					{
						id: 'net_T',
						value: false,
						points: [
							{ x: IO_WIDTH / 2, y: -20 },
							{ x: IO_WIDTH / 2 + 140, y: -20 },
						],
					},
					{
						id: 'net_pad',
						value: false,
						points: [
							{ x: -IO_WIDTH / 2, y: 0 },
							{ x: -IO_WIDTH / 2 - 150, y: 0 },
						],
					},
				],
				pads: [
					{
						pos: { x: -IO_WIDTH / 2 - 125, y: IO_HEIGHT / 2 - 25 },
						size: { width: 50, height: 50 },
					},
				],
			},
		],
	},
	{
		// Middle Left side io bank that shares a slot with VCC so only has 1 bank
		ids: ['DA'],
		io_bank: [
			{
				pos: { x: -510, y: 140 },
				size: { width: IO_WIDTH, height: IO_HEIGHT },
				nets: [
					{ id: `net_ts_mux`, value: false, points: [] },
					{ id: `net_io_clk`, value: false, points: [] },
					{ id: `net_in_q`, value: false, points: [] },
					{
						id: 'net_O',
						value: false,
						points: [
							{ x: IO_WIDTH / 2, y: 60 },
							{ x: IO_WIDTH / 2 + 260, y: 60 },
							{ x: IO_WIDTH / 2 + 260, y: 160 },
						],
					},
					{
						id: 'net_I',
						value: false,
						points: [
							{ x: IO_WIDTH / 2, y: 20 },
							{ x: IO_WIDTH / 2 + 280, y: 20 },
							{ x: IO_WIDTH / 2 + 280, y: 200 },
							{ x: IO_WIDTH / 2 + 280, y: 20, continuous: false },
							{ x: IO_WIDTH / 2 + 280, y: -180 },
						],
					},
					{
						id: 'net_T',
						value: false,
						points: [
							{ x: IO_WIDTH / 2, y: -20 },
							{ x: IO_WIDTH / 2 + 140, y: -20 },
						],
					},
					{
						id: 'net_pad',
						value: false,
						points: [
							{ x: -IO_WIDTH / 2, y: 0 },
							{ x: -IO_WIDTH / 2 - 150, y: 0 },
						],
					},
				],
				pads: [
					{
						pos: { x: -IO_WIDTH / 2 - 125, y: IO_HEIGHT / 2 - 25 },
						size: { width: 50, height: 50 },
					},
				],
			},
		],
	},

	/**
	 *
	 * BOTTOM SIDE IO BANKS
	 *
	 */

	{
		// All bottom IO except HA, which is slightly different (sigh)
		ids: id_range('H[B-H]'),
		io_bank: [
			// Left IO BANK
			{
				pos: { x: -50 - IO_WIDTH / 2, y: 530 },
				size: { width: IO_HEIGHT, height: IO_WIDTH },
				nets: [
					{ id: `net_ts_mux`, value: false, points: [] },
					{ id: `net_io_clk`, value: false, points: [] },
					{ id: `net_in_q`, value: false, points: [] },
					// Left
					{
						id: 'net_O',
						value: false,
						points: [
							{ x: IO_HEIGHT / 2 - 10, y: -IO_WIDTH / 2 - 30 },
							{ x: IO_HEIGHT / 2 - 10, y: -IO_WIDTH / 2 - 210 },
						],
					},

					// Middle
					{
						id: 'net_I',
						value: false,
						points: [
							{ x: IO_HEIGHT / 2 - 50, y: -IO_WIDTH / 2 - 30 },
							{ x: IO_HEIGHT / 2 - 50, y: -IO_WIDTH / 2 - 270 },
							{ x: IO_HEIGHT / 2 + 50, y: -IO_WIDTH / 2 - 270 },
							{ x: IO_HEIGHT / 2 - 50, y: -IO_WIDTH / 2 - 270, continuous: false },
							{ x: IO_HEIGHT / 2 - 50, y: -IO_WIDTH / 2 - 270 },
							{ x: IO_HEIGHT / 2 - 50, y: -IO_WIDTH / 2 - 290 },
							{ x: IO_HEIGHT / 2 - 270, y: -IO_WIDTH / 2 - 290 },
							{ x: IO_HEIGHT / 2 - 90, y: -IO_WIDTH / 2 - 290 },
							{ x: IO_HEIGHT / 2 - 90, y: -IO_WIDTH / 2 - 470 },
						],
					},

					// Right
					{
						id: 'net_T',
						value: false,
						points: [
							{ x: IO_HEIGHT / 2 - 90, y: -IO_WIDTH / 2 - 30 },
							{ x: IO_HEIGHT / 2 - 90, y: -IO_WIDTH / 2 - 270 },
							{ x: IO_HEIGHT / 2 - 290, y: -IO_WIDTH / 2 - 270 },
						],
					},
					{
						id: 'net_pad',
						value: false,
						points: [
							{ x: 30, y: IO_WIDTH / 2 - 30 },
							{ x: 30, y: IO_WIDTH / 2 + 150 - 30 },
						],
					},
				],
				pads: [
					{
						pos: { x: IO_HEIGHT / 2 - 25, y: IO_WIDTH / 2 + 220 },
						size: { width: 50, height: 50 },
					},
				],
			},

			// Right IO BANK
			{
				pos: { x: 50 + IO_WIDTH / 2, y: 530 },
				size: { width: IO_HEIGHT, height: IO_WIDTH },
				nets: [
					{ id: `net_ts_mux`, value: false, points: [] },
					{ id: `net_io_clk`, value: false, points: [] },
					{ id: `net_in_q`, value: false, points: [] },
					// Right
					{
						id: 'net_T',
						value: false,
						points: [
							{ x: -IO_HEIGHT / 2 + 150, y: -IO_WIDTH / 2 - 30 },
							{ x: -IO_HEIGHT / 2 + 150, y: -IO_WIDTH / 2 - 210 },
						],
					},

					// Middle
					{
						id: 'net_I',
						value: false,
						points: [
							{ x: -IO_HEIGHT / 2 + 110, y: -IO_WIDTH / 2 - 30 },
							{ x: -IO_HEIGHT / 2 + 110, y: -IO_WIDTH / 2 - 230 },
							{ x: -IO_HEIGHT / 2 + 330, y: -IO_WIDTH / 2 - 230 },
						],
					},

					// Left
					{
						id: 'net_O',
						value: false,
						points: [
							{ x: -IO_HEIGHT / 2 + 70, y: -IO_WIDTH / 2 - 30 },
							{ x: -IO_HEIGHT / 2 + 70, y: -IO_WIDTH / 2 - 250 },
							{ x: -IO_HEIGHT / 2 + 350, y: -IO_WIDTH / 2 - 250 },
						],
					},
					{
						id: 'net_pad',
						value: false,
						points: [
							{ x: 30, y: IO_WIDTH / 2 - 30 },
							{ x: 30, y: IO_WIDTH / 2 + 150 - 30 },
						],
					},
				],
				pads: [
					{
						pos: { x: IO_HEIGHT / 2 - 25, y: IO_WIDTH / 2 + 220 },
						size: { width: 50, height: 50 },
					},
				],
			},
		],
	},

	{
		// HA Bank
		ids: ['HA'],
		// Left IO BANK
		io_bank: [
			{
				pos: { x: -90 - IO_WIDTH / 2, y: 530 },
				size: { width: IO_HEIGHT, height: IO_WIDTH },
				nets: [
					{ id: `net_ts_mux`, value: false, points: [] },
					{ id: `net_io_clk`, value: false, points: [] },
					{ id: `net_in_q`, value: false, points: [] },
					// Right
					{
						id: 'net_O',
						value: false,
						points: [
							{ x: IO_HEIGHT / 2 - 10, y: -IO_WIDTH / 2 - 30 },
							{ x: IO_HEIGHT / 2 - 10, y: -IO_WIDTH / 2 - 210 },
						],
					},

					// Middle
					{
						id: 'net_I',
						value: false,
						points: [
							{ x: IO_HEIGHT / 2 - 50, y: -IO_WIDTH / 2 - 30 },
							{ x: IO_HEIGHT / 2 - 50, y: -IO_WIDTH / 2 - 270 },
							{ x: IO_HEIGHT / 2 + 50, y: -IO_WIDTH / 2 - 270 },
							{ x: IO_HEIGHT / 2 - 50, y: -IO_WIDTH / 2 - 270, continuous: false },
							{ x: IO_HEIGHT / 2 - 50, y: -IO_WIDTH / 2 - 270 },
							{ x: IO_HEIGHT / 2 - 50, y: -IO_WIDTH / 2 - 290 },
							{ x: IO_HEIGHT / 2 - 330, y: -IO_WIDTH / 2 - 290 },
							{ x: IO_HEIGHT / 2 - 50, y: -IO_WIDTH / 2 - 290 },
							{ x: IO_HEIGHT / 2 - 50, y: -IO_WIDTH / 2 - 470 },
						],
					},

					// Left
					{
						id: 'net_T',
						value: false,
						points: [
							{ x: IO_HEIGHT / 2 - 90, y: -IO_WIDTH / 2 - 30 },
							{ x: IO_HEIGHT / 2 - 90, y: -IO_WIDTH / 2 - 270 },
							{ x: IO_HEIGHT / 2 - 330, y: -IO_WIDTH / 2 - 270 },
						],
					},
					{
						id: 'net_pad',
						value: false,
						points: [
							{ x: 30, y: IO_WIDTH / 2 - 30 },
							{ x: 30, y: IO_WIDTH / 2 + 150 - 30 },
						],
					},
				],
				pads: [
					{
						pos: { x: IO_HEIGHT / 2 - 25, y: IO_WIDTH / 2 + 220 },
						size: { width: 50, height: 50 },
					},
				],
			},

			// Right IO BANK
			{
				pos: { x: 50 + IO_WIDTH / 2, y: 530 },
				size: { width: IO_HEIGHT, height: IO_WIDTH },
				nets: [
					{ id: `net_ts_mux`, value: false, points: [] },
					{ id: `net_io_clk`, value: false, points: [] },
					{ id: `net_in_q`, value: false, points: [] },
					// Right
					{
						id: 'net_T',
						value: false,
						points: [
							{ x: -IO_HEIGHT / 2 + 150, y: -IO_WIDTH / 2 - 30 },
							{ x: -IO_HEIGHT / 2 + 150, y: -IO_WIDTH / 2 - 210 },
						],
					},

					// Middle
					{
						id: 'net_I',
						value: false,
						points: [
							{ x: -IO_HEIGHT / 2 + 110, y: -IO_WIDTH / 2 - 30 },
							{ x: -IO_HEIGHT / 2 + 110, y: -IO_WIDTH / 2 - 230 },
							{ x: -IO_HEIGHT / 2 + 330, y: -IO_WIDTH / 2 - 230 },
						],
					},

					// Left
					{
						id: 'net_O',
						value: false,
						points: [
							{ x: -IO_HEIGHT / 2 + 70, y: -IO_WIDTH / 2 - 30 },
							{ x: -IO_HEIGHT / 2 + 70, y: -IO_WIDTH / 2 - 250 },
							{ x: -IO_HEIGHT / 2 + 350, y: -IO_WIDTH / 2 - 250 },
						],
					},
					{
						id: 'net_pad',
						value: false,
						points: [
							{ x: 30, y: IO_WIDTH / 2 - 30 },
							{ x: 30, y: IO_WIDTH / 2 + 150 - 30 },
						],
					},
				],
				pads: [
					{
						pos: { x: IO_HEIGHT / 2 - 25, y: IO_WIDTH / 2 + 220 },
						size: { width: 50, height: 50 },
					},
				],
			},
		],
	},

	/**
	 *
	 * RIGHT SIDE IO BANKS
	 *
	 */
	{
		// All the same but the one in the middle, which shares IO space with the VCC input
		ids: [...id_range('[A-C]H'), ...id_range('[E-G]H')],
		io_bank: [
			// Top IO Bank
			{
				pos: { x: 470, y: 140 },
				size: { width: IO_WIDTH, height: IO_HEIGHT },
				nets: [
					// Top Input
					{
						id: 'net_T',
						value: false,
						points: [
							{ x: -IO_WIDTH / 2, y: -20 },
							{ x: -IO_WIDTH / 2 - 140, y: -20 },
						],
					},

					// Middle Output
					{
						id: 'net_I',
						value: false,
						points: [
							{ x: -IO_WIDTH / 2, y: 20 },
							{ x: -IO_WIDTH / 2 - 240, y: 20 },
							{ x: -IO_WIDTH / 2 - 240, y: 160 },
						],
					},

					// Bottom Input
					{
						id: 'net_O',
						value: false,
						points: [
							{ x: -IO_WIDTH / 2, y: 60 },
							{ x: -IO_WIDTH / 2 - 220, y: 60 },
							{ x: -IO_WIDTH / 2 - 220, y: 180 },
							{ x: -IO_WIDTH / 2 - 220, y: 60, continuous: false },
							{ x: -IO_WIDTH / 2 - 220, y: -180 },
						],
					},
				],
			},

			// Bottom IO Bank
			{
				pos: { x: 470, y: 400 },
				size: { width: IO_WIDTH, height: IO_HEIGHT },
				nets: [
					// Top Input
					{
						id: 'net_T',
						value: false,
						points: [
							{ x: -IO_WIDTH / 2, y: -20 },
							{ x: -IO_WIDTH / 2 - 140, y: -20 },
						],
					},

					// Middle Output
					{
						id: 'net_I',
						value: false,
						points: [
							{ x: -IO_WIDTH / 2, y: 20 },
							{ x: -IO_WIDTH / 2 - 180, y: 20 },
							{ x: -IO_WIDTH / 2 - 180, y: -160 },
						],
					},

					// Bottom Input
					{
						id: 'net_O',
						value: false,
						points: [
							{ x: -IO_WIDTH / 2, y: 60 },
							{ x: -IO_WIDTH / 2 - 200, y: 60 },
							{ x: -IO_WIDTH / 2 - 200, y: 260 },
							{ x: -IO_WIDTH / 2 - 200, y: 60, continuous: false },
							{ x: -IO_WIDTH / 2 - 200, y: -160 },
						],
					},
				],
			},
		],
	},
	{
		// Middle right IO bank that shares space with VCC
		ids: ['DH'],
		io_bank: [
			// Top IO Bank
			{
				pos: { x: 470, y: 140 },
				size: { width: IO_WIDTH, height: IO_HEIGHT },
				nets: [
					// Top Input
					{
						id: 'net_T',
						value: false,
						points: [
							{ x: -IO_WIDTH / 2, y: -20 },
							{ x: -IO_WIDTH / 2 - 140, y: -20 },
						],
					},

					// Middle Output
					{
						id: 'net_I',
						value: false,
						points: [
							{ x: -IO_WIDTH / 2, y: 20 },
							{ x: -IO_WIDTH / 2 - 240, y: 20 },
							{ x: -IO_WIDTH / 2 - 240, y: 160 },
						],
					},

					// Bottom Input
					{
						id: 'net_O',
						value: false,
						points: [
							{ x: -IO_WIDTH / 2, y: 60 },
							{ x: -IO_WIDTH / 2 - 220, y: 60 },
							{ x: -IO_WIDTH / 2 - 220, y: 180 },
							{ x: -IO_WIDTH / 2 - 220, y: 60, continuous: false },
							{ x: -IO_WIDTH / 2 - 220, y: -180 },
						],
					},
				],
			},
		],
	},

	/**
	 *
	 * TOP IO Banks
	 *
	 */
	{
		// All bottom IO except AA, which is slightly different (sigh)
		ids: id_range('A[B-H]'),
		io_bank: [
			// Left IO BANK
			{
				pos: { x: -50 - IO_WIDTH / 2, y: -510 },
				size: { width: IO_HEIGHT, height: IO_WIDTH },
				nets: [
					// Left
					{
						id: 'net_T',
						value: false,
						points: [
							{ x: IO_HEIGHT / 2 - 90, y: IO_WIDTH / 2 - 30 },
							{ x: IO_HEIGHT / 2 - 90, y: IO_WIDTH / 2 + 190 },
							{ x: IO_HEIGHT / 2 - 290, y: IO_WIDTH / 2 + 190 },
						],
					},

					// Middle
					{
						id: 'net_I',
						value: false,
						points: [
							{ x: IO_HEIGHT / 2 - 50, y: IO_WIDTH / 2 - 30 },
							{ x: IO_HEIGHT / 2 - 50, y: IO_WIDTH / 2 + 210 },
							{ x: IO_HEIGHT / 2 - 270, y: IO_WIDTH / 2 + 210 },
							{ x: IO_HEIGHT / 2 - 50, y: IO_WIDTH / 2 + 210, continuous: false },
							{ x: IO_HEIGHT / 2 - 50, y: IO_WIDTH / 2 + 170 },
							{ x: IO_HEIGHT / 2 + 50, y: IO_WIDTH / 2 + 170 },
						],
					},

					// Right
					{
						id: 'net_O',
						value: false,
						points: [
							{ x: IO_HEIGHT / 2 - 10, y: IO_WIDTH / 2 - 30 },
							{ x: IO_HEIGHT / 2 - 10, y: IO_WIDTH / 2 + 130 },
						],
					},
				],
			},

			// Right IO BANK
			{
				pos: { x: 50 + IO_WIDTH / 2, y: -510 },
				size: { width: IO_HEIGHT, height: IO_WIDTH },
				nets: [
					// Left
					{
						id: 'net_T',
						value: false,
						points: [
							{ x: IO_HEIGHT / 2 - 130, y: IO_WIDTH / 2 - 30 },
							{ x: IO_HEIGHT / 2 - 130, y: IO_WIDTH / 2 + 170 },
							{ x: IO_HEIGHT / 2 + 170, y: IO_WIDTH / 2 + 170 },
						],
					},

					// Middle
					{
						id: 'net_I',
						value: false,
						points: [
							{ x: IO_HEIGHT / 2 - 90, y: IO_WIDTH / 2 - 30 },
							{ x: IO_HEIGHT / 2 - 90, y: IO_WIDTH / 2 + 150 },
							{ x: IO_HEIGHT / 2 + 150, y: IO_WIDTH / 2 + 150 },
						],
					},

					// Right
					{
						id: 'net_O',
						value: false,
						points: [
							{ x: IO_HEIGHT / 2 - 50, y: IO_WIDTH / 2 - 30 },
							{ x: IO_HEIGHT / 2 - 50, y: IO_WIDTH / 2 + 130 },
						],
					},
				],
			},
		],
	},
];

const bus_config: Net[] = [
	{
		id: 'global.net_clk',
		value: false,
		points: [
			{ x: -160, y: 4160 },
			{ x: -160, y: CLK_TOP },
			{ x: 3600, y: CLK_TOP },
			{ x: 460, y: CLK_TOP, continuous: false },
			{ x: 460, y: 4160 },
			{ x: 980, y: CLK_TOP, continuous: false },
			{ x: 980, y: 4160 },
			{ x: 1500, y: CLK_TOP, continuous: false },
			{ x: 1500, y: 4160 },
			{ x: 2020, y: CLK_TOP, continuous: false },
			{ x: 2020, y: 4160 },
			{ x: 2540, y: CLK_TOP, continuous: false },
			{ x: 2540, y: 4160 },
			{ x: 3060, y: CLK_TOP, continuous: false },
			{ x: 3060, y: 4160 },
			{ x: 3580, y: CLK_TOP, continuous: false },
			{ x: 3580, y: 4160 },
		],
	},

	/**
	 *
	 *  VERTICAL GLOBAL BUSSES, 0 = Left, 8 = Right
	 *
	 */

	// Left most verilog long lines (IDX 0)
	{
		id: 'global_V0.net_0',
		value: false,
		points: [
			{ x: -200, y: 0 },
			{ x: -200, y: 4460 },
		],
	},
	{
		id: 'global_V0.net_1',
		value: false,
		points: [
			{ x: -180, y: 0 },
			{ x: -180, y: 4500 },
		],
	},

	// Vertical set 1
	{
		id: 'global_V1.net_0',
		value: false,
		points: [
			{ x: 420, y: 0 },
			{ x: 420, y: 4460 },
		],
	},
	{
		id: 'global_V1.net_1',
		value: false,
		points: [
			{ x: 440, y: 0 },
			{ x: 440, y: 4500 },
		],
	},

	// Vertical set 2
	{
		id: 'global_V2.net_0',
		value: false,
		points: [
			{ x: 940, y: 0 },
			{ x: 940, y: 4460 },
		],
	},
	{
		id: 'global_V2.net_1',
		value: false,
		points: [
			{ x: 960, y: 0 },
			{ x: 960, y: 4500 },
		],
	},

	// Vertical set 3
	{
		id: 'global_V3.net_0',
		value: false,
		points: [
			{ x: 1460, y: 0 },
			{ x: 1460, y: 4460 },
		],
	},
	{
		id: 'global_V3.net_1',
		value: false,
		points: [
			{ x: 1480, y: 0 },
			{ x: 1480, y: 4500 },
		],
	},

	// Vertical set 4
	{
		id: 'global_V4.net_0',
		value: false,
		points: [
			{ x: 1980, y: 0 },
			{ x: 1980, y: 4460 },
		],
	},
	{
		id: 'global_V4.net_1',
		value: false,
		points: [
			{ x: 2000, y: 0 },
			{ x: 2000, y: 4500 },
		],
	},

	// Vertical set 5
	{
		id: 'global_V5.net_0',
		value: false,
		points: [
			{ x: 2500, y: 0 },
			{ x: 2500, y: 4460 },
		],
	},
	{
		id: 'global_V5.net_1',
		value: false,
		points: [
			{ x: 2520, y: 0 },
			{ x: 2520, y: 4500 },
		],
	},

	// Vertical set 6
	{
		id: 'global_V6.net_0',
		value: false,
		points: [
			{ x: 3020, y: 0 },
			{ x: 3020, y: 4460 },
		],
	},
	{
		id: 'global_V6.net_1',
		value: false,
		points: [
			{ x: 3040, y: 0 },
			{ x: 3040, y: 4500 },
		],
	},

	// Vertical set 7
	{
		id: 'global_V7.net_0',
		value: false,
		points: [
			{ x: 3540, y: 0 },
			{ x: 3540, y: 4460 },
		],
	},
	{
		id: 'global_V7.net_1',
		value: false,
		points: [
			{ x: 3560, y: 0 },
			{ x: 3560, y: 4500 },
		],
	},

	// Vertical set 8
	{
		id: 'global_V8.net_0',
		value: false,
		points: [
			{ x: 3980, y: 0 },
			{ x: 3980, y: 4460 },
		],
	},
	{
		id: 'global_V8.net_1',
		value: false,
		points: [
			{ x: 4000, y: 0 },
			{ x: 4000, y: 4500 },
		],
	},

	/**
	 *
	 *  HORIZONTAL GLOBAL BUSSES, 0 = Left, 9 = Right
	 *
	 */

	// Top most horizontal long lines (IDX 0)
	{
		id: 'global_H0.net_0',
		value: false,
		points: [
			{ x: -240, y: -120 },
			{ x: 4000, y: -120 },
		],
	},
	{
		id: 'global_H1.net_0',
		value: false,
		points: [
			{ x: -320, y: 500 },
			{ x: 4120, y: 500 },
		],
	},
	{
		id: 'global_H2.net_0',
		value: false,
		points: [
			{ x: -320, y: 1060 },
			{ x: 4120, y: 1060 },
		],
	},
	{
		id: 'global_H3.net_0',
		value: false,
		points: [
			{ x: -320, y: 1620 },
			{ x: 4120, y: 1620 },
		],
	},
	{
		id: 'global_H4.net_0',
		value: false,
		points: [
			{ x: -320, y: 2180 },
			{ x: 4120, y: 2180 },
		],
	},
	{
		id: 'global_H5.net_0',
		value: false,
		points: [
			{ x: -320, y: 2740 },
			{ x: 4120, y: 2740 },
		],
	},
	{
		id: 'global_H6.net_0',
		value: false,
		points: [
			{ x: -320, y: 3300 },
			{ x: 4120, y: 3300 },
		],
	},
	{
		id: 'global_H7.net_0',
		value: false,
		points: [
			{ x: -320, y: 3860 },
			{ x: 4120, y: 3860 },
		],
	},
	{
		id: 'global_H8.net_0',
		value: false,
		points: [
			{ x: -320, y: 4460 },
			{ x: 4120, y: 4460 },
		],
	},
	{
		id: 'global_VIOL.net_0',
		value: false,
		points: [
			{ x: -320, y: 0 },
			{ x: -320, y: 4460 },
		],
	},
];
