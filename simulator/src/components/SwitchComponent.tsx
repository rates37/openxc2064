import React, { useState, useEffect } from 'react';
import "../styles/Switch.css";
import { SimulatorContext } from '../context/SimulatorContext';
import { SwitchMatrix } from '../models/SwitchMatrix';


type SwitchComponentProps = {
    x: number;
    y: number;
    id: string;
    onClick?: (matrix: SwitchMatrix) => void;
    downLE: string;
    leftLE: string;
};

export const SwitchComponent: React.FC<SwitchComponentProps> = ({ x, y, id, onClick, downLE, leftLE }) => {
    const [connections, setConnections] = useState<React.JSX.Element[]>([]);
    const [points, setPoints] = useState<React.JSX.Element[]>([]);
    const [matrix, setMatrix] = useState<SwitchMatrix | null>(null);
    const context = React.useContext(SimulatorContext);

    const handleClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (onClick && id) {
            onClick(matrix);
        }
    };

    useEffect(() => {
        if (!matrix) {
            const newMatrix = new SwitchMatrix(id, downLE, leftLE);
            newMatrix.x = x;
            newMatrix.y = y;
            newMatrix.initializeNets(context, downLE, leftLE);
            setMatrix(newMatrix);
            context.updateSwitchMatrix(newMatrix);
        }

    }, []);

    useEffect(() => {
        if (!matrix) return;
        context.updateSwitchMatrix(matrix);
    }, [matrix]);

    useEffect(() => {
        // const currentSwitch = context.switchMatrices.find(s => s.id === id);
        // if (!currentSwitch) return;
        // const currentPoints = currentSwitch.points.map((point, i) => (
        //     <rect key={`point-${i}`} x={point.x + x} y={point.y + y} width={2} height={2} fill="black" />
        // ));
        // setPoints(currentPoints);

        // console.log("SwitchComponent useEffect", currentPoints);

    }, [context]);

    return <>
        {/* {points} */}
        <rect
            className="Switch"
            x={x - 2}
            y={y - 2}
            width={21}
            height={21}
            fill="#ccc"
            stroke="black"
            strokeWidth={0.5}
            onClick={handleClick}
            style={{ cursor: 'pointer' }}
        />
    </>;
}