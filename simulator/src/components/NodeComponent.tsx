import React, { useState } from 'react';
import "../styles/Node.css";

type NodeComponentProps = {
    x: number;
    y: number;
    node?: string;
};

export const NodeComponent: React.FC<NodeComponentProps> = ({ x, y, node }) => {
    const [isActive, setIsActive] = useState(false);

    const handleClick = () => {
        setIsActive(!isActive);
    };
    
    return <circle 
        className="Node" 
        cx={x} 
        cy={y} 
        r={3}
        fill={isActive ? 'black' : 'white'}
        stroke="black"
        strokeWidth={1}
        onClick={handleClick}
        style={{ cursor: 'pointer' }}
    />;
}