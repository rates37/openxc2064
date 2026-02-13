import { createContext, MutableRefObject } from 'react';
import React from 'react';
import { LogicElement } from '../models/LogicElement';
import { XC2064 } from '../constants';
import { SwitchMatrix } from '../models/SwitchMatrix';
import { glob } from 'fs';

export type SimulatorContextType = {
    // Objects / Data
    logicElements: LogicElement[][];
    switchMatrices: SwitchMatrix[];

    // Display Globals
    canvas: HTMLCanvasElement | null;

    // Functions
    setLogicElements: (logicElements: LogicElement[][]) => void;
    updateLogicElement: (element: LogicElement) => void;
    setSwitchMatrices: (switchMatrices: SwitchMatrix[]) => void;
    updateSwitchMatrix: (matrix: SwitchMatrix) => void;

    setCanvas: (canvas: HTMLCanvasElement | null) => void;

    // Simulation
    simulate: () => void;

    // Nets
    globalNets: { [key: string]: (0 | 1) };
    // setGlobalNets: (nets: { [key: string]: (0 | 1) }) => void;
    setNet: (netID: string, value: 0 | 1) => void;
    getNet: (netID: string) => 0 | 1 | undefined;

    boundNets: {input: string, output: string}[];
    setBoundNets: (boundNets: {input: string, output: string}[]) => void;
    bindNets: (input: string, output: string) => void;
    unbindNets: (input: string, output: string) => void;
    resetNets: string[];


};

export const SimulatorContext = createContext<SimulatorContextType>({} as SimulatorContextType);

export const SimulatorContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [logicElements, setLogicElements] = React.useState<LogicElement[][]>(initialiseLogicElements());
    const [switchMatrices, setSwitchMatrices] = React.useState<SwitchMatrix[]>([]);
    const [canvas, setCanvas] = React.useState<HTMLCanvasElement | null>(null);
    const [globalNets, setGlobalNets] = React.useState<{ [key: string]: (0 | 1) }>({});
    const globalNetsRef = React.useRef<{ [key: string]: (0 | 1) }>({});
    const [boundNets, setBoundNets] = React.useState<{input: string, output: string}[]>([]);
    const [resetNets, setResetNets] = React.useState<string[]>([]);

    const contextValue: SimulatorContextType = {
        logicElements: logicElements,
        switchMatrices: switchMatrices,
        setLogicElements: setLogicElements,
        updateLogicElement: (element: LogicElement) => updateLogicElement(element, contextValue),
        setSwitchMatrices: setSwitchMatrices,
        updateSwitchMatrix: (matrix: SwitchMatrix) => updateSwitchMatrix(matrix, contextValue),
        canvas: canvas,
        setCanvas: setCanvas,
        globalNets: globalNets,
        // setGlobalNets: setGlobalNets,
        setNet: (netID: string, value: 0 | 1) => setNet(netID, value, globalNetsRef, setGlobalNets),
        getNet: (netID: string) => getNet(netID, globalNetsRef),
        simulate: () => simulate(contextValue, globalNetsRef, setResetNets),
        boundNets: boundNets,
        setBoundNets: setBoundNets,
        bindNets: (input: string, output: string) => {
            console.log("Binding nets", input, output);
            setBoundNets([...boundNets, {input: input, output: output}]);
        },
        unbindNets: (input: string, output: string) => {
            setResetNets(prev => [...prev, output]);
            setBoundNets(boundNets.filter(b => b.input !== input || b.output !== output));
        },
        resetNets: resetNets,
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

            const OFFSET = 400;

            const elX = x * 190 + OFFSET;
            const elY = y * 190 + OFFSET;

            clb.x = elX;
            clb.y = elY;


            row.push(clb);
        }
        clbs.push(row);
    }

    return clbs;
}

const updateLogicElement = (element: LogicElement, context: SimulatorContextType) => {
    const elementRow = context.logicElements.findIndex(row => row.some(el => el.id === element.id));
    if (elementRow === -1) return;

    const elementToUpdate = context.logicElements[elementRow].findIndex(el => el.id === element.id);
    if (elementToUpdate === -1) return;

    context.logicElements[elementRow][elementToUpdate] = element;
    context.setLogicElements([...context.logicElements]);
}

const updateSwitchMatrix = (matrix: SwitchMatrix, context: SimulatorContextType) => {
    const matrixIndex = context.switchMatrices.findIndex(m => m.id === matrix.id);
    if (matrixIndex === -1) {
        context.switchMatrices.push(matrix);
    } else {
        context.switchMatrices[matrixIndex] = matrix;
    }

    context.setSwitchMatrices([...context.switchMatrices]);
}

const setNet = (netID: string, value: 0 | 1, globalNetsRef: MutableRefObject<{ [key: string]: (0 | 1) }>, setGlobalNets: React.Dispatch<React.SetStateAction<{ [key: string]: (0 | 1) }>>) => {
    // console.log(`Setting net ${netID} to ${value}`);
    // console.log("Previous nets:", context.globalNets);
    globalNetsRef.current[netID] = value;
    setGlobalNets(prev => {
        const newNets = { ...prev, [netID]: value };
        // console.log("Updated nets:", newNets);
        return newNets;
    });
}

const getNet = (netID: string, globalNetsRef: MutableRefObject<{ [key: string]: (0 | 1) }>) => {
    return globalNetsRef.current[netID];
}


const simulate = (context: SimulatorContextType, globalNetsRef: MutableRefObject<{ [key: string]: (0 | 1) }>, setResetNets: (nets: string[]) => void) => {
    // console.log(context.boundNets);
    // console.log(context.resetNets);
    for (const netID of context.resetNets) {
        context.setNet(netID, 0);
    }
    setResetNets([]);

    let prevLEs, prevNets;
    do {
        // prevLEs = {...context.logicElements};
        prevNets = {...globalNetsRef.current};

        // console.log(prevNets["AA:Y"], context.getNet("AA:Y"));
        
        context.logicElements.forEach(row => {
            row.forEach(element => {
                element.simulate(context);
            });
        });
        
        context.switchMatrices.forEach(matrix => {
            matrix.simulate(context);
        });
        
        context.boundNets.forEach(boundNet => {
            const inputValue = globalNetsRef.current[boundNet.input];
            context.setNet(boundNet.output, inputValue);
        });
        
        // console.log("Simulation step complete.");
        // console.log(prevNets["AA:Y"], context.getNet("AA:Y"));
        // console.log("Global Nets:", JSON.stringify(globalNetsRef.current) !== JSON.stringify(prevNets) ? globalNetsRef.current : "No change");
        // console.log("Logic Elements:", JSON.stringify(context.logicElements) !== JSON.stringify(prevLEs) ? context.logicElements : "No change");
        // console.log("Logic Elements:", JSON.stringify(context.logicElements), JSON.stringify(prevLEs));
        // console.log("Bound Nets:", JSON.stringify(context.boundNets) !== JSON.stringify(prevBound) ? context.boundNets : "No change");

    } while (JSON.stringify(globalNetsRef.current) !== JSON.stringify(prevNets));

}
