import React from 'react';
import "../styles/Bus.css";

type BusComponentProps = {
    horizontal: boolean;
    point: number;
    length: number;
};  


export const BusComponent: React.FC<BusComponentProps> = ({horizontal, point, length}) => {
    return <div className="Bus" style={
        {top: horizontal ? point : -110, left: horizontal ? -180 : point, width: horizontal ? length : 2, height: horizontal ? 2 : length}
    }></div>; 
}