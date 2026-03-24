import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from "react";
import { LogicCell } from "./models/LogicCell";
import { SwitchMatrix } from "./models/SwitchMatrix";
import { Net, Pip } from "./types";
import getConfig from "./configs/configs";
import {
    CELL_WIDTH,
    CELL_HEIGHT,
    CELL_MARGIN_X,
    CELL_MARGIN_Y,
    CELL_OFFSET_X,
    CELL_OFFSET_Y,
    MATRIX_WIDTH,
    MATRIX_HEIGHT,
} from "./configs/Routing";
import { IOBank, IOPad } from "./models/IOBank";

// =============================================================================
// 1. Define the shape of your context value here.
//    Add new state fields, lists, and functions as needed.
// =============================================================================
interface SimulatorContextValue {
    // -- Example primitive state --
    isRunning: boolean;
    tick: number;

    // -- Example list --
    // Add arrays/lists here. For example:
    //   items: MyItem[];
    logicCells: LogicCell[];
    switchMatrices: SwitchMatrix[];
    pips: Pip[];
    ioBanks: IOBank[];
    busNets: Net[];
    drivers: { source: string; destination: string }[];

    // -- Functions --
    // Add callable functions here. For example:
    //   addItem: (item: MyItem) => void;
    //   removeItem: (id: string) => void;
    simulate: () => void;
    showGrid: boolean;
    toggleGrid: () => void;
    getNet: (globalNetId: string) => Net | undefined;
    togglePip: (index: number) => void;
    selectedMatrix: SwitchMatrix | null;
    selectMatrix: (matrix: SwitchMatrix | null) => void;
    saveMatrixConnections: (matrixIndex: number, connections: number[][]) => void;
    selectedCell: LogicCell | null;
    selectCell: (cell: LogicCell | null) => void;
    setLogicCells: React.Dispatch<React.SetStateAction<LogicCell[]>>;
    toggleIONet: (bankIndex: number) => void;
    // Selected IO bank for modal editing
    selectedIOBank: IOBank | null;
    selectIOBank: (bank: IOBank | null) => void;
    cursorPos: { x: number; y: number } | null;
    setCursorPos: (pos: { x: number; y: number } | null) => void;
    exportState: () => void;
    importState: () => void;
    // Search state: id of net to highlight (e.g. "AA.net_0")
    searchQuery: string | null;
    setSearchQuery: (q: string | null) => void;
    setDriver(source: string | null, destination: string): void;
    removeDriver(destination: string): void;
    hasDriver(dest): boolean;

    // To add more functions, declare them in this interface and
    // implement them inside SimulatorProvider below.
}

// =============================================================================
// 2. Create the context with `undefined` default so we can enforce usage
//    inside the provider tree.
// =============================================================================
const SimulatorContext = createContext<SimulatorContextValue | undefined>(undefined);

// =============================================================================
// 3. Provider component - wraps your app (or a subtree) and supplies state.
//    All state, lists, and functions live here.
// =============================================================================
export const SimulatorProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    // -- State --
    const [isRunning, setIsRunning] = useState(false);
    const [showGrid, setShowGrid] = useState(true);
    const [tick, setTick] = useState(0);

    const bumpTick = useCallback(() => setTick((t) => t + 1), []);

    const toggleGrid = useCallback(() => setShowGrid((prev) => !prev), []);

    // -- Lists --
    // Manage arrays via useState. Example:
    //   const [items, setItems] = useState<MyItem[]>([]);
    const [logicCells, setLogicCells] = useState<LogicCell[]>([]);
    const [switchMatrices, setSwitchMatrices] = useState<SwitchMatrix[]>([]);
    const [pips, setPips] = useState<Pip[]>([]);
    const [ioBanks, setIoBanks] = useState<IOBank[]>([]);
    const [busNets, setBusNets] = useState<Net[]>([]);
    const [drivers, setDrivers] = useState<{ source: string; destination: string }[]>([]);

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
        [drivers]
    );

    const togglePip = useCallback((index: number) => {
        const current_pips = pips;
        const pip = current_pips[index];

        setPips((prev) => prev.map((pip, i) => (i === index ? { ...pip, enabled: !pip.enabled } : pip)));
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

    const toggleConnection = useCallback(
        (matrixIndex: number, row: number, col: number) => {
            const matrix = switchMatrices[matrixIndex];
            if (!matrix) return;
            if (!matrix.possibleConnections[row][col]) return;
            matrix.connections[row][col] = matrix.connections[row][col] ? 0 : 1;
            bumpTick();
            setSelectedMatrix(matrix);
        },
        [switchMatrices, bumpTick]
    );

    const saveMatrixConnections = useCallback(
        (matrixIndex: number, connections: number[][]) => {
            const matrix = switchMatrices[matrixIndex];
            if (!matrix) return;
            matrix.connections = connections;
            bumpTick();
        },
        [switchMatrices, bumpTick]
    );

    const toggleIONet = useCallback(
        (bankIndex: number) => {
            const bank = ioBanks[bankIndex];
            if (!bank) return;
            const net = bank.nets.find((n) => n.id === `${bank.id}.net_pad`);
            if (net) net.value = !net.value;
            bumpTick();
        },
        [ioBanks, bumpTick]
    );

    // -- Functions --
    // Wrap in useCallback to keep stable references and avoid unnecessary
    // re-renders in consumers.

    // getNet: a helper function to resolve a global net ID to the actual Net object, in either a logic cell, or a global line.
    const getNet = useCallback(
        (globalNetId: string): Net | undefined => {
            const [location, id] = globalNetId.split(".");

            const allCellIds = logicCells.map((cell) => cell.id);

            if (allCellIds.includes(location[0] + location[1]) && location.length === 2) {
                const cell = logicCells.find((cell) => cell.id === location);
                return cell?.nets.find((net) => net.id === id);
            }

            // if first char is M
            if (allCellIds.includes(location[0] + location[1]) && location.length === 5 && location[3] === "M") {
                const matrix = switchMatrices.find((matrix) => matrix.id === location);
                return matrix?.nets.find((net) => net && net.id === globalNetId);
            }

            if (allCellIds.includes(location[0] + location[1]) && location.length === 6 && location[3] === "I") {
                const iobank = ioBanks.find((bank) => bank.id === location);
                return iobank?.nets.find((net) => net && net.id === globalNetId);
            }

            if (busNets.find((net) => net.id === globalNetId)) {
                return busNets.find((net) => net.id === globalNetId);
            }

            console.log(
                `Net ${globalNetId} not found in any cell.`,
                allCellIds.includes(location[0] + location[1]),
                location[0] + location[1]
            );

            return undefined;
        },
        [logicCells]
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

            ioBanks.forEach((bank) => {
                if (bank.used) {
                    bank.simulate();
                }
            });

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
                            // console.log("Has driver source: " + hasDriver(pip.source) + " destination: " + hasDriver(pip.destination));
                            if (drivers.filter((driver) => driver.source === pip.destination).length > 0) {
                                sourceNet.value = destinationNet.value;
                            } else {
                                destinationNet.value = sourceNet.value;
                            }

                        } else {
                            destinationNet.value = sourceNet.value;
                        }



                    }
                }
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

        // Update Simulation
        bumpTick();

        const endTime = performance.now();
        console.log(`Simulation settled after ${steps} step(s) in ${(endTime - startTime).toFixed(2)} ms`);
        if (steps >= MAX_ITERATIONS) {
            console.warn(`Simulation did not settle within ${MAX_ITERATIONS} iterations`);
        }
        setIsRunning(false);
    }, [logicCells, switchMatrices, pips, getNet]);

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
        const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "xc2064-config.json";
        a.click();
        URL.revokeObjectURL(url);
    }, [logicCells, switchMatrices, pips]);

    const importState = useCallback(() => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = ".json";
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
                            })
                        );
                    }
                    bumpTick();
                } catch (e) {
                    console.error("Failed to import state:", e);
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
        throw new Error("useSimulator must be used within a <SimulatorProvider>");
    }
    return context;
};

const ROWS = 8;
const COLS = 8;

const initialiseSimulation = (): {
    logicCells: LogicCell[];
    switchMatrices: SwitchMatrix[];
    pips: Pip[];
    ioBanks: IOBank[];
    busNets: Net[];
} => {
    const cells: LogicCell[] = [];
    const matrices: SwitchMatrix[] = [];
    const pips: Pip[] = [];
    const ioBanks: IOBank[] = [];
    const busNets: Net[] = (getConfig("bus", "") || []).map((net: Net) => ({ ...net, points: net.points.map((p) => ({ ...p })) }));

    // Local resolver that operates on the arrays being built, rather than
    // the (empty) React state that exists at mount time.
    const localGetNet = (globalNetId: string): Net | undefined => {
        const [location, id] = globalNetId.split(".");

        if (location.length === 2) {
            const cell = cells.find((c) => c.id === location);
            return cell?.nets.find((net) => net.id === id);
        }

        if (location.length === 5 && location[3] === "M") {
            const matrix = matrices.find((m) => m.id === location);
            return matrix?.nets.find((net) => net && net.id === globalNetId);
        }

        if (location.length === 6 && location[3] === "I") {
            const iobank = ioBanks.find((bank) => bank.id === location);
            return iobank?.nets.find((net) => net && net.id === globalNetId);
        }

        if (busNets.find((net) => net.id === globalNetId)) {
            return busNets.find((net) => net.id === globalNetId);
        }

        return undefined;
    };

    for (let i = 0; i < ROWS; i++) {
        for (let j = 0; j < COLS; j++) {
            // Cell Ids are letters, one for row, one for col, so top left is AA
            const cellId = String.fromCharCode(65 + i) + String.fromCharCode(65 + j);
            let config = getConfig("logic_cell", cellId);

            if (!config) {
                config = { nets: [], pips: [] };
            }

            const x = j * (CELL_WIDTH + CELL_MARGIN_X) + CELL_OFFSET_X;
            const y = i * (CELL_HEIGHT + CELL_MARGIN_Y) + CELL_OFFSET_Y;

            cells.push(new LogicCell(cellId, { ...config, pos: { x, y } }));

            const switchMatrixConfig = getConfig("switch_matrix", cellId);

            if (switchMatrixConfig) {
                switchMatrixConfig.forEach((matrixConfig, index) => {
                    const matrixId = `${cellId}_M${index}`;
                    const x = j * (CELL_WIDTH + CELL_MARGIN_X) + CELL_OFFSET_X + CELL_WIDTH / 2 + matrixConfig.pos.x - MATRIX_WIDTH / 2;
                    const y = i * (CELL_HEIGHT + CELL_MARGIN_Y) + CELL_OFFSET_Y + CELL_HEIGHT / 2 - MATRIX_HEIGHT / 2 + matrixConfig.pos.y;
                    const matrix = new SwitchMatrix(matrixId, { x, y });
                    matrix.nets = matrixConfig.nets.map((net) => ({
                        ...net,
                        id: matrixId + "." + net.id,
                        points: net.points.map((p) => ({ ...p })),
                    }));

                    matrices.push(matrix);
                    // console.log(matrix);
                });
            }

            const ioConfig = getConfig("io", cellId);

            if (ioConfig) {
                ioConfig.forEach((ioBankConfig, index) => {
                    const ioBankId = `${cellId}_IO${index}`;
                    const x =
                        j * (CELL_WIDTH + CELL_MARGIN_X) +
                        CELL_OFFSET_X +
                        CELL_WIDTH / 2 +
                        ioBankConfig.pos.x -
                        ioBankConfig.size.width / 2;
                    const y =
                        i * (CELL_HEIGHT + CELL_MARGIN_Y) +
                        CELL_OFFSET_Y +
                        CELL_HEIGHT / 2 -
                        ioBankConfig.size.height / 2 +
                        ioBankConfig.pos.y;
                    const ioBank = new IOBank(ioBankId, { x, y }, { width: ioBankConfig.size.width, height: ioBankConfig.size.height });
                    ioBank.nets = ioBankConfig.nets.map((net) => ({
                        ...net,
                        id: ioBankId + "." + net.id,
                        points: net.points.map((p) => ({ ...p })),
                    }));
                    if (ioBankConfig.pads) {
                        ioBank.pad = new IOPad(ioBankConfig.pads[0].pos, ioBankConfig.pads[0].size);
                    }

                    ioBanks.push(ioBank);
                });
            }
        }
    }

    for (let i = 0; i < ROWS; i++) {
        for (let j = 0; j < COLS; j++) {
            // Cell Ids are letters, one for row, one for col, so top left is AA
            const cellId = String.fromCharCode(65 + i) + String.fromCharCode(65 + j);
            let config = getConfig("logic_cell", cellId);

            if (!config) {
                config = { nets: [], pips: [] };
            }

            const x = j * (CELL_WIDTH + CELL_MARGIN_X) + CELL_OFFSET_X;
            const y = i * (CELL_HEIGHT + CELL_MARGIN_Y) + CELL_OFFSET_Y;

            for (const pip of config.pips) {
                let source = pip.source;
                let destination = pip.destination;

                if (!source.startsWith("net")) {
                    if (source.startsWith("global")) {
                        if (source.length !== 6) {
                            let address = source.split("_")[1];
                            let isHorizontal = address.startsWith("H");
                            let dir = address[1];

                            if (dir !== "U" && dir !== "D" && dir !== "L" && dir !== "R") {
                                
                            } else if (!isHorizontal) {
                                let busIdx = j + (dir === "R" ? 1 : 0);
                                source = `global_V${busIdx}.${source.split(".")[1]}`;
                            } else {
                                let busIdx = i + (dir === "U" ? 0 : 1);
                                source = `global_H${busIdx}.${source.split(".")[1]}`;
                            }
                        }
                    } else {
                        let direction, device;

                        if (source.split(".")[0].length <= 2) {
                            direction = source.split(".")[0];
                            device = "";
                        } else {
                            direction = source.split("_")[0];
                            device = "_" + source.split("_")[1].split(".")[0];
                        }

                        let cellIndex = 0;

                        let i_offset = direction.includes("N") ? -1 : direction.includes("S") ? 1 : 0;
                        let j_offset = direction.includes("W") ? -1 : direction.includes("E") ? 1 : 0;

                        if (i + i_offset >= 0 && i + i_offset < ROWS && j + j_offset >= 0 && j + j_offset < COLS) {
                            cellIndex = (i + i_offset) * COLS + (j + j_offset);
                        } else {
                            console.warn(`Pip ${pip.id} has invalid source ${source}`);
                            continue;
                        }

                        source = `${cells[cellIndex].id}${device}.${source.split(".")[1]}`;
                    }
                } else {
                    source = `${cells[i * COLS + j].id}.${source}`;
                }

                if (!destination.startsWith("net")) {
                    if (destination.startsWith("global")) {
                        if (destination.length !== 6) {
                            let address = destination.split("_")[1];
                            let isHorizontal = address.startsWith("H");
                            let dir = address[1];

                            if (dir !== "U" && dir !== "D" && dir !== "L" && dir !== "R") {
                                
                            } else if (!isHorizontal) {
                                let busIdx = j + (dir === "R" ? 1 : 0);
                                destination = `global_V${busIdx}.${destination.split(".")[1]}`;
                            } else {
                                let busIdx = i + (dir === "U" ? 0 : 1);
                                destination = `global_H${busIdx}.${destination.split(".")[1]}`;
                            }
                        }
                    } else {
                        let direction, device;
                        if (destination.split(".")[0].length <= 2) {
                            direction = destination.split(".")[0];
                            device = "";
                        } else {
                            direction = destination.split("_")[0];
                            device = "_" + destination.split("_")[1].split(".")[0];
                        }

                        let cellIndex = 0;

                        let i_offset = direction.includes("N") ? -1 : direction.includes("S") ? 1 : 0;
                        let j_offset = direction.includes("W") ? -1 : direction.includes("E") ? 1 : 0;

                        if (i + i_offset >= 0 && i + i_offset < ROWS && j + j_offset >= 0 && j + j_offset < COLS) {
                            cellIndex = (i + i_offset) * COLS + (j + j_offset);
                        } else {
                            console.warn(`Pip ${pip.id} has invalid destination ${destination}`);
                            continue;
                        }

                        destination = `${cells[cellIndex].id}${device}.${destination.split(".")[1]}`;
                        // console.log(destination);
                    }
                } else {
                    destination = `${cells[i * COLS + j].id}.${destination}`;
                }

                // console.log(`Adding pip ${pip.id} from ${source} to ${destination}`);
                pips.push({
                    id: pip.id,
                    source,
                    destination,
                    enabled: pip.enabled,
                    pos: { x: x + pip.pos.x, y: y + pip.pos.y },
                    bidirectional: pip.bidirectional,
                });
            }
        }
    }

    // Populate Switching Matrices nets
    for (let i = 0; i < ROWS; i++) {
        for (let j = 0; j < COLS; j++) {
            const cellId = String.fromCharCode(65 + i) + String.fromCharCode(65 + j);
            const switchMatrixConfig = getConfig("switch_matrix", cellId);

            if (switchMatrixConfig) {
                switchMatrixConfig.forEach((matrixConfig, index) => {
                    const matrixId = `${cellId}_M${index}`;
                    const x = j * (CELL_WIDTH + CELL_MARGIN_X) + CELL_OFFSET_X + CELL_WIDTH / 2 + matrixConfig.pos.x - MATRIX_WIDTH / 2;
                    const y = i * (CELL_HEIGHT + CELL_MARGIN_Y) + CELL_OFFSET_Y + CELL_HEIGHT / 2 - MATRIX_HEIGHT / 2 + matrixConfig.pos.y;

                    const matrix = matrices.find((m) => m.id === matrixId);
                    // Figure out the net ids for the ones not managed by this matrix
                    const left_code = cellId.charCodeAt(0);
                    const right_code = cellId.charCodeAt(1);

                    let left_cell_id = j > 0 ? String.fromCharCode(left_code) + String.fromCharCode(right_code - 1) : null;
                    let bottom_cell_id = i < ROWS - 1 ? String.fromCharCode(left_code + 1) + String.fromCharCode(right_code) : null;

                    let bottom_index = index;
                    let left_index = index;

                    if (!left_cell_id && bottom_cell_id) {
                        // If the switch cannot find a cell to the left, it must be on the left edge, so it should connect to switch M2 and M3 of the current cell instead.
                        if (index < 2) {
                            left_cell_id = cellId;
                            left_index = index + 2;
                        }
                        // console.warn(`Matrix ${matrixId} has invalid neighboring cells on the left ${left_cell_id}`);
                    }

                    if (!left_cell_id) {
                        console.warn(`Matrix ${matrixId} has invalid neighboring cell on the left`);
                    } else {
                        matrix.nets[6] = localGetNet(`${left_cell_id}_M${left_index}.net_3`) || null;
                        matrix.nets[7] = localGetNet(`${left_cell_id}_M${left_index}.net_2`) || null;
                    }

                    if (!bottom_cell_id) {
                        console.warn(`Matrix ${matrixId} has invalid neighboring cell on the bottom`);
                    } else {
                        matrix.nets[4] = localGetNet(`${bottom_cell_id}_M${bottom_index}.net_1`) || null;
                        matrix.nets[5] = localGetNet(`${bottom_cell_id}_M${bottom_index}.net_0`) || null;
                    }
                });
            }
        }
    }
    return { logicCells: cells, switchMatrices: matrices, pips, ioBanks, busNets };
};
