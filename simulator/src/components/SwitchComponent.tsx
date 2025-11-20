import React, { useState } from 'react';
import "../styles/Switch.css";

type SwitchComponentProps = {
    x: number;
    y: number;
};

export const SwitchComponent: React.FC<SwitchComponentProps> = ({ x, y }) => {
    return <div 
        className="Switch" 
        style={{ left: x, top: y }}
    ></div>;
}