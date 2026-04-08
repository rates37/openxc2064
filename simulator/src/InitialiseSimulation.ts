import getConfig from './configs/configs';
import { IOBank, IOPad } from './models/IOBank';
import { LogicCell } from './models/LogicCell';
import { Net, Pip, Mux, LUT } from './types';
import { SwitchMatrix } from './models/SwitchMatrix';
import { CELL_WIDTH, CELL_HEIGHT, CELL_MARGIN_X, CELL_MARGIN_Y, CELL_OFFSET_X, CELL_OFFSET_Y, MATRIX_WIDTH, MATRIX_HEIGHT } from './configs/constants';

const ROWS = 8;
const COLS = 8;

export const initialiseSimulation = (): {
	logicCells: LogicCell[];
	switchMatrices: SwitchMatrix[];
	pips: Pip[];
	ioBanks: IOBank[];
	busNets: Net[];
} => {
	/**
	 * Initialises local copies of each list of primatives
	 */
	const cells: LogicCell[] = [];
	const matrices: SwitchMatrix[] = [];
	const pips: Pip[] = [];
	const ioBanks: IOBank[] = [];

	// Initialise busNets (global long lines and clocks) directly from the config without processing (because they are global!)
	const busNets: Net[] = (getConfig('bus', '') || []).map((net: Net) => ({ ...net, points: net.points.map((p) => ({ ...p })) }));

	// This is a local version of the getNets function in the SimulationContext, but uses the local list copies, not the global ones.
	const localGetNet = (globalNetId: string): Net | undefined => {
		// Split the net into [Location].[id], as specified in detail in the decodeRelativeNetName function below
		const [location, id] = globalNetId.split('.');

		// If the location is only two chars, then we can assume it is a cell id, and we can look for the net in that cell's nets
		// If we assumed wrong, it will return undefined and be handled by the caller.
		if (location.length === 2) {
			const cell = cells.find((c) => c.id === location);
			return cell?.nets.find((net) => net.id === id);
		}

		// If location length is 5, we are expecting a matrix with [Logic Cell ID]_M[Matrix Index] format, e.g. AA_M0
		// If we assumed wrong, it will return undefined and be handled by the caller.
		if (location.length === 5 && location[3] === 'M') {
			const matrix = matrices.find((m) => m.id === location);
			return matrix?.nets.find((net) => net && net.id === globalNetId);
		}

		// If location length is 6, we are expecting an IO Block with [Logic Cell ID]_I[IO Index] format, e.g. AA_I0
		// If we assumed wrong, it will return undefined and be handled by the caller.
		if (location.length === 6 && location[3] === 'I') {
			const iobank = ioBanks.find((bank) => bank.id === location);
			return iobank?.nets.find((net) => net && net.id === globalNetId);
		}

		// If we made it this far, search for the net in the global bus list, if not, return undefined and let the caller handle it
		if (busNets.find((net) => net.id === globalNetId)) {
			return busNets.find((net) => net.id === globalNetId);
		}

		return undefined;
	};

	/**
	 * FIRST CONFIG SETUP PASS.
	 *
	 * Will initialise each of the primitives themselves, but cannot do the relative interconnects until all primitives are created, so those are handled in the second pass below.
	 * All primitives are associated with a CLB, so we can loop over all CLBs, and find the IOBanks, Switches and Pips from there.
	 */
	for (let i = 0; i < ROWS; i++) {
		for (let j = 0; j < COLS; j++) {
			// Cell Ids are letters, one for row, one for col, so top left is AA.
			// Generate the new cells ID
			const cellId = String.fromCharCode(65 + i) + String.fromCharCode(65 + j);

			// Fetch the configs for the logic cell.
			let config = getConfig('logic_cell', cellId);

			// If there is no config for the cell, we can still create it, just with no nets or pips.
			if (!config) {
				config = { nets: [], pips: [] };
			}

			// Calculate the position of the CLB based on the CELL grid denoted in ./configs/constants.ts
			const x = j * (CELL_WIDTH + CELL_MARGIN_X) + CELL_OFFSET_X;
			const y = i * (CELL_HEIGHT + CELL_MARGIN_Y) + CELL_OFFSET_Y;

			// Add the cell to the global list.
			cells.push(new LogicCell(cellId, { ...config, pos: { x, y } }));

			// Fetch ALL switch matrices associated with the current CLB.
			const switchMatrixConfig = getConfig('switch_matrix', cellId);

			// If There are any switch matrices to process, deal with them here.
			if (switchMatrixConfig) {
				switchMatrixConfig.forEach((matrixConfig, index) => {
					// Make Matrix ID
					const matrixId = `${cellId}_M${index}`;

					// Find its world position relative to the CLB and config position
					const x = j * (CELL_WIDTH + CELL_MARGIN_X) + CELL_OFFSET_X + CELL_WIDTH / 2 + matrixConfig.pos.x - MATRIX_WIDTH / 2;
					const y = i * (CELL_HEIGHT + CELL_MARGIN_Y) + CELL_OFFSET_Y + CELL_HEIGHT / 2 - MATRIX_HEIGHT / 2 + matrixConfig.pos.y;

					// Create the matrix
					const matrix = new SwitchMatrix(matrixId, { x, y });

					// Add any nets that are predefined. Will handle relative nets later.
					// Each matrix (excluding some edge cases) are solely "responsible" for the nets to the top and right of the cell.
					// For example, the matrix's bottom nets are actually controll by the switch matrix in the cell below it.
					matrix.nets = matrixConfig.nets.map((net) => ({
						...net,
						id: matrixId + '.' + net.id, // Apply the [location].[net_id] format to the net ids for easier global searching later
						points: net.points.map((p) => ({ ...p })), // Copy the nets, not point to them to avoid reference issues
					}));

					matrices.push(matrix);
				});
			}

			// Fetch ALL IO Banks associated with the current CLB.
			const ioConfig = getConfig('io', cellId);

			// If there are any IO Banks to process, deal with them here.
			if (ioConfig) {
				ioConfig.forEach((ioBankConfig, index) => {
					// Make IO Bank ID
					const ioBankId = `${cellId}_IO${index}`;

					// Find its world position relative to the CLB and config position
					const x = j * (CELL_WIDTH + CELL_MARGIN_X) + CELL_OFFSET_X + CELL_WIDTH / 2 + ioBankConfig.pos.x - ioBankConfig.size.width / 2;
					const y = i * (CELL_HEIGHT + CELL_MARGIN_Y) + CELL_OFFSET_Y + CELL_HEIGHT / 2 - ioBankConfig.size.height / 2 + ioBankConfig.pos.y;

					// Create the IO Bank
					const ioBank = new IOBank(ioBankId, { x, y }, { width: ioBankConfig.size.width, height: ioBankConfig.size.height });

					// Add any nets that are predefined. Will handle relative nets later.
					ioBank.nets = ioBankConfig.nets.map((net) => ({
						...net,
						id: ioBankId + '.' + net.id,
						points: net.points.map((p) => ({ ...p })),
					}));

					// If there is a pad defined in the config, add it to the IO Bank. Will assume only one pad per IO Bank for now, as that is the only possible config for the XC2064
					if (ioBankConfig.pads) ioBank.pad = new IOPad(ioBankConfig.pads[0].pos, ioBankConfig.pads[0].size);

					// IO Pad index to help map Pad name to global index in the bitstream
					ioBank.index = ioBanks.length;

					ioBanks.push(ioBank);
				});
			}
		}
	}

	// Programmable Interconnect Pins (PIP) setup
	// These are also controlled by their local CLB
	for (let i = 0; i < ROWS; i++) {
		for (let j = 0; j < COLS; j++) {
			// Cell Ids are letters, one for row, one for col, so top left is AA
			const cellId = String.fromCharCode(65 + i) + String.fromCharCode(65 + j);

			// Need to grab the logic cell to get its pips
			let config = getConfig('logic_cell', cellId);

			if (!config) {
				config = { nets: [], pips: [] };
				continue; // If there is no config for the cell, we can skip to the next one, as there are no pips to process.
			}

			// Get the world position of the CLB as the reference point for its PIPs
			const x = j * (CELL_WIDTH + CELL_MARGIN_X) + CELL_OFFSET_X;
			const y = i * (CELL_HEIGHT + CELL_MARGIN_Y) + CELL_OFFSET_Y;

			for (const pip of config.pips) {
				// Get the governemnt names of the pip nets based on the relative positioning format specified in the config and detailed in the decodeRelativeNetName function below.
				const sourceNetName = decodeRelativeNetName(pip.source, cellId, { i, j });
				const destinationNetName = decodeRelativeNetName(pip.destination, cellId, { i, j });

				// Add the pip to the list
				pips.push({
					id: pip.id,
					source: sourceNetName,
					destination: destinationNetName,
					enabled: pip.enabled,
					pos: { x: x + pip.pos.x, y: y + pip.pos.y },
					bidirectional: pip.bidirectional,
				});
			}
		}
	}

	/**
	 *
	 *  SECOND CONFIG SETUP PASS.
	 *
	 *  To handle the relative connections between matrices. Has to be done last, after all matrices are created.
	 */
	matrices.forEach((matrix) => {
		const matrixIndex = parseInt(matrix.id[4]);
		const cellId = matrix.id.slice(0, 2);

        // Fetch parent CLB's grid position.
		const i = cellId.charCodeAt(0) - 65;
		const j = cellId.charCodeAt(1) - 65;

		// Figure out the net ids for the ones not managed by this matrix
        // Left char in the cell id
		const left_code = cellId.charCodeAt(0);
		// Right char in the cell id
        const right_code = cellId.charCodeAt(1);

        // Cell id of the one to the left
		let left_cell_id = j > 0 ? String.fromCharCode(left_code) + String.fromCharCode(right_code - 1) : null;
		
        // Cell id for the one to the bottom
        let bottom_cell_id = i < ROWS - 1 ? String.fromCharCode(left_code + 1) + String.fromCharCode(right_code) : null;

        // Current Matrix index, i.e. M0, or M1 etc. Most matrices are connected to the same index of the neighbouring CLB, but there are some edge cases.
		let bottom_index = matrixIndex;
		let left_index = matrixIndex;
    
        // If we are on the left edge.
		if (!left_cell_id && bottom_cell_id) {
			// If the switch cannot find a cell to the left, it must be on the left edge, so it should connect to switch M2 and M3 of the current cell instead.
			if (matrixIndex < 2) {
				left_cell_id = cellId;
				left_index = matrixIndex + 2;
			}
		}

        // If we are on the bottom edge.
        if (left_cell_id && !bottom_cell_id) {
            // If the switch cannot find a cell to the bottom, it must be on the bottom edge, and we can ignore the bottom connections because there is no cell there to connect to.
        }


        // If we are on the top edge (i.e. row 0) 
        if (i === 0) {
			// Handle the edge case of clb AA because it is the only cell with 6 matrices.
			if (cellId === 'AA') {
				if (matrixIndex >= 2) {
					bottom_index = matrixIndex % 2;
				}

				if (matrixIndex >= 4) {
					bottom_cell_id = cellId;
				}
			} else {
            	// Top cells should be M2/M3, and will connect to the local M1/M0 cells bellow, and M2/M3 of the cell to the left if it exists
            	if (matrixIndex >= 2) {
            	    bottom_index = matrixIndex % 2; // M2/M3 should connect to M0/M1 of the cell below
					bottom_cell_id = cellId;
            	}
			}
        }

        // If we are on the right edge (i.e. col 7)
        if (j === COLS - 1) {
            // Right cells should be M1/M0 on both sides, this can be ignored
        }



		if (!left_cell_id) {
			// console.warn(`Matrix ${matrix.id} has invalid neighboring cell on the left`);
		} else {
			// Dont set the bottom and left netss if they already exist, there are some edge cases where it matters.
			if (matrix.nets[6] == undefined || matrix.nets[6]?.id.split('.')[1] === 'dummy') matrix.nets[6] = localGetNet(`${left_cell_id}_M${left_index}.net_3`) || null;
			if (matrix.nets[7] == undefined || matrix.nets[7]?.id.split('.')[1] === 'dummy') matrix.nets[7] = localGetNet(`${left_cell_id}_M${left_index}.net_2`) || null;
		}
		
		if (!bottom_cell_id) {
			// console.warn(`Matrix ${matrix.id} has invalid neighboring cell on the bottom`);
		} else {
			// Dont set the bottom and left nets if they already exist, there are some edge cases where it matters.
			if (matrix.nets[4] == undefined || matrix.nets[4]?.id.split('.')[1] === 'dummy') matrix.nets[4] = localGetNet(`${bottom_cell_id}_M${bottom_index}.net_1`) || null;
			if (matrix.nets[5] == undefined || matrix.nets[5]?.id.split('.')[1] === 'dummy') matrix.nets[5] = localGetNet(`${bottom_cell_id}_M${bottom_index}.net_0`) || null;
		}
	});

	return { logicCells: cells, switchMatrices: matrices, pips, ioBanks, busNets };
};

const decodeRelativeNetName = (netName: string, cellId: string, coords: { i: number; j: number }): string => {
	/**
	 * All nets have a standard format:
	 *          [location].[net_id]
	 *
	 * The location can be either a cell id (e.g. AA), a switch matrix id (e.g. AA_M0), an IO bank id (e.g. AA_IO0), or a global long line identifier (e.g. global_HU).
	 *
	 */

	// If the net name has no location it will default to being 'owned' by the current cell. So we can just prepend the current cell id to it to give it a location.
	if (netName.startsWith('net')) {
		return `${cellId}.${netName}`;
	}

	/**
	 *
	 *  Handle the relative addressing for the global long line nets.
	 *
	 *  The relative addresses for these nets all start with `global`,
	 *  and are then followed by a H (horizontal) or V (vertical) to indicate the direction of the long line.
	 *
	 *  If it is a vertical long line, it is followed by U or D to indicate whether the line is above (U) or below (D) the current cell.
	 *  If it is a horizontal long line, it is followed by L or R to indicate whether the line is to the left (L) or right (R) of the current cell.
	 *
	 *  From there, the net index then defines which net in the bundle it is, starting from top to bottom for vertical lines and left to right for horizontal lines.
	 *  For example:
	 *  - `global_HU.net_0` is the first net, in the horizontal long line bus that is above the current cell.
	 *  - `global_VR.net_3` is the fourth net, in the vertical long line bus that is to the right of the current cell.
	 *
	 */
	if (netName.startsWith('global')) {
		let address = netName.split('_')[1];

		if (address.length == 1) return netName; // Not relative coordinate, so just return as is
		let isHorizontal = address.startsWith('H');
		let dir = address[1];

		if (dir !== 'U' && dir !== 'D' && dir !== 'L' && dir !== 'R') return netName; // Invalid direction, so return as is assuming it is not a relative coordinate

		if (!isHorizontal) {
			let busIdx = coords.j + (dir === 'R' ? 1 : 0);
			return `global_V${busIdx}.${netName.split('.')[1]}`;
		} else {
			let busIdx = coords.i + (dir === 'U' ? 0 : 1);
			return `global_H${busIdx}.${netName.split('.')[1]}`;
		}
	}

	/**
	 * If we got this far, it means the net is referring to a relative coordinate of a neighboring cell. The format for this is either:
	 * - [direction].[net_id] (e.g. N.net_0) if the neighboring cell is in the cardinal directions
	 * - [direction]_[device].[net_id] (e.g. S_M2.net_1) if the neighboring cell is in the cardinal directions and specifies a device (e.g. M2 for switch matrix 3 [zero indexed])
	 *
	 * Because of the way this works, any letter other than a cardinal direction will be considered "this cell", but the standard convention is to use "T" for "This", so T.net_0, or T_M!.net_2 for example.
	 */
	let direction, device;

	// If the [direction] part of the net coordinate is only two chars, it has to be a cell id with no device
	if (netName.split('.')[0].length <= 2) {
		direction = netName.split('.')[0];
		device = '';

		// If not, then it must have a device as well
	} else {
		direction = netName.split('_')[0];
		device = '_' + netName.split('_')[1].split('.')[0];
	}

	let newCellIndex = 0;

	// Calculate the offsets for the neighboring cell based on the direction
	let i_offset = direction.includes('N') ? -1 : direction.includes('S') ? 1 : 0;
	let j_offset = direction.includes('W') ? -1 : direction.includes('E') ? 1 : 0;

	// Make sure the cardinal direction doesn't go off the grid
	if (coords.i + i_offset >= 0 && coords.i + i_offset < ROWS && coords.j + j_offset >= 0 && coords.j + j_offset < COLS) {
		newCellIndex = (coords.i + i_offset) * COLS + (coords.j + j_offset);
	} else {
		console.warn(`Net was searched for, but points to an invalid location ${netName}`);
		return '';
	}

	// Caluclate the new cell id based on the index to avoid passing in the entire cell grid just to resolve a single net coordinate
	const newCellId = String.fromCharCode(65 + Math.floor(newCellIndex / COLS)) + String.fromCharCode(65 + (newCellIndex % COLS));

	// Return the resolved net name with the new cell id and device if applicable
	return `${newCellId}${device}.${netName.split('.')[1]}`;
};
