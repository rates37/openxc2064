import React, { useState, useEffect } from 'react';
import { LogicCell } from '../models/LogicCell';
import { useSimulator } from '../SimulatorContext';


const LogicCellRenderer = () => {
    const { logicCells } = useSimulator();
    const [logicCellDisplays, setLogicCellDisplays] = useState<React.ReactNode[]>([]);

    const CELL_WIDTH = 180;
    const CELL_HEIGHT = 280;
    const CELL_MARGIN_X = 500;
    const CELL_MARGIN_Y = 330;

    useEffect(() => {
        // Initialize display state for this cell if not already set


        const displays = logicCells.map((cell, index) => {
            const row = Math.floor(index / 8);
            const col = index % 8;

            const x = col * (CELL_WIDTH + CELL_MARGIN_X);
            const y = row * (CELL_HEIGHT + CELL_MARGIN_Y);

            return <React.Fragment key={cell.id}>
                <rect
                    x={x} y={y} width={CELL_WIDTH} height={CELL_HEIGHT}
                    fill="#fff" stroke="#333" strokeWidth={8} rx={5} ry={5}
                />
                <text x={x + CELL_WIDTH / 2} y={y + CELL_HEIGHT / 2} textAnchor="middle" dominantBaseline="middle" fontSize={48}>
                    {cell.id}
                </text>
            </React.Fragment>   
        });

        setLogicCellDisplays(displays);

    }, [logicCells]);





    return (
        <g>
            {/* Cell background */}
            {logicCellDisplays}
            {/* Cell name */}
        </g>
    );
};

export default LogicCellRenderer;
