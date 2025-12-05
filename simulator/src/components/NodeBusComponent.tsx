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
    nets: {[key: string]: 0 | 1};
};  

    
export const NodeBusComponent: React.FC<NodeBusComponentProps> = ({x1, y1, x2, y2, nodeID, nets}) => {
    const [active, setActive] = React.useState(false);
    const context  = React.useContext(SimulatorContext);
    
    useEffect(() => {   
        if (nets && nodeID in nets) {
            setActive(nets[nodeID] === 1);
        }
    }, [context.logicElements, nets, nodeID]);

    return <line 
        className={`NodeBus${active ? "Active" : ""}`}
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke={active ? "red" : "black"}
        strokeWidth={active ? 2 : 1}
    />; 
}