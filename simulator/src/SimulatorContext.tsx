import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { LogicCell } from "./models/LogicCell";

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

  // -- Functions --
  // Add callable functions here. For example:
  //   addItem: (item: MyItem) => void;
  //   removeItem: (id: string) => void;
  simulate: () => void;

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

  // -- Lists --
  // Manage arrays via useState. Example:
  //   const [items, setItems] = useState<MyItem[]>([]);
  const [logicCells, setLogicCells] = useState<LogicCell[]>([]);

  // -- Functions --
  // Wrap in useCallback to keep stable references and avoid unnecessary
  // re-renders in consumers.

  // simulate: your main entry-point for running a simulation step/cycle.
  const simulate = useCallback(() => {  
    setIsRunning(true);
    // TODO: put simulation logic here
    
    setIsRunning(false);
  }, []);

  useEffect(() => {
    const cells = initialiseSimulation();
    setLogicCells(cells);
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

const initialiseSimulation = (): LogicCell[] => {
    const cells: LogicCell[] = [];

    for (let i = 0; i < ROWS; i++) {
        for (let j = 0; j < COLS; j++) {
            // Cell Ids are letters, one for row, one for col, so top left is AA
            const cellId = String.fromCharCode(65 + i) + String.fromCharCode(65 + j);
            cells.push(new LogicCell(cellId));
        }
    }

    return cells;
};