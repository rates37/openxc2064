import React from 'react';
import { createPortal } from 'react-dom';
import { LogicElement } from '../models/LogicElement';
import "../styles/LogicArray.css";
import { useEffect } from 'react';
import { NodeComponent } from './NodeComponent';
import { XC2064 } from '../constants';
import { SwitchComponent } from './SwitchComponent';
import { BusComponent } from './BusComponent';
import { NodeBusComponent } from './NodeBusComponent';
import { SimulatorContext } from '../context/SimulatorContext';
import { SwitchMatrix } from '../models/SwitchMatrix';

type LogicElementComponentProps = {
    i: number;
    j: number;
    x: number;
    y: number;
    onClick?: (element: LogicElement) => void;
    onSwitchClick?: (matrix: SwitchMatrix) => void;
    bussesContainer?: SVGGElement | null;
    switchesContainer?: SVGGElement | null;
    nodesContainer?: SVGGElement | null;
};

export const LogicElementComponent: React.FC<LogicElementComponentProps> = ({ 
    i, j, x, y, onClick, onSwitchClick,
    bussesContainer, switchesContainer, nodesContainer 
}) => {
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

                // Calculate the index relative to the node type (e.g., A1, A2, B1, B2)
                // We need to count how many nodes of this type we've seen so far in this specific list

                setBusses(prev => <>
                    {prev}
                    <NodeBusComponent x1={busXStart} y1={busY} x2={busXEnd} y2={busY} nodeID={logicElement.id + ":" + nodeName} />
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
                const busX = topNodes[0].x + x + 3;

                // Calculate the index relative to the node type (e.g., A1, A2, B1, B2)
                // We need to count how many nodes of this type we've seen so far in this specific list;

                setBusses(prev => <>
                    {prev}
                    <NodeBusComponent x1={busX} y1={busYStart} x2={busX} y2={busYEnd} nodeID={logicElement.id + ":" + nodeName} />
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
                const busX = bottomNodes[0].x + x + 3;

                // Calculate the index relative to the node type (e.g., A1, A2, B1, B2)
                // We need to count how many nodes of this type we've seen so far in this specific list;

                setBusses(prev => <>
                    {prev}
                    <NodeBusComponent x1={busX} y1={busYEnd} x2={busX} y2={busYStart} nodeID={logicElement.id + ":" + nodeName} />
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

                // Calculate the index relative to the node type (e.g., A1, A2, B1, B2)
                // We need to count how many nodes of this type we've seen so far in this specific list

                setBusses(prev => <>
                    {prev}
                    <NodeBusComponent x1={busXEnd} y1={busY} x2={busXStart} y2={busY} nodeID={logicElement.id + ":" + nodeName} />
                </>);
            }
        });


    }

    useEffect(() => {
        logicElement.init_nets(context);


        const allNodes: { x: number, y: number, node: string, switch?: number, net?: number }[] = [];
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
            allNodes.push(...XC2064.B_NODES as { x: number, y: number, node: string, switch: number, net: number }[]);
        }

        // C Nodes
        if (idSecondChar === 'A') {
            allNodes.push(...XC2064.C_EDGE_NODES as { x: number, y: number, node: string }[]);
        } else {
            allNodes.push(...XC2064.C_NODES as { x: number, y: number, node: string, switch: number, net: number }[]);
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

        // Generate Switch Busses
        const DLE = logicElement.getNeighbour("down", context.logicElements);
        const LLE = logicElement.getNeighbour("left", context.logicElements);
        const ULE = logicElement.getNeighbour("up", context.logicElements);
        const RLE = logicElement.getNeighbour("right", context.logicElements);

        const DRLE = DLE ? DLE.getNeighbour("right", context.logicElements) : null;


        const leftLE = LLE ? LLE.id + "-SW-" : "";
        const downLE = DLE ? DLE.id + "-SW-" : "";

        const switchElements = [];

        // Generate Switches
        for (const sw of allSwitches) {
            const swId = `${logicElement.id}-SW-${allSwitches.indexOf(sw)}`;

            // console.log(swId, downLE, leftLE);
            switchElements.push(<SwitchComponent key={swId} x={sw.x + x} y={sw.y + y} id={swId} onClick={onSwitchClick} downLE={downLE} leftLE={leftLE} />);
        }


        const switchBusses = [];

        const setSwitchBusses = () => {

            // Generate Switch Busses
            for (const sw of allSwitches) {
                const swId = `${logicElement.id}-SW-${allSwitches.indexOf(sw)}`;

                const switchObj = context.switchMatrices.find(s => s.id === swId);

                if (!switchObj) continue;

                if (ULE) {
                    const ULE_sw = context.switchMatrices.find(s => s.id.startsWith(ULE.id + "-SW-" + allSwitches.indexOf(sw)));
                    let x1, y1, x2, y2;

                    if (!ULE_sw) continue;

                    // console.log(switchObj.points["1"], sw);
                    // console.log(ULE_sw.points);
                    x1 = switchObj.points.find(p => p.key === "1").x + switchObj.x + 1;
                    x2 = ULE_sw.points.find(p => p.key === "6").x + ULE_sw.x + 1;
                    y1 = switchObj.points.find(p => p.key === "1").y + switchObj.y;
                    y2 = ULE_sw.points.find(p => p.key === "6").y + ULE_sw.y;
                    switchBusses.push(<NodeBusComponent key={swId + "_net_1"} x1={x1} y1={y1} x2={x2} y2={y2} id={swId} nodeID={swId + "_net_1"} strokeWidth={0.5} stroke={"lightgray"} />);

                    x1 = switchObj.points.find(p => p.key === "2").x + switchObj.x + 1;
                    x2 = ULE_sw.points.find(p => p.key === "5").x + ULE_sw.x + 1;
                    y1 = switchObj.points.find(p => p.key === "2").y + switchObj.y;
                    y2 = ULE_sw.points.find(p => p.key === "5").y + ULE_sw.y;
                    switchBusses.push(<NodeBusComponent key={swId + "_net_2"} x1={x1} y1={y1} x2={x2} y2={y2} id={swId} nodeID={swId + "_net_2"} strokeWidth={0.5} stroke={"lightgray"} />);

                    // console.log("Generated ULE bus", swId, x1, y1, x2, y2);
                }

                if (RLE) {
                    const RLE_sw = context.switchMatrices.find(s => s.id.startsWith(RLE.id + "-SW-" + allSwitches.indexOf(sw)));
                    let x1, y1, x2, y2;
                    if (!RLE_sw) continue;

                    x1 = switchObj.points.find(p => p.key === "3").x + switchObj.x;
                    x2 = RLE_sw.points.find(p => p.key === "8").x + RLE_sw.x;
                    y1 = switchObj.points.find(p => p.key === "3").y + switchObj.y + 1;
                    y2 = RLE_sw.points.find(p => p.key === "8").y + RLE_sw.y + 1;
                    switchBusses.push(<NodeBusComponent key={swId + "_net_3"} x1={x1} y1={y1} x2={x2} y2={y2} id={swId} nodeID={swId + "_net_3"} strokeWidth={0.5} stroke={"lightgray"} />);

                    x1 = switchObj.points.find(p => p.key === "4").x + switchObj.x;
                    x2 = RLE_sw.points.find(p => p.key === "7").x + RLE_sw.x;
                    y1 = switchObj.points.find(p => p.key === "4").y + switchObj.y + 1;
                    y2 = RLE_sw.points.find(p => p.key === "7").y + RLE_sw.y + 1;
                    switchBusses.push(<NodeBusComponent key={swId + "_net_4"} x1={x1} y1={y1} x2={x2} y2={y2} id={swId} nodeID={swId + "_net_4"} strokeWidth={0.5} stroke={"lightgray"} />);
                    // console.log("Generated RLE bus", swId, x1, y1, x2, y2);
                }

            }

            setBusses(prev => <>{prev}{switchBusses}</>);
        }

        setSwitches(<>{switchElements}</>);


        // setSwitches(<>{allSwitches.map((sw, index) => <SwitchComponent key={index + "s"} x={x + sw.x} y={y + sw.y} id={`${logicElement.id}-SW-${index}`} onClick={onSwitchClick} />)}</>);
        generateIOBusses(allNodes);

        setTimeout(() => {
            setSwitchBusses();

            setTimeout(() => {
                setNodes(<>
                    {allNodes.map((node, index) => {
                        // Calculate the index relative to the node type (e.g., A1, A2, B1, B2)
                        // We need to count how many nodes of this type we've seen so far in this specific list
                        const nodeType = node.node;
                        const nodesOfType = allNodes.filter(n => n.node === nodeType);
                        const relativeIndex = nodesOfType.indexOf(node) + 1;
                        const label = `${nodeType}${relativeIndex}`;

                        let connectedNets: { input: string, output: string } = { input: "", output: "" };


                        switch (node.node) {
                            case "B":
                                if (node.switch !== undefined && node.net !== undefined) {
                                    if (DLE) {
                                        const DLE_sw = context.switchMatrices.find(s => s.id.startsWith(DLE.id + "-SW-" + node.switch));
                                        if (!DLE_sw) return;

                                        connectedNets = {
                                            input: DLE.id + "-SW-" + node.switch + "_net_" + node.net,
                                            output: logicElement.id + ":" + nodeType
                                        };
                                    }
                                }

                                break;
                            case "Y":
                                // console.log(node.switch, node.net);
                                if (node.switch !== undefined && node.net !== undefined) {
                                    if (DRLE) {
                                        // console.log(context.switchMatrices);
                                        // console.log(DRLE.id + "-SW-" + node.switch);
                                        const DRLE_sw = context.switchMatrices.find(s => s.id === DRLE.id + "-SW-" + node.switch);
                                        if (!DRLE_sw) return;

                                        connectedNets = {
                                            input: logicElement.id + ":" + nodeType,
                                            output: DRLE.id + "-SW-" + node.switch + "_net_" + node.net,
                                        };
                                    }
                                }
                                break;
                        }





                        return (
                            <g key={index + "-g"}>

                                <NodeComponent
                                    key={index + "-"}
                                    x={x + node.x}
                                    y={y + node.y}
                                    node={logicElement.id + ":" + node.node}
                                    label={label}
                                    connectedNets={connectedNets}
                                />
                            </g>
                        );
                    })}
                </>);
            }, 50);
        }, 50);


    }, []);

    useEffect(() => {
        const canvas = context.canvas;
        if (!canvas) return;

        // Draw the logic element on the canvas
        const ctx = canvas.getContext("2d");
        if (ctx) {
            ctx.fillStyle = "white";
            ctx.fillRect(x, y, 50, 80);
            ctx.strokeStyle = "black";
            ctx.strokeRect(x, y, 50, 80);
            ctx.fillStyle = "black";
            ctx.fillText(logicElement.id, x + 18, y + 40);
        }
    }, [context.canvas, x, y, logicElement.id]);

    return <>
        <rect
            x={x}
            y={y}
            width={50}
            height={80}
            fill="transparent"
            onClick={handleClick}
            style={{ cursor: 'pointer' }}
        />
        
        {bussesContainer ? createPortal(busses, bussesContainer) : (
            <g className="busses-layer">
                {busses}
            </g>
        )}
        
        {switchesContainer ? createPortal(switches, switchesContainer) : (
            <g className="switches-layer">
                {switches}
            </g>
        )}

        {nodesContainer ? createPortal(nodes, nodesContainer) : (
            <g className="nodes-layer" style={{ isolation: 'isolate' }}>
                {nodes}
            </g>
        )}
    </>
}