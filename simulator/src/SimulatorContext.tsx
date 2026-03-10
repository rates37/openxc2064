import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { LogicCell } from "./models/LogicCell";
import { SwitchMatrix } from "./models/SwitchMatrix";
import { Net, Pip } from "./types";
import getConfig from './configs/configs';
import { CELL_WIDTH, CELL_HEIGHT, CELL_MARGIN_X, CELL_MARGIN_Y, CELL_OFFSET_X, CELL_OFFSET_Y, MATRIX_WIDTH, MATRIX_HEIGHT } from './configs/Routing';

// =============================================================================
// 1. Define the shape of your context value here.
//    Add new state fields, lists, and functions as needed.
// =============================================================================
interface SimulatorContextValue {
  // -- Example primitive state --
  isRunning: boolean;

  // -- Example list --
  // Add arrays/lists here. For example:
  //   items: MyItem[];
  logicCells: LogicCell[];
  switchMatrices: SwitchMatrix[];
  pips: Pip[];

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

  const toggleGrid = useCallback(() => setShowGrid(prev => !prev), []);


  // -- Lists --
  // Manage arrays via useState. Example:
  //   const [items, setItems] = useState<MyItem[]>([]);
  const [logicCells, setLogicCells] = useState<LogicCell[]>([]);
  const [switchMatrices, setSwitchMatrices] = useState<SwitchMatrix[]>([]);
  const [pips, setPips] = useState<Pip[]>([]);

  const togglePip = useCallback((index: number) => {
    setPips(prev => prev.map((pip, i) => i === index ? { ...pip, enabled: !pip.enabled } : pip));
  }, []);

  const [selectedMatrix, setSelectedMatrix] = useState<SwitchMatrix | null>(null);
  const [selectedCell, setSelectedCell] = useState<LogicCell | null>(null);

  const selectCell = useCallback((cell: LogicCell | null) => {
    setSelectedCell(cell);
  }, []);

  const selectMatrix = useCallback((matrix: SwitchMatrix | null) => {
    setSelectedMatrix(matrix);
  }, []);

  const toggleConnection = useCallback((matrixIndex: number, row: number, col: number) => {
    const matrix = switchMatrices[matrixIndex];
    if (!matrix) return;
    if (!matrix.possibleConnections[row][col]) return;
    matrix.connections[row][col] = matrix.connections[row][col] ? 0 : 1;
    setSwitchMatrices([...switchMatrices]);
    setSelectedMatrix(matrix);
  }, [switchMatrices]);

  const saveMatrixConnections = useCallback((matrixIndex: number, connections: number[][]) => {
    const matrix = switchMatrices[matrixIndex];
    if (!matrix) return;
    matrix.connections = connections;
    setSwitchMatrices([...switchMatrices]);
  }, [switchMatrices]);

  // -- Functions --
  // Wrap in useCallback to keep stable references and avoid unnecessary
  // re-renders in consumers.

  // getNet: a helper function to resolve a global net ID to the actual Net object, in either a logic cell, or a global line.
  const getNet = useCallback((globalNetId: string): Net | undefined => {
    const [location, id] = globalNetId.split(".");

    const allCellIds = logicCells.map(cell => cell.id);

    if (allCellIds.includes(location[0] + location[1]) && location.length === 2) {
      const cell = logicCells.find(cell => cell.id === location);
      return cell?.nets.find(net => net.id === id);
    }

    // if first char is M
    if (allCellIds.includes(location[0] + location[1]) && location.length === 5 && location[3] === "M") {
      const matrix = switchMatrices.find(matrix => matrix.id === location);
      return matrix?.nets.find(net => net && net.id === globalNetId);
    }

    console.log(`Net ${globalNetId} not found in any cell.`, allCellIds.includes(location[0] + location[1]), location[0] + location[1]);

    return undefined;
  }, [logicCells]);


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
      return snap;
    };

    let steps = 0;
    let settled = false;

    while (!settled && steps < MAX_ITERATIONS) {
      const before = snapshotNets();

      logicCells.forEach(cell => {
        cell.simulate();
      });

      switchMatrices.forEach(matrix => {
        matrix.simulate();
      });

      pips.forEach(pip => {
        if (pip.enabled) {
          const sourceNet = getNet(pip.source);
          const destinationNet = getNet(pip.destination);

          if (sourceNet && destinationNet) {
            // console.log(`Pip ${pip.id} transferring value from ${pip.source} (${sourceNet.value}) to ${pip.destination} (was ${destinationNet.value})`);
            destinationNet.value = sourceNet.value;
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
    setLogicCells([...logicCells]);
    setSwitchMatrices([...switchMatrices]);

    const endTime = performance.now();
    console.log(`Simulation settled after ${steps} step(s) in ${(endTime - startTime).toFixed(2)} ms`);
    if (steps >= MAX_ITERATIONS) {
      console.warn(`Simulation did not settle within ${MAX_ITERATIONS} iterations`);
    }
    setIsRunning(false);
  }, [logicCells, switchMatrices, pips, getNet]);

  useEffect(() => {
    const { logicCells, switchMatrices, pips } = initialiseSimulation();
    setLogicCells(logicCells);
    setSwitchMatrices(switchMatrices);
    setPips(pips);

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

  const value: SimulatorContextValue = {
    isRunning,
    logicCells,
    simulate,
    showGrid,
    toggleGrid,
    getNet,
    switchMatrices,
    pips,
    togglePip,
    selectedMatrix,
    selectMatrix,
    saveMatrixConnections,
    selectedCell,
    selectCell,
    setLogicCells
  };

  return (
    <SimulatorContext.Provider value={value}>
      {children}
    </SimulatorContext.Provider>
  );
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


const ROWS = 8;
const COLS = 8;

const initialiseSimulation = (): { logicCells: LogicCell[], switchMatrices: SwitchMatrix[], pips: Pip[] } => {
  const cells: LogicCell[] = [];
  const matrices: SwitchMatrix[] = [];
  const pips: Pip[] = [];

  // Local resolver that operates on the arrays being built, rather than
  // the (empty) React state that exists at mount time.
  const localGetNet = (globalNetId: string): Net | undefined => {
    const [location, id] = globalNetId.split(".");

    if (location.length === 2) {
      const cell = cells.find(c => c.id === location);
      return cell?.nets.find(net => net.id === id);
    }

    if (location.length === 5 && location[3] === "M") {
      const matrix = matrices.find(m => m.id === location);
      return matrix?.nets.find(net => net && net.id === globalNetId);
    }

    return undefined;
  };

  for (let i = 0; i < ROWS; i++) {
    for (let j = 0; j < COLS; j++) {
      // Cell Ids are letters, one for row, one for col, so top left is AA
      let config = getConfig("logic_cell", i * COLS + j);

      if (!config) {
        config = { "nets": [], "pips": [] };
      }

      const cellId = String.fromCharCode(65 + i) + String.fromCharCode(65 + j);

      const x = j * (CELL_WIDTH + CELL_MARGIN_X) + CELL_OFFSET_X;
      const y = i * (CELL_HEIGHT + CELL_MARGIN_Y) + CELL_OFFSET_Y;


      cells.push(new LogicCell(cellId, { ...config, pos: { x, y } }));

      const switchMatrixConfig = getConfig("switch_matrix", i * COLS + j);

      if (switchMatrixConfig) {
        switchMatrixConfig.forEach((matrixConfig, index) => {
          const matrixId = `${cellId}_M${index}`;
          const x = j * (CELL_WIDTH + CELL_MARGIN_X) + CELL_OFFSET_X + CELL_WIDTH / 2 + matrixConfig.pos.x - MATRIX_WIDTH / 2;
          const y = i * (CELL_HEIGHT + CELL_MARGIN_Y) + CELL_OFFSET_Y + CELL_HEIGHT / 2 - MATRIX_HEIGHT / 2 + matrixConfig.pos.y;
          const matrix = new SwitchMatrix(matrixId, { x, y });
          matrix.nets = matrixConfig.nets.map(net => ({ ...net, id: matrixId + "." + net.id, points: net.points.map(p => ({ ...p })) }));

          matrices.push(matrix);
          // console.log(matrix);
        });
      }
    }
  }

  for (let i = 0; i < ROWS; i++) {
    for (let j = 0; j < COLS; j++) {
      // Cell Ids are letters, one for row, one for col, so top left is AA
      let config = getConfig("logic_cell", i * COLS + j);

      if (!config) {
        config = { "nets": [], "pips": [] };
      }

      const x = j * (CELL_WIDTH + CELL_MARGIN_X) + CELL_OFFSET_X;
      const y = i * (CELL_HEIGHT + CELL_MARGIN_Y) + CELL_OFFSET_Y;

      for (const pip of config.pips) {
        let source = pip.source;
        let destination = pip.destination;

        if (!source.startsWith("net")) {
          let direction, matrixIndex;

          if (source.includes("_M")) {
            direction = source.split("_")[0];
            matrixIndex = parseInt(source.split("_")[1].substring(1));
          } else {
            direction = source.split(".")[0];
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

          if (matrixIndex !== undefined) {
            source = `${cells[cellIndex].id}_M${matrixIndex}.${source.split(".")[1]}`;
          } else {
            source = `${cells[cellIndex].id}.${source.split(".")[1]}`;
          }
        } else {
          source = `${cells[i * COLS + j].id}.${source}`;
        }

        if (!destination.startsWith("net")) {
          let direction, matrixIndex;
          if (destination.includes("_M")) {
            direction = destination.split("_")[0];
            matrixIndex = parseInt(destination.split("_")[1].substring(1));
          } else {
            direction = destination.split(".")[0];
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

          if (matrixIndex !== undefined) {
            destination = `${cells[cellIndex].id}_M${matrixIndex}.${destination.split(".")[1]}`;
          } else {
            destination = `${cells[cellIndex].id}.${destination.split(".")[1]}`;
          }
        } else {
          destination = `${cells[i * COLS + j].id}.${destination}`;
        }

        // console.log(`Adding pip ${pip.id} from ${source} to ${destination}`);
        pips.push({ id: pip.id, source, destination, enabled: pip.enabled, pos: { x: x + pip.pos.x, y: y + pip.pos.y }, bidirectional: false });
      }
    }
  }


  // Populate Switching Matrices nets
  for (let i = 0; i < ROWS; i++) {
    for (let j = 0; j < COLS; j++) {

      const switchMatrixConfig = getConfig("switch_matrix", i * COLS + j);
      const cellId = String.fromCharCode(65 + i) + String.fromCharCode(65 + j);

      if (switchMatrixConfig) {
        switchMatrixConfig.forEach((matrixConfig, index) => {
          const matrixId = `${cellId}_M${index}`;
          const x = j * (CELL_WIDTH + CELL_MARGIN_X) + CELL_OFFSET_X + CELL_WIDTH / 2 + matrixConfig.pos.x - MATRIX_WIDTH / 2;
          const y = i * (CELL_HEIGHT + CELL_MARGIN_Y) + CELL_OFFSET_Y + CELL_HEIGHT / 2 - MATRIX_HEIGHT / 2 + matrixConfig.pos.y;

          const matrix = matrices.find(m => m.id === matrixId);
          // Figure out the net ids for the ones not managed by this matrix
          const left_code = cellId.charCodeAt(0);
          const right_code = cellId.charCodeAt(1);

          const left_cell_id = j > 0 ? String.fromCharCode(left_code) + String.fromCharCode(right_code - 1) : null;
          const bottom_cell_id = i < ROWS - 1 ? String.fromCharCode(left_code + 1) + String.fromCharCode(right_code) : null;

          if (!left_cell_id || !bottom_cell_id) {
            console.warn(`Matrix ${matrixId} has invalid neighboring cells: left ${left_cell_id}, bottom ${bottom_cell_id}`);
          } else {
            matrix.nets[4] = localGetNet(`${bottom_cell_id}_M${index}.net_1`) || null;
            matrix.nets[5] = localGetNet(`${bottom_cell_id}_M${index}.net_0`) || null;
            matrix.nets[6] = localGetNet(`${left_cell_id}_M${index}.net_3`) || null;
            matrix.nets[7] = localGetNet(`${left_cell_id}_M${index}.net_2`) || null;
          }
        });
      }
    }
  }
  return { logicCells: cells, switchMatrices: matrices, pips }; // Placeholder for switch matrices
};