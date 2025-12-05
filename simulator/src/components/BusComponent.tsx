import React from 'react';
import "../styles/Bus.css";

type BusComponentProps = {
    horizontal: boolean;
    point: number;
    length: number;
};  


export const BusComponent: React.FC<BusComponentProps> = ({horizontal, point, length}) => {
    if (horizontal) {
        return <line 
            className="Bus" 
            x1={-180}
            y1={point}
            x2={-180 + length}
            y2={point}
            stroke="black"
            strokeWidth={1}
        />;
    } else {
        return <line 
            className="Bus" 
            x1={point}
            y1={-110}
            x2={point}
            y2={-110 + length}
            stroke="black"
            strokeWidth={1}
        />;
    }
}