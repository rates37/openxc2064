import React, { useState } from 'react';
import "../styles/Switch.css";

type SwitchComponentProps = {
    x: number;
    y: number;
};

export const SwitchComponent: React.FC<SwitchComponentProps> = ({ x, y }) => {
    return <rect 
        className="Switch" 
        x={x}
        y={y}
        width={5}
        height={5}
        fill="#ccc"
        stroke="black"
        strokeWidth={0.5}
    />;
}