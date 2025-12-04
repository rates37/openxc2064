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

    return <div className={`NodeBus${active ? "Active" : ""}`} style={
        {top: y1, left: x1, width: x2 - x1, height: y2 - y1}
    }></div>; 
}