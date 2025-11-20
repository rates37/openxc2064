import { createContext } from 'react';
import React from 'react';
import { LogicElement } from '../models/LogicElement';
import { XC2064 } from '../constants';

export type SimulatorContextType = {
    // Objects / Data
    logicElements: LogicElement[][];

    // Functions
    setLogicElements: (logicElements: LogicElement[][]) => void;
};



export const SimulatorContext = createContext<SimulatorContextType>({} as SimulatorContextType);







export const SimulatorContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [logicElements, setLogicElements] = React.useState<LogicElement[][]>(initialiseLogicElements());


    const contextValue: SimulatorContextType = {
        logicElements: logicElements,
        setLogicElements: setLogicElements,
    };

    return (
        <SimulatorContext.Provider value={contextValue}>
            {children}
        </SimulatorContext.Provider>
    );
};


const initialiseLogicElements = (): LogicElement[][] => {
    const context: SimulatorContextType = React.useContext(SimulatorContext);

    // Initiliase the context of the application
    const clbs: LogicElement[][] = [];

    for (let y = 0; y < XC2064.HEIGHT; y++) {
        const row: LogicElement[] = [];
        for (let x = 0; x < XC2064.WIDTH; x++) {
            // Set ID to AA, AB ... BA, BB etc
            const id = `${String.fromCharCode(65 + y)}${String.fromCharCode(65 + x)}`;
            const clb = new LogicElement();
            clb.id = id;
            row.push(clb);
        }
        clbs.push(row);
    }

    return clbs;
}