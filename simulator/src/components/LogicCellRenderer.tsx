import React, { useState, useEffect } from 'react';
import { LogicCell } from '../models/LogicCell';
import { useSimulator } from '../SimulatorContext';
import { LineSegment } from './LineSegment';
import { CELL_WIDTH, CELL_HEIGHT, PIP_WIDTH, PIP_HEIGHT, MATRIX_WIDTH, MATRIX_HEIGHT } from '../configs/Routing';


const LogicCellRenderer = () => {
    const { logicCells, switchMatrices, pips, togglePip, selectMatrix, selectCell } = useSimulator();

    const logicCellDisplays = logicCells.map((cell, index) => {
        const { x, y } = cell.pos;

        return <React.Fragment key={cell.id}>
            {cell.nets.filter(net => net.points.length > 0).map(
                (net, netIndex) => {
                    return <LineSegment key={netIndex} value={net.value} baseX={x + CELL_WIDTH / 2} baseY={y + CELL_HEIGHT / 2} points={net.points} />
                }
            )}
            <rect
                x={x} y={y} width={CELL_WIDTH} height={CELL_HEIGHT}
                fill="#fff" stroke="#333" strokeWidth={8} rx={5} ry={5}
                style={{ cursor: 'pointer' }}
                onClick={(e) => { e.stopPropagation(); selectCell(cell); }}
            />
            <text x={x + CELL_WIDTH / 2} y={y + CELL_HEIGHT / 2} textAnchor="middle" dominantBaseline="middle" fontSize={48}>
                {cell.id}
            </text>


        </React.Fragment>
    });

    // Mini node positions for switch matrix graph (relative to center, scaled to fit inside MATRIX_WIDTH x MATRIX_HEIGHT)
    const R = (MATRIX_WIDTH / 2) - 4; // ring radius inside the box
    const miniNodeOffsets = [
        { dx: -10, dy: -R },   // 0 - top-left
        { dx: 10,  dy: -R },   // 1 - top-right
        { dx: R,  dy: -10 },   // 2 - right-top
        { dx: R,  dy: 10 },    // 3 - right-bottom
        { dx: 10,  dy: R },    // 4 - bottom-right
        { dx: -10, dy: R },    // 5 - bottom-left
        { dx: -R, dy: 10 },    // 6 - left-bottom
        { dx: -R, dy: -10 },   // 7 - left-top
    ];

    const switchMatrixDisplays = switchMatrices.map((matrix, index) => {
        const cx = matrix.pos.x + MATRIX_WIDTH / 2;
        const cy = matrix.pos.y + MATRIX_HEIGHT / 2;

        // Collect active connection lines
        const lines: { from: number; to: number }[] = [];
        for (let i = 0; i < 8; i++) {
            for (let j = i + 1; j < 8; j++) {
                if (matrix.connections[i]?.[j] || matrix.connections[j]?.[i]) {
                    lines.push({ from: i, to: j });
                }
            }
        }

        return <React.Fragment key={index}>
            <rect
                x={matrix.pos.x} y={matrix.pos.y} width={MATRIX_WIDTH} height={MATRIX_HEIGHT}
                fill="#fff" stroke="#333" strokeWidth={8} rx={5} ry={5}
                style={{ cursor: 'pointer' }}
                onClick={(e) => { e.stopPropagation(); selectMatrix(matrix); }}
            />
            {/* Mini connection lines */}
            {lines.map(({ from, to }) => (
                <line
                    key={`mc-${index}-${from}-${to}`}
                    x1={cx + miniNodeOffsets[from].dx} y1={cy + miniNodeOffsets[from].dy}
                    x2={cx + miniNodeOffsets[to].dx} y2={cy + miniNodeOffsets[to].dy}
                    stroke="#2196F3" strokeWidth={1.5}
                    pointerEvents="none"
                />
            ))}
            {/* Mini node dots */}
            {miniNodeOffsets.map((off, i) => (
                <circle
                    key={`mn-${index}-${i}`}
                    cx={cx + off.dx} cy={cy + off.dy} r={2}
                    fill="#333"
                    pointerEvents="none"
                />
            ))}
            {matrix.nets.filter(net => (net !== null)).filter(net => net.points.length > 0).map(
                (net, netIndex) => {
                    if (netIndex > 3) return;
                    return <LineSegment key={netIndex} value={net.value} baseX={cx} baseY={cy} points={net.points} />
                }
            )}
        </React.Fragment>
    });

    // console.log(pips);
    const pipDisplays = pips.map((pip, index) => {
        return <React.Fragment key={index}>
            <rect
                x={pip.pos.x - PIP_WIDTH / 2} y={pip.pos.y - PIP_HEIGHT / 2}
                width={PIP_WIDTH} height={PIP_HEIGHT}
                fill={pip.enabled ? "#000000" : "#ffffff"} stroke="#333" strokeWidth={3}
                style={{ cursor: 'pointer' }}
                onClick={() => togglePip(index)}
            />
        </React.Fragment>
    });


    return (
        <g>
            {logicCellDisplays}

            {switchMatrixDisplays}
        
            {pipDisplays}
        </g>
    );
};

export default React.memo(LogicCellRenderer);
