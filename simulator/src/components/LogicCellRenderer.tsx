import React from 'react';
import { LogicCell } from '../models/LogicCell';
import { SwitchMatrix } from '../models/SwitchMatrix';
import { IOBank } from '../models/IOBank';
import { Net, Pip } from '../types';
import { useSimulator } from '../SimulatorContext';
import { LineSegment } from './LineSegment';
import { CELL_WIDTH, CELL_HEIGHT, PIP_WIDTH, PIP_HEIGHT, MATRIX_WIDTH, MATRIX_HEIGHT, IO_WIDTH, IO_HEIGHT } from '../configs/Routing';

// --- Individual memoized components ---

const CellDisplay = React.memo(({ cell, tick, onSelect }: { cell: LogicCell; tick: number; onSelect: (cell: LogicCell) => void }) => {
    const { x, y } = cell.pos;
    return <g>
        {cell.nets.filter(net => net.points.length > 0).map(
            (net, netIndex) => <LineSegment key={netIndex} value={net.value} baseX={x + CELL_WIDTH / 2} baseY={y + CELL_HEIGHT / 2} points={net.points} />
        )}
        <rect
            x={x} y={y} width={CELL_WIDTH} height={CELL_HEIGHT}
            fill="#fff" stroke="#333" strokeWidth={8} rx={5} ry={5}
            style={{ cursor: 'pointer' }}
            onClick={(e) => { e.stopPropagation(); onSelect(cell); }}
        />
        <text x={x + CELL_WIDTH / 2} y={y + CELL_HEIGHT / 2} textAnchor="middle" dominantBaseline="middle" fontSize={48}>
            {cell.id}
        </text>
        <text x={x + CELL_WIDTH / 2 + 60} y={y + CELL_HEIGHT / 2 - 135} textAnchor="middle" dominantBaseline="middle" fontSize={24} fill="#666">A</text>
        <text x={x + CELL_WIDTH / 2 - 80} y={y + CELL_HEIGHT / 2 - 38} textAnchor="middle" dominantBaseline="middle" fontSize={24} fill="#666">B</text>
        <text x={x + CELL_WIDTH / 2 - 80} y={y + CELL_HEIGHT / 2 + 23} textAnchor="middle" dominantBaseline="middle" fontSize={24} fill="#666">C</text>
        <text x={x + CELL_WIDTH / 2} y={y + CELL_HEIGHT - 18} textAnchor="middle" dominantBaseline="middle" fontSize={24} fill="#666">D</text>
        <text x={x + CELL_WIDTH / 2 + 80} y={y + CELL_HEIGHT / 2 + 23} textAnchor="middle" dominantBaseline="middle" fontSize={24} fill="#666">X</text>
        <text x={x + CELL_WIDTH / 2 + 80} y={y + CELL_HEIGHT / 2 + 102} textAnchor="middle" dominantBaseline="middle" fontSize={24} fill="#666">Y</text>
        <text x={x + CELL_WIDTH / 2 - 80} y={y + CELL_HEIGHT / 2 + 83} textAnchor="middle" dominantBaseline="middle" fontSize={24} fill="#666">K</text>
    </g>;
});

const R = (MATRIX_WIDTH / 2) - 2;
const miniNodeOffsets = [
    { dx: -10, dy: -R },
    { dx: 10, dy: -R },
    { dx: R, dy: -10 },
    { dx: R, dy: 10 },
    { dx: 10, dy: R },
    { dx: -10, dy: R },
    { dx: -R, dy: 10 },
    { dx: -R, dy: -10 },
];

const MatrixDisplay = React.memo(({ matrix, index, tick, onSelect }: { matrix: SwitchMatrix; index: number; tick: number; onSelect: (m: SwitchMatrix) => void }) => {
    const cx = matrix.pos.x + MATRIX_WIDTH / 2;
    const cy = matrix.pos.y + MATRIX_HEIGHT / 2;

    const lines: { from: number; to: number }[] = [];
    for (let i = 0; i < 8; i++) {
        for (let j = i + 1; j < 8; j++) {
            if (matrix.connections[i]?.[j] || matrix.connections[j]?.[i]) {
                lines.push({ from: i, to: j });
            }
        }
    }

    return <g>
        {matrix.nets.filter(net => (net !== null)).filter(net => net.points.length > 0).map(
            (net, netIndex) => {
                if (netIndex > 3) return null;
                return <LineSegment key={netIndex} value={net.value} baseX={cx} baseY={cy} points={net.points} colour={"rgb(199, 199, 199)"} />;
            }
        )}
        <rect
            x={matrix.pos.x} y={matrix.pos.y} width={MATRIX_WIDTH} height={MATRIX_HEIGHT}
            fill="#fff" stroke="#333" strokeWidth={5} rx={5} ry={5}
            style={{ cursor: 'pointer' }}
            onClick={(e) => { e.stopPropagation(); onSelect(matrix); }}
        />
        {lines.map(({ from, to }) => (
            <line
            key={`mc-${index}-${from}-${to}`}
            x1={cx + miniNodeOffsets[from].dx} y1={cy + miniNodeOffsets[from].dy}
            x2={cx + miniNodeOffsets[to].dx} y2={cy + miniNodeOffsets[to].dy}
            stroke="#2196F3" strokeWidth={1.5}
            pointerEvents="none"
            />
        ))}
        {miniNodeOffsets.map((off, i) => (
            <circle
            key={`mn-${index}-${i}`}
            cx={cx + off.dx} cy={cy + off.dy} r={2}
                fill="#333"
                pointerEvents="none"
            />
        ))}
    </g>;
});

const PipDisplay = React.memo(({ pip, index, onToggle }: { pip: Pip; index: number; onToggle: (i: number) => void }) => {
    return <rect
        x={pip.pos.x - PIP_WIDTH / 2} y={pip.pos.y - PIP_HEIGHT / 2}
        width={PIP_WIDTH} height={PIP_HEIGHT}
        fill={pip.enabled ? "#696969" : "#ffffff"} stroke="#333" strokeWidth={3}
        style={{ cursor: 'pointer' }}
        onClick={() => onToggle(index)}
    />;
});

const IODisplay = React.memo(({ bank, index, tick, onToggle, onSimulate }: { bank: IOBank; index: number; tick: number; onToggle: (i: number) => void; onSimulate: () => void }) => {
    const { x, y } = bank.pos;
    const netO = bank.nets.find(n => n.id === `${bank.id}.net_O`);
    const isActive = netO?.value ?? false;

    return <g>
        <rect
            x={x} y={y} width={bank.size.width} height={bank.size.height}
            fill={isActive ? "#f76420" : "#fff"} stroke="#333" strokeWidth={5} rx={5} ry={5}
            style={{ cursor: 'pointer' }}
            onClick={(e) => { e.stopPropagation(); onToggle(index); onSimulate(); }}
        />
        {bank.nets.filter(net => net.points.length > 0).map(
            (net, netIndex) => <LineSegment key={netIndex} value={net.value} baseX={x + IO_WIDTH / 2} baseY={y + IO_HEIGHT / 2} points={net.points} colour={"#333"} />
        )}
    </g>;
});

const BusNetDisplay = React.memo(({ net, tick }: { net: Net; tick: number }) => {
    if (net.points.length < 2) return null;
    return <LineSegment value={net.value} baseX={0} baseY={0} points={net.points} colour={"rgb(68, 68, 68)"} />;
});

// --- Main renderer ---

const LogicCellRenderer = () => {
    const { logicCells, switchMatrices, pips, ioBanks, busNets, togglePip, selectMatrix, selectCell, toggleIONet, simulate, tick } = useSimulator();

    return (
        <g>
            {busNets.map((net, i) =>
                <BusNetDisplay key={net.id || i} net={net} tick={tick} />
            )}
            {switchMatrices.map((matrix, i) =>
                <MatrixDisplay key={matrix.id} matrix={matrix} index={i} tick={tick} onSelect={selectMatrix} />
            )}
            {logicCells.map(cell =>
                <CellDisplay key={cell.id} cell={cell} tick={tick} onSelect={selectCell} />
            )}
            {ioBanks.map((bank, i) =>
                <IODisplay key={bank.id} bank={bank} index={i} tick={tick} onToggle={toggleIONet} onSimulate={simulate} />
            )}
            {pips.map((pip, i) =>
                <PipDisplay key={i} pip={pip} index={i} onToggle={togglePip} />
            )}
        </g>
    );
};

export default React.memo(LogicCellRenderer);
