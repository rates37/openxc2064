import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { LogicCell } from './models/LogicCell';
import { SwitchMatrix } from './models/SwitchMatrix';
import { Net, Pip } from './types';
import { initialiseSimulation } from './InitialiseSimulation';
import { IOBank, IOPad } from './models/IOBank';
import { createExportStateFunction, createImportStateFunction } from './SaveSimulation';

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

	// Simulation stats
	simStats: { avg_steps: number; avg_time: number; min_time: number; max_time: number } | null;
}

const SimulatorContext = createContext<SimulatorContextValue | undefined>(undefined);

export const SimulatorProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
	/**
	 *
	 * State variables for everything that is managed globally across the simulator
	 *
	 */
	const [isRunning, setIsRunning] = useState(false);
	const [showGrid, setShowGrid] = useState(true);
	const [tick, setTick] = useState(0);
	const [logicCells, setLogicCells] = useState<LogicCell[]>([]);
	const [switchMatrices, setSwitchMatrices] = useState<SwitchMatrix[]>([]);
	const [pips, setPips] = useState<Pip[]>([]);
	const [ioBanks, setIoBanks] = useState<IOBank[]>([]);
	const [busNets, setBusNets] = useState<Net[]>([]);
	const [drivers, setDrivers] = useState<{ source: string; destination: string }[]>([]);
	const [oscillator, setOscillator] = useState({ enabled: false, frequency: 1 });
	const [selectedMatrix, setSelectedMatrix] = useState<SwitchMatrix | null>(null);
	const [selectedCell, setSelectedCell] = useState<LogicCell | null>(null);
	const [selectedIOBank, setSelectedIOBank] = useState<IOBank | null>(null);
	const [cursorPos, setCursorPos] = useState<{ x: number; y: number } | null>(null);
	const [searchQuery, setSearchQuery] = useState<string | null>(null);
	const [simStats, setSimStats] = useState<{ avg_steps: string; avg_time: number; min_time: number; max_time: number } | null>(null);

	// Dummy update function to force a re-render of the simulator canvas. This is nice, because it means we can only re-render the display after the simulation is settled, not between each step.
	const bumpTick = useCallback(() => setTick((t) => t + 1), []);

	// Manage the background grid button
	const toggleGrid = useCallback(() => setShowGrid((prev) => !prev), []);

	// Import/Export functions
	const exportState = useCallback(() => createExportStateFunction(logicCells, switchMatrices, pips, ioBanks, drivers)(), [logicCells, switchMatrices, pips, ioBanks, drivers]);
	const importState = useCallback(() => createImportStateFunction(logicCells, switchMatrices, ioBanks, setPips, setDrivers, bumpTick)(), [logicCells, switchMatrices, ioBanks, bumpTick]);

	// Driver management functions
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

	// Toggle a PIP on/off by index in the pips array
	const togglePip = useCallback((index: number) => {
		setPips((prev) => prev.map((pip, i) => (i === index ? { ...pip, enabled: !pip.enabled } : pip)));
	}, []);

	const updateIOBank = useCallback((updatedBank: IOBank) => {
		setIoBanks((prev) => prev.map((bank, i) => (bank.id === updatedBank.id ? updatedBank : bank)));
	}, []);

	// Manage the selected primative to select which (if any) modal should be shown.
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

	const propagateDriver = useCallback((source: string) => {
		drivers
			.filter((d) => d.source === source)
			.forEach((driver) => {
				const sourceNet = getNet(driver.source);
				const destNet = getNet(driver.destination);
				if (sourceNet && destNet) {
					destNet.value = sourceNet.value;
					propagateDriver(driver.destination); // Recursively propagate the change to any nets driven by the destination net
				}

				const clb_inputs = ['net_A', 'net_B', 'net_C', 'net_D', 'net_K'];
				const destSplit = driver.destination.split('.');
				// console.log(driver.destination, destSplit);
				if (destSplit[0].length == 2 && clb_inputs.includes(destSplit[1])) {
					// If the destination is a CLB input, we need to trigger a simulation of that CLB to ensure the new value propagates to the output
					// console.log(`Triggering simulation of ${destSplit[0]} due to driver change on ${driver.destination}`); // Debug log
					const cell = logicCells.find((c) => c.id === destSplit[0]);

					// Save a copy of the cells x and y to detect a change
					const cellX = cell?.nets.find((n) => n.id === 'net_X')?.value;
					const cellY = cell?.nets.find((n) => n.id === 'net_Y')?.value;

					cell?.simulate();

					if (cell && cell?.nets.find((n) => n.id === 'net_X')?.value !== cellX) propagateDriver(`${cell.id}.net_X`);

					if (cell && cell?.nets.find((n) => n.id === 'net_Y')?.value !== cellY) propagateDriver(`${cell.id}.net_Y`);
				}
			});
	});

	// simulate: your main entry-point for running a simulation step/cycle.
	// Keeps ticking until all net values have settled (no changes between steps).
	const simulate = useCallback(() => {
		setIsRunning(true);
		// console.log(pips);
		const startTime = performance.now();

		const MAX_ITERATIONS = 25;

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

		// Get all nets that can possibley trigger a change in the simulation
		const inputNets = ioBanks.flatMap((bank) => bank.nets).filter((net) => net.id.endsWith('net_I')).map((net) => net.id); // All IO Bank pad nets are potential inputs
		inputNets.push('global.net_osc_in'); // Oscillator net is also a potential input

        for (const clb of logicCells) {
            if (!clb) continue;

            if (clb.isConstant()) {
                const xnet = `${clb.id}.${clb.nets.find((n) => n.id === 'net_X')?.id}`;
                const ynet = `${clb.id}.${clb.nets.find((n) => n.id === 'net_Y')?.id}`;
                inputNets.push(xnet, ynet);
            }
        }

		while (!settled && steps < MAX_ITERATIONS) {
			const before = snapshotNets();

			// Simulate IOBanks after PIPs propagate, so they account for any incoming values
			ioBanks.forEach((bank) => {
				bank.simulate();
			});
			
			inputNets.forEach((net_id) => {
				propagateDriver(net_id);
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

		// console.log(`Simulation settled after ${steps} step(s) in ${(endTime - startTime).toFixed(1)} ms`);

		// Update simulation stats
		setSimStats((prev) => {
			const newStats = {
				avg_steps: ((prev?.avg_steps ? parseFloat(prev.avg_steps) : 0) * tick + steps) / (tick + 1),
				avg_time: ((prev?.avg_time ?? 0) * tick + (endTime - startTime)) / (tick + 1),
				min_time: prev?.min_time ? Math.min(prev.min_time, endTime - startTime) : endTime - startTime,
				max_time: prev?.max_time ? Math.max(prev.max_time, endTime - startTime) : endTime - startTime,
			};

			// console.log(`Simulation stats: \n\tAvg Steps: ${newStats.avg_steps.toFixed(2)}\n\tAvg Time: ${newStats.avg_time.toFixed(1)} ms\n\tMin Time: ${newStats.min_time.toFixed(1)} ms\n\tMax Time: ${newStats.max_time.toFixed(1)} ms`);
			return newStats;
		});

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

	// Put together all of the possible values and functions that are available to the useSimulator hook.
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
		simStats: simStats,
	};

	return <SimulatorContext.Provider value={value}>{children}</SimulatorContext.Provider>;
};

export const useSimulator = (): SimulatorContextValue => {
	const context = useContext(SimulatorContext);
	if (context === undefined) {
		throw new Error('useSimulator must be used within a <SimulatorProvider>');
	}
	return context;
};
