import React from 'react';
import "../styles/Bus.css";
import { useEffect } from 'react';
import { SimulatorContext } from '../context/SimulatorContext';

type NodeBusComponentProps = {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    nodeID: string;
    strokeWidth?: number;
    stroke?: string;
};


export const NodeBusComponent: React.FC<NodeBusComponentProps> = ({ x1, y1, x2, y2, nodeID, strokeWidth, stroke }) => {
    const [active, setActive] = React.useState(false);
    const context = React.useContext(SimulatorContext);

    // console.log(nodeID);

    useEffect(() => {
        // console.log("NodeBusComponent useEffect", context.globalNets, nodeID);

        const netValue = context.getNet(nodeID);

        if (netValue !== undefined) {
            setActive(netValue === 1);
        } else {
            setActive(false);
        }

    }, [context.globalNets, nodeID]);

    return <line
        className={`NodeBus${active ? "Active" : ""}`}
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke={active ? "red" : (stroke || "black")}
        strokeWidth={active ? 2 : (strokeWidth || 1)}
    />;
}