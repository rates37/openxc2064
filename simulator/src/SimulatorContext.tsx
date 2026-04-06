import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { LogicCell } from './models/LogicCell';
import { SwitchMatrix } from './models/SwitchMatrix';
import { Net, Pip } from './types';
import { initialiseSimulation } from './InitialiseSimulation';
import { IOBank, IOPad } from './models/IOBank';

interface SimulatorContextValue {
	/**
	 * Basic Variables
	 */
	isRunning: boolean;
	tick: number;
	showGrid: boolean;

	/**
	 * Simulation Primatives
	 */

	// Logic Cells
	logicCells: LogicCell[];
	selectedCell: LogicCell | null;
	selectCell: (cell: LogicCell | null) => void;
	setLogicCells: React.Dispatch<React.SetStateAction<LogicCell[]>>;

	// Switch Matrices (MaGiCBoxes)
	switchMatrices: SwitchMatrix[];
	selectedMatrix: SwitchMatrix | null;
	selectMatrix: (matrix: SwitchMatrix | null) => void;
	saveMatrixConnections: (matrixIndex: number, connections: number[][]) => void;

	// Programmable Interconnect Points (PIPs)
	pips: Pip[];
	togglePip: (index: number) => void;

	// IO Banks
	ioBanks: IOBank[];
	selectedIOBank: IOBank | null;
	selectIOBank: (bank: IOBank | null) => void;
	updateIOBank: (updatedBank: IOBank) => void;
	toggleIONet: (bankIndex: number) => void;

	// Global Bus Nets
	busNets: Net[];

	// Drivers: keeps track of which net is currently driving another net through a PIP, to allow for bidirectional behavior
	drivers: { source: string; destination: string }[];
	setDriver(source: string | null, destination: string): void;
	removeDriver(destination: string): void;
	hasDriver(dest: string): boolean;

	/**
	 * Simulation Utility Functions
	 */
	simulate: () => void;
	toggleGrid: () => void;
	getNet: (globalNetId: string) => Net | undefined;

	// Cursor Position information
	cursorPos: { x: number; y: number } | null;
	setCursorPos: (pos: { x: number; y: number } | null) => void;
	exportState: () => void;
	importState: () => void;

	// Search state: id of net to highlight (e.g. "AA.net_0")
	searchQuery: string | null;
	setSearchQuery: (q: string | null) => void;

	// Oscillator state
	oscillator: { enabled: boolean; frequency: number };
	setOscillator: (osc: { enabled: boolean; frequency: number }) => void;
}

const SimulatorContext = createContext<SimulatorContextValue | undefined>(undefined);

export const SimulatorProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
	const [isRunning, setIsRunning] = useState(false);
	const [showGrid, setShowGrid] = useState(true);
	const [tick, setTick] = useState(0);

	const bumpTick = useCallback(() => setTick((t) => t + 1), []);

	const toggleGrid = useCallback(() => setShowGrid((prev) => !prev), []);

	const [logicCells, setLogicCells] = useState<LogicCell[]>([]);
	const [switchMatrices, setSwitchMatrices] = useState<SwitchMatrix[]>([]);
	const [pips, setPips] = useState<Pip[]>([]);
	const [ioBanks, setIoBanks] = useState<IOBank[]>([]);
	const [busNets, setBusNets] = useState<Net[]>([]);
	const [drivers, setDrivers] = useState<{ source: string; destination: string }[]>([]);
	const [oscillator, setOscillator] = useState({ enabled: false, frequency: 1 });

	const setDriver = useCallback((source: string, destination: string) => {
		console.log(source, destination);
		setDrivers((prev) => {
			return [...prev, { source, destination }];
		});
	}, []);

	const removeDriver = useCallback((destination: string) => {
		setDrivers((prev) => prev.filter((d) => d.destination !== destination));
	}, []);

	const hasDriver = useCallback(
		(destination: string) => {
			return drivers.some((d) => d.destination === destination);
		},
		[drivers],
	);

	const togglePip = useCallback((index: number) => {
		const current_pips = pips;
		const pip = current_pips[index];

		setPips((prev) => prev.map((pip, i) => (i === index ? { ...pip, enabled: !pip.enabled } : pip)));
	}, []);

	const updateIOBank = useCallback((updatedBank: IOBank) => {
		setIoBanks((prev) => prev.map((bank, i) => (bank.id === updatedBank.id ? updatedBank : bank)));
	}, []);

	const [selectedMatrix, setSelectedMatrix] = useState<SwitchMatrix | null>(null);
	const [selectedCell, setSelectedCell] = useState<LogicCell | null>(null);
	const [selectedIOBank, setSelectedIOBank] = useState<IOBank | null>(null);
	const [cursorPos, setCursorPos] = useState<{ x: number; y: number } | null>(null);
	const [searchQuery, setSearchQuery] = useState<string | null>(null);

	const selectCell = useCallback((cell: LogicCell | null) => {
		setSelectedCell(cell);
	}, []);

	const selectMatrix = useCallback((matrix: SwitchMatrix | null) => {
		setSelectedMatrix(matrix);
	}, []);

	const selectIOBank = useCallback((bank: IOBank | null) => {
		setSelectedIOBank(bank);
	}, []);

	const saveMatrixConnections = useCallback(
		(matrixIndex: number, connections: number[][]) => {
			const matrix = switchMatrices[matrixIndex];
			if (!matrix) return;
			matrix.connections = connections;
			simulate();
		},
		[switchMatrices, bumpTick],
	);

	const toggleIONet = useCallback(
		(bankIndex: number) => {
			const bank = ioBanks[bankIndex];
			if (!bank) return;
			const net = bank.nets.find((n) => n.id === `${bank.id}.net_pad`);
			if (net) net.value = !net.value;
			// Trigger state update to ensure React re-renders with the new value
			setIoBanks((prev) => [...prev]);
			simulate();
		},
		[ioBanks, pips, bumpTick],
	);

	// -- Functions --
	// Wrap in useCallback to keep stable references and avoid unnecessary
	// re-renders in consumers.

	const getNet = useCallback(
		(globalNetId: string): Net | undefined => {
            // Split the net into [Location].[id], as specified in detail in the decodeRelativeNetName function below
			const [location, id] = globalNetId.split('.');
            
			const allCellIds = logicCells.map((cell) => cell.id);
            
			// If the location is only two chars, then we can assume it is a cell id, and we can look for the net in that cell's nets
			// If we assumed wrong, it will return undefined and be handled by the caller.
			if (allCellIds.includes(location[0] + location[1]) && location.length === 2) {
                const cell = logicCells.find((cell) => cell.id === location);
				return cell?.nets.find((net) => net.id === id);
			}
            
            // If location length is 5, we are expecting a matrix with [Logic Cell ID]_M[Matrix Index] format, e.g. AA_M0
            // If we assumed wrong, it will return undefined and be handled by the caller.
			if (allCellIds.includes(location[0] + location[1]) && location.length === 5 && location[3] === 'M') {
                const matrix = switchMatrices.find((matrix) => matrix.id === location);
				return matrix?.nets.find((net) => net && net.id === globalNetId);
			}
            
            // If location length is 6, we are expecting an IO Block with [Logic Cell ID]_I[IO Index] format, e.g. AA_I0
            // If we assumed wrong, it will return undefined and be handled by the caller.
			if (allCellIds.includes(location[0] + location[1]) && location.length === 6 && location[3] === 'I') {
                const iobank = ioBanks.find((bank) => bank.id === location);
				return iobank?.nets.find((net) => net && net.id === globalNetId);
			}
            
            // If we made it this far, search for the net in the global bus list, if not, return undefined and let the caller handle it
			if (busNets.find((net) => net.id === globalNetId)) {
				return busNets.find((net) => net.id === globalNetId);
			}

			console.log(`Net ${globalNetId} not found in any cell.`, allCellIds.includes(location[0] + location[1]), location[0] + location[1]);
			return undefined;
		},
		[logicCells],
	);

	// simulate: your main entry-point for running a simulation step/cycle.
	// Keeps ticking until all net values have settled (no changes between steps).
	const simulate = useCallback(() => {
		setIsRunning(true);
		// console.log(pips);
		const startTime = performance.now();

		const MAX_ITERATIONS = 10;

		const snapshotNets = (): Map<string, boolean> => {
			const snap = new Map<string, boolean>();
			for (const cell of logicCells) {
				for (const net of cell.nets) {
					snap.set(`${cell.id}.${net.id}`, net.value);
				}
			}

			for (const matrix of switchMatrices) {
				for (const net of matrix.nets) {
					if (net) snap.set(`${matrix.id}.${net.id}`, net.value);
				}
			}

			for (const bank of ioBanks) {
				for (const net of bank.nets) {
					if (net) snap.set(`${bank.id}.${net.id}`, net.value);
				}
			}

			for (const net of busNets) {
				snap.set(net.id, net.value);
			}

			return snap;
		};

		let steps = 0;
		let settled = false;

		while (!settled && steps < MAX_ITERATIONS) {
			const before = snapshotNets();

			logicCells.forEach((cell) => {
				cell.simulate();
			});

			switchMatrices.forEach((matrix) => {
				matrix.simulate();
			});

			pips.forEach((pip) => {
				if (pip.enabled) {
					const sourceNet = getNet(pip.source);
					const destinationNet = getNet(pip.destination);

					if (sourceNet && destinationNet) {
						if (pip.bidirectional) {
							// Destination is driven by something else, so it drives back to source
							const sourceDrivers = drivers.filter((d) => d.destination === pip.source);

							if (sourceDrivers.some((d) => d.source === pip.destination)) {
								sourceNet.value = destinationNet.value;
							} else {
								destinationNet.value = sourceNet.value;
							}
						} else {
							// Unidirectional: source always drives destination
							destinationNet.value = sourceNet.value;
						}
					}
				}
			});

			// Simulate IOBanks after PIPs propagate, so they account for any incoming values
			ioBanks.forEach((bank) => {
				bank.simulate();
			});

			steps++;

			const after = snapshotNets();
			settled = true;
			for (const [key, val] of after) {
				if (before.get(key) !== val) {
					settled = false;
					break;
				}
			}
		}

		const endTime = performance.now();

		console.log(`Simulation settled after ${steps} step(s) in ${(endTime - startTime).toFixed(1)} ms`);

		if (steps >= MAX_ITERATIONS) {
			console.warn(`Simulation did not settle within ${MAX_ITERATIONS} iterations`);
		}

		setIsRunning(false);
		bumpTick();
	}, [logicCells, switchMatrices, pips, ioBanks, drivers, getNet, bumpTick]);

	// Oscillator timer effect - runs independently from simulation
	useEffect(() => {
		if (!oscillator.enabled) return;

		const halfPeriod = 500 / oscillator.frequency; // milliseconds
		let lastValue = getNet('global.net_osc_in')?.value ?? false;

		const interval = setInterval(() => {
			const oscNet = getNet('global.net_osc_in');
			if (oscNet) {
				const newValue = !lastValue;
				if (newValue !== oscNet.value) {
					oscNet.value = newValue;
					lastValue = newValue;
					simulate();
				}
			}
		}, halfPeriod);

		return () => clearInterval(interval);
	}, [oscillator.enabled, oscillator.frequency, getNet, simulate]);

	useEffect(() => {
		const { logicCells, switchMatrices, pips, ioBanks, busNets } = initialiseSimulation();
		setLogicCells(logicCells);
		setSwitchMatrices(switchMatrices);
		setPips(pips);
		setIoBanks(ioBanks);
		setBusNets(busNets);
	}, []);

	// To add a new function:
	//   1. Declare it in the SimulatorContextValue interface above.
	//   2. Implement it here with useCallback.
	//   3. Include it in the `value` object below.

	// To add a new list:
	//   1. Add the type to the interface (e.g. items: MyItem[]).
	//   2. Create state here (e.g. const [items, setItems] = useState<MyItem[]>([])).
	//   3. (Optional) Create helper functions (addItem, removeItem, etc.).
	//   4. Include the list and helpers in the `value` object below.

	const exportState = useCallback(() => {
		const state = {
			logicCells: logicCells.map((cell) => ({
				id: cell.id,
				muxes: cell.muxes.map((m) => ({ id: m.id, select: m.select })),
				luts: cell.luts.map((l) => ({ id: l.id, truthTable: [...l.truthTable] })),
			})),
			switchMatrices: switchMatrices.map((matrix) => ({
				id: matrix.id,
				connections: matrix.connections.map((row) => [...row]),
			})),
			pips: pips.map((pip) => ({
				id: pip.id,
				source: pip.source,
				destination: pip.destination,
				enabled: pip.enabled,
			})),
		};
		const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = 'xc2064-config.json';
		a.click();
		URL.revokeObjectURL(url);
	}, [logicCells, switchMatrices, pips]);

	const importState = useCallback(() => {
		const input = document.createElement('input');
		input.type = 'file';
		input.accept = '.json';
		input.onchange = () => {
			const file = input.files?.[0];
			if (!file) return;
			const reader = new FileReader();
			reader.onload = () => {
				try {
					const state = JSON.parse(reader.result as string);
					if (state.logicCells) {
						for (const saved of state.logicCells) {
							const cell = logicCells.find((c) => c.id === saved.id);
							if (!cell) continue;
							if (saved.muxes) {
								for (const sm of saved.muxes) {
									const mux = cell.muxes.find((m) => m.id === sm.id);
									if (mux) mux.select = sm.select;
								}
							}
							if (saved.luts) {
								for (const sl of saved.luts) {
									const lut = cell.luts.find((l) => l.id === sl.id);
									if (lut && Array.isArray(sl.truthTable)) {
										lut.truthTable = sl.truthTable;
									}
								}
							}
						}
					}
					if (state.switchMatrices) {
						for (const saved of state.switchMatrices) {
							const matrix = switchMatrices.find((m) => m.id === saved.id);
							if (matrix && saved.connections) {
								matrix.connections = saved.connections;
							}
						}
					}
					if (state.pips) {
						setPips((prev) =>
							prev.map((pip) => {
								const saved = state.pips.find((s: any) => s.source === pip.source && s.destination === pip.destination);
								return saved ? { ...pip, enabled: saved.enabled } : pip;
							}),
						);
					}
					bumpTick();
				} catch (e) {
					console.error('Failed to import state:', e);
				}
			};
			reader.readAsText(file);
		};
		input.click();
	}, [logicCells, switchMatrices, bumpTick]);

	const value: SimulatorContextValue = {
		isRunning: isRunning,
		tick: tick,
		logicCells: logicCells,
		simulate: simulate,
		showGrid: showGrid,
		toggleGrid: toggleGrid,
		getNet: getNet,
		switchMatrices: switchMatrices,
		pips: pips,
		ioBanks: ioBanks,
		togglePip: togglePip,
		selectedMatrix: selectedMatrix,
		selectMatrix: selectMatrix,
		saveMatrixConnections: saveMatrixConnections,
		selectedCell: selectedCell,
		selectCell: selectCell,
		setLogicCells: setLogicCells,
		toggleIONet: toggleIONet,
		selectedIOBank: selectedIOBank,
		selectIOBank: selectIOBank,
		busNets: busNets,
		cursorPos: cursorPos,
		setCursorPos: setCursorPos,
		exportState: exportState,
		importState: importState,
		drivers: drivers,
		setDriver: setDriver,
		removeDriver: removeDriver,
		hasDriver: hasDriver,
		searchQuery: searchQuery,
		setSearchQuery: setSearchQuery,
		updateIOBank: updateIOBank,
		oscillator: oscillator,
		setOscillator: setOscillator,
	};

	return <SimulatorContext.Provider value={value}>{children}</SimulatorContext.Provider>;
};

// =============================================================================
// 4. Custom hook - use this in any component to access the context.
//    Throws if used outside of <SimulatorProvider>.
//
//    Usage:
//      const { simulate, logicCells, isRunning } = useSimulator();
// =============================================================================
export const useSimulator = (): SimulatorContextValue => {
	const context = useContext(SimulatorContext);
	if (context === undefined) {
		throw new Error('useSimulator must be used within a <SimulatorProvider>');
	}
	return context;
};
