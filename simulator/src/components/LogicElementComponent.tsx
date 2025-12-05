import React from 'react';
import { LogicElement } from '../models/LogicElement';
import "../styles/LogicArray.css";
import { useEffect } from 'react';
import { NodeComponent } from './NodeComponent';
import { XC2064 } from '../constants';
import { SwitchComponent } from './SwitchComponent';
import { BusComponent } from './BusComponent';
import { NodeBusComponent } from './NodeBusComponent';
import { SimulatorContext } from '../context/SimulatorContext';

type LogicElementComponentProps = {
    i: number;
    j: number;
    x: number;
    y: number;
    onClick?: (element: LogicElement) => void;
};

export const LogicElementComponent: React.FC<LogicElementComponentProps> = ({ i, j, x, y, onClick }) => {
    const [nodes, setNodes] = React.useState<React.JSX.Element | null>(null);
    const [switches, setSwitches] = React.useState<React.JSX.Element | null>(null);
    const [busses, setBusses] = React.useState<React.JSX.Element | null>(null);

    const context = React.useContext(SimulatorContext);
    const logicElement: LogicElement = context.logicElements[i][j];

    // TODO: Handle logic element click to open modal
    const handleClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (onClick) {
            onClick(logicElement);
        }
    };

    const generateIOBusses = (allNodes: { x: number, y: number, node: string }[]) => {
        // Auto generate left hand lines
        const nodeNamesLeft = ["B", "C", "K"];
        nodeNamesLeft.forEach(nodeName => {
            const leftNodes = allNodes.filter(n => n.node === nodeName);
            if (leftNodes.length > 0) {
                const busXStart = leftNodes.reduce((min, n) => n.x < min ? n.x : min, leftNodes[0].x) + x;
                const busXEnd = x;
                const busY = leftNodes[0].y + y + 3;

                setBusses(prev => <>
                    {prev}
                    <NodeBusComponent x1={busXStart} y1={busY} x2={busXEnd} y2={busY} nodeID={nodeName} nets={logicElement.outputs} />
                </>);
            }
        });


        // Auto generate top lines
        const nodeNamesTop = ["A"];
        nodeNamesTop.forEach(nodeName => {
            const topNodes = allNodes.filter(n => n.node === nodeName);
            if (topNodes.length > 0) {
                const busYStart = topNodes.reduce((min, n) => n.y < min ? n.y : min, topNodes[0].y) + y;
                const busYEnd = y;
                const busX = topNodes[0].x + x + 2;
                setBusses(prev => <>
                    {prev}
                    <NodeBusComponent x1={busX} y1={busYStart} x2={busX} y2={busYEnd} nodeID={nodeName} nets={logicElement.outputs} />
                </>);
            }
        });

        // Auto generate bottom lines
        const nodeNamesBottom = ["D"];
        nodeNamesBottom.forEach(nodeName => {
            const bottomNodes = allNodes.filter(n => n.node === nodeName);
            if (bottomNodes.length > 0) {
                const busYStart = bottomNodes.reduce((max, n) => n.y > max ? n.y : max, bottomNodes[0].y) + y + 5;
                const busYEnd = y + 80;
                const busX = bottomNodes[0].x + x + 2;

                setBusses(prev => <>
                    {prev}
                    <NodeBusComponent x1={busX} y1={busYEnd} x2={busX} y2={busYStart} nodeID={nodeName} nets={logicElement.outputs} />
                </>);
            }
        });

        // Auto generate right hand lines
        const nodeNamesRight = ["X", "Y"];
        nodeNamesRight.forEach(nodeName => {
            const rightNodes = allNodes.filter(n => n.node === nodeName);
            if (rightNodes.length > 0) {
                const busXStart = rightNodes.reduce((max, n) => n.x > max ? n.x : max, rightNodes[0].x) + x + 5;
                const busXEnd = x + 50;
                const busY = rightNodes[0].y + y + 3;

                setBusses(prev => <>
                    {prev}
                    <NodeBusComponent x1={busXEnd} y1={busY} x2={busXStart} y2={busY} nodeID={nodeName} nets={logicElement.outputs} />
                </>);
            }
        });


    }

    useEffect(() => {
        const allNodes: { x: number, y: number, node: string }[] = [];
        const allSwitches: { x: number, y: number }[] = [];

        const idFirstChar = logicElement.id.charAt(0);
        const idSecondChar = logicElement.id.charAt(1);
        // A Nodes
        if (idFirstChar === 'A') {
            allNodes.push(...XC2064.A_EDGE_NODES as { x: number, y: number, node: string }[]);
        } else {
            allNodes.push(...XC2064.A_NODES as { x: number, y: number, node: string }[]);
        }

        // B Nodes
        if (idSecondChar === 'A') {
            allNodes.push(...XC2064.B_EDGE_NODES as { x: number, y: number, node: string }[]);
        } else {
            allNodes.push(...XC2064.B_NODES as { x: number, y: number, node: string }[]);
        }

        // C Nodes
        if (idSecondChar === 'A') {
            allNodes.push(...XC2064.C_EDGE_NODES as { x: number, y: number, node: string }[]);
        } else {
            allNodes.push(...XC2064.C_NODES as { x: number, y: number, node: string }[]);
        }

        // D Nodes
        if (idFirstChar === 'H') {
            allNodes.push(...XC2064.D_EDGE_NODES as { x: number, y: number, node: string }[]);
        } else {
            allNodes.push(...XC2064.D_NODES as { x: number, y: number, node: string }[]);
        }

        // K Nodes
        if (idSecondChar === 'A') {
            allNodes.push(...XC2064.K_EDGE_NODES as { x: number, y: number, node: string }[]);
        } else {
            allNodes.push(...XC2064.K_NODES as { x: number, y: number, node: string }[]);
        }

        // X Nodes
        if (idSecondChar === 'H') {
            allNodes.push(...XC2064.X_EDGE_NODES as { x: number, y: number, node: string }[]);
        } else {
            allNodes.push(...XC2064.X_NODES as { x: number, y: number, node: string }[]);
        }

        // Y Nodes
        if (idSecondChar === 'H') {
            allNodes.push(...XC2064.Y_EDGE_NODES as { x: number, y: number, node: string }[]);
        } else {
            allNodes.push(...XC2064.Y_NODES as { x: number, y: number, node: string }[]);
        }

        // Switches
        switch (idFirstChar) {
            case 'A':
                if (idSecondChar != 'A') {
                    allSwitches.push(...XC2064.SWITCHES_TOP as { x: number, y: number }[]);
                }
                break;
            case 'H':
                if (idSecondChar !== 'A') {
                    allSwitches.push(...XC2064.SWITCHES_BOTTOM as { x: number, y: number }[]);
                    allSwitches.push(...XC2064.SWITCHES as { x: number, y: number }[]);
                } else {
                    allSwitches.push(...XC2064.SWITCHES_LEFT as { x: number, y: number }[]);
                }

                if (idSecondChar === 'H') {
                    allSwitches.push(...XC2064.SWITCHES_RIGHT as { x: number, y: number }[]);
                }
                break;
            default:
                switch (idSecondChar) {
                    case 'A':
                        allSwitches.push(...XC2064.SWITCHES_LEFT as { x: number, y: number }[]);
                        break;
                    case 'H':
                        allSwitches.push(...XC2064.SWITCHES_RIGHT as { x: number, y: number }[]);
                        allSwitches.push(...XC2064.SWITCHES as { x: number, y: number }[]);

                        break;
                    default:
                        allSwitches.push(...XC2064.SWITCHES as { x: number, y: number }[]);
                        break;
                }
                break;
        }

        setNodes(<>{allNodes.map((node, index) => <NodeComponent key={index + "-"} x={x + node.x} y={y + node.y} node={logicElement.id + ":" + node.node} />)}</>);
        setSwitches(<>{allSwitches.map((sw, index) => <SwitchComponent key={index + "s"} x={x + sw.x} y={y + sw.y} />)}</>);

        generateIOBusses(allNodes);


    }, []);



    return <>
        <g className="LogicElement" transform={`translate(${x}, ${y})`}>
            <rect 
                x={0} 
                y={0} 
                width={50} 
                height={80} 
                fill="white" 
                stroke="black" 
                strokeWidth={2}
                onClick={handleClick}
                style={{ cursor: 'pointer' }}
            />
            <text 
                x={25} 
                y={45} 
                textAnchor="middle" 
                fontSize={14} 
                fontWeight="bold"
                pointerEvents="none"
            >
                {logicElement.id}
            </text>

            {/* IO Labels */}
            <text className="LogicElementIOLabel" x={42} y={8} fontSize={8} pointerEvents="none">A</text>
            <text className="LogicElementIOLabel" x={27} y={78} fontSize={8} pointerEvents="none">D</text>
            <text className="LogicElementIOLabel" x={2} y={30} fontSize={8} pointerEvents="none">B</text>
            <text className="LogicElementIOLabel" x={2} y={45} fontSize={8} pointerEvents="none">C</text>
            <text className="LogicElementIOLabel" x={2} y={72} fontSize={8} pointerEvents="none">K</text>
            <text className="LogicElementIOLabel" x={43} y={12} fontSize={8} pointerEvents="none">X</text>
            <text className="LogicElementIOLabel" x={43} y={78} fontSize={8} pointerEvents="none">Y</text>
        </g>
        {nodes}
        {switches}
        {busses}
    </>
}