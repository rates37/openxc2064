import React from 'react';
import { LogicElement } from '../models/LogicElement';
import "../styles/LogicArray.css";
import { useEffect } from 'react';
import { NodeComponent } from './NodeComponent';
import { XC2064 } from '../constants';
import { SwitchComponent } from './SwitchComponent';


type LogicElementComponentProps = {
    logicElement: LogicElement;
    x: number;
    y: number;
    onClick?: (element: LogicElement) => void;
};

export const LogicElementComponent: React.FC<LogicElementComponentProps> = ({ logicElement, x, y, onClick }) => {
    const [nodes, setNodes] = React.useState<React.JSX.Element | null>(null);
    const [switches, setSwitches] = React.useState<React.JSX.Element | null>(null);

    const clb = logicElement;

    // TODO: Handle logic element click to open modal
    const handleClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (onClick) {
            onClick(logicElement);
        }
    };


    useEffect(() => {
        const allNodes: {x: number, y: number}[] = [];
        const allSwitches: {x: number, y: number}[] = [];

        const idFirstChar = clb.id.charAt(0);
        const idSecondChar = clb.id.charAt(1);
        // A Nodes
        if (idFirstChar === 'A') {
            allNodes.push(...XC2064.A_EDGE_NODES as {x: number, y: number}[]);
        } else {
            allNodes.push(...XC2064.A_NODES as {x: number, y: number}[]);
        }

        // B Nodes
        if (idSecondChar === 'A') {
            allNodes.push(...XC2064.B_EDGE_NODES as {x: number, y: number}[]);
        } else {
            allNodes.push(...XC2064.B_NODES as {x: number, y: number}[]);
        }
        
        // C Nodes
        if (idSecondChar === 'A') {
            allNodes.push(...XC2064.C_EDGE_NODES as {x: number, y: number}[]);
        } else {
            allNodes.push(...XC2064.C_NODES as {x: number, y: number}[]);
        }

        // D Nodes
        if (idFirstChar === 'H') {
            allNodes.push(...XC2064.D_EDGE_NODES as {x: number, y: number}[]);
        } else {
            allNodes.push(...XC2064.D_NODES as {x: number, y: number}[]);
        }

        // K Nodes
        if (idSecondChar === 'A') {
            allNodes.push(...XC2064.K_EDGE_NODES as {x: number, y: number}[]);
        } else {
            allNodes.push(...XC2064.K_NODES as {x: number, y: number}[]);
        }

        // X Nodes
        if (idSecondChar === 'H') {
            allNodes.push(...XC2064.X_EDGE_NODES as {x: number, y: number}[]);
        } else {
            allNodes.push(...XC2064.X_NODES as {x: number, y: number}[]);
        }

        // Y Nodes
        if (idSecondChar === 'H') {
            allNodes.push(...XC2064.Y_EDGE_NODES as {x: number, y: number}[]);
        } else {
            allNodes.push(...XC2064.Y_NODES as {x: number, y: number}[]);
        }

        // Switches
        switch (idFirstChar) {
            case 'A':
                if (idSecondChar != 'A') {
                    allSwitches.push(...XC2064.SWITCHES_TOP as {x: number, y: number}[]);
                }
                break;
            case 'H':
                if (idSecondChar !== 'A') {
                    allSwitches.push(...XC2064.SWITCHES_BOTTOM as {x: number, y: number}[]);
                    allSwitches.push(...XC2064.SWITCHES as {x: number, y: number}[]);
                } else {
                    allSwitches.push(...XC2064.SWITCHES_LEFT as {x: number, y: number}[]);
                }

                if (idSecondChar === 'H') {
                    allSwitches.push(...XC2064.SWITCHES_RIGHT as {x: number, y: number}[]);
                }
                break;
            default:
                switch (idSecondChar) {
                    case 'A':
                        allSwitches.push(...XC2064.SWITCHES_LEFT as {x: number, y: number}[]);
                        break;
                    case 'H':
                        allSwitches.push(...XC2064.SWITCHES_RIGHT as {x: number, y: number}[]);
                        allSwitches.push(...XC2064.SWITCHES as {x: number, y: number}[]);

                        break;
                    default:
                        allSwitches.push(...XC2064.SWITCHES as {x: number, y: number}[]);
                        break;
                }
                break;
        }

        setNodes(<>{allNodes.map((node, index) => <NodeComponent key={index + "-"} x={x + node.x} y={y + node.y} />)}</>);
        setSwitches(<>{allSwitches.map((sw, index) => <SwitchComponent key={index + "s"} x={x + sw.x} y={y + sw.y} />)}</>);
    }, []);


    return <>
        <div className="LogicElement" style={{ left: x, top: y }} onClick={handleClick}>{clb.id}</div>
        {nodes}
        {switches}
    </>
}