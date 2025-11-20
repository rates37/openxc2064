import React, { useState } from 'react';
import "../styles/Node.css";

type NodeComponentProps = {
    x: number;
    y: number;
};

export const NodeComponent: React.FC<NodeComponentProps> = ({ x, y }) => {
    const [isActive, setIsActive] = useState(false);

    const handleClick = () => {
        setIsActive(!isActive);
    };
    
    return <div 
        className="Node" 
        onClick={handleClick}
        style={{ backgroundColor: isActive ? 'black' : undefined, left: x, top: y }}
    ></div>;
}