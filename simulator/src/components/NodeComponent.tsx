import React, { useState } from 'react';
import "../styles/Node.css";
import { SimulatorContext } from '../context/SimulatorContext';

type NodeComponentProps = {
    x: number;
    y: number;
    node?: string;
    label?: string;
    connectedNets?  : string[];
};

export const NodeComponent: React.FC<NodeComponentProps> = ({ x, y, node, label, connectedNets }) => {
    const [isActive, setIsActive] = useState(false);
    const context = React.useContext(SimulatorContext);

    const handleClick = () => {
        setIsActive(!isActive);

        if (connectedNets === undefined) return;
        // if (connectedNets && connectedNets.length < 2) return;
        console.log(connectedNets);

        if (isActive) {
            context.unbindNets(connectedNets["input"], connectedNets["output"]);
        } else {
            context.bindNets(connectedNets["input"], connectedNets["output"]);
        }

    };
    
    // Render the rect on the background
    // If the node is active, it will be black, otherwise it will be white
    // The node is clickable to toggle its state
    // The node has a stroke of black and a width of 1
    // The node has a cursor pointer style
    return (
        <g onClick={handleClick} style={{ cursor: 'pointer' }}>
            {(label && isActive && false) && (
                <text 
                    x={x + 3} 
                    y={y - 2} 
                    textAnchor="middle" 
                    fontSize="6" 
                    fill="green"
                    style={{ pointerEvents: 'none', userSelect: 'none' }}
                >
                    {label}
                </text>
            )}
            <rect 
                className="Node" 
                x={x} 
                y={y} 
                width={6}
                height={6}
                fill={isActive ? 'black' : 'white'}
                stroke="black"
                strokeWidth={1}
            />
        </g>
    );
}