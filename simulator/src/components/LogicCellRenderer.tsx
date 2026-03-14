import React, { useMemo } from 'react';
import { LogicCell } from '../models/LogicCell';
import { SwitchMatrix } from '../models/SwitchMatrix';
import { IOBank } from '../models/IOBank';
import { Net, Pip } from '../types';
import { useSimulator } from '../SimulatorContext';
import { LineSegment } from './LineSegment';
import { CELL_WIDTH, CELL_HEIGHT, PIP_WIDTH, PIP_HEIGHT, MATRIX_WIDTH, MATRIX_HEIGHT, IO_WIDTH, IO_HEIGHT } from '../configs/Routing';

// --- Individual memoized components ---

const CellDisplay = React.memo(({ cell, onSelect }: { cell: LogicCell; onSelect: (cell: LogicCell) => void }) => {
    const { x, y } = cell.pos;
    const netsWithPoints = useMemo(() => cell.nets.filter(net => net.points.length > 0), [cell.nets]);
    
    return <g>
        {netsWithPoints.map(
            (net, netIndex) => <LineSegment key={net.id || netIndex} value={net.value} baseX={x + CELL_WIDTH / 2} baseY={y + CELL_HEIGHT / 2} points={net.points} />
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
}, (prevProps, nextProps) => {
    return prevProps.cell === nextProps.cell && prevProps.onSelect === nextProps.onSelect;
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

const MatrixDisplay = React.memo(({ matrix, index, onSelect }: { matrix: SwitchMatrix; index: number; onSelect: (m: SwitchMatrix) => void }) => {
    const cx = matrix.pos.x + MATRIX_WIDTH / 2;
    const cy = matrix.pos.y + MATRIX_HEIGHT / 2;

    const lines = useMemo(() => {
        const result: { from: number; to: number }[] = [];
        for (let i = 0; i < 8; i++) {
            for (let j = i + 1; j < 8; j++) {
                if (matrix.connections[i]?.[j] || matrix.connections[j]?.[i]) {
                    result.push({ from: i, to: j });
                }
            }
        }
        return result;
    }, [matrix.connections]);

    const netsWithPoints = useMemo(() => 
        matrix.nets.filter(net => net !== null && net.points.length > 0).slice(0, 4), 
        [matrix.nets]
    );

    return <g>
        {netsWithPoints.map(
            (net, netIndex) => <LineSegment key={net.id || netIndex} value={net.value} baseX={cx} baseY={cy} points={net.points} colour={"rgb(199, 199, 199)"} />
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
}, (prevProps, nextProps) => {
    return prevProps.matrix === nextProps.matrix && 
           prevProps.index === nextProps.index && 
           prevProps.onSelect === nextProps.onSelect;
});

const PipDisplay = React.memo(({ pip, index, onToggle }: { pip: Pip; index: number; onToggle: (i: number) => void }) => {
    return <rect
        x={pip.pos.x - PIP_WIDTH / 2} y={pip.pos.y - PIP_HEIGHT / 2}
        width={PIP_WIDTH} height={PIP_HEIGHT}
        fill={pip.enabled ? "#696969" : "#ffffff"} stroke="#333" strokeWidth={3}
        style={{ cursor: 'pointer' }}
        onClick={() => onToggle(index)}
    />;
}, (prevProps, nextProps) => {
    return prevProps.pip.enabled === nextProps.pip.enabled &&
           prevProps.pip.pos.x === nextProps.pip.pos.x &&
           prevProps.pip.pos.y === nextProps.pip.pos.y &&
           prevProps.index === nextProps.index;
});

const IODisplay = React.memo(({ bank, index, onToggle, onSimulate }: { bank: IOBank; index: number; onToggle: (i: number) => void; onSimulate: () => void }) => {
    const { x, y } = bank.pos;
    const netO = bank.nets.find(n => n.id === `${bank.id}.net_O`);
    const isActive = netO?.value ?? false;
    
    const netsWithPoints = useMemo(() => bank.nets.filter(net => net.points.length > 0), [bank.nets]);

    return <g>
        <rect
            x={x} y={y} width={bank.size.width} height={bank.size.height}
            fill={isActive ? "#f76420" : "#fff"} stroke="#333" strokeWidth={5} rx={5} ry={5}
            style={{ cursor: 'pointer' }}
            onClick={(e) => { e.stopPropagation(); onToggle(index); onSimulate(); }}
        />
        {netsWithPoints.map(
            (net, netIndex) => <LineSegment key={net.id || netIndex} value={net.value} baseX={x + IO_WIDTH / 2} baseY={y + IO_HEIGHT / 2} points={net.points} colour={"#333"} />
        )}
    </g>;
}, (prevProps, nextProps) => {
    const prevNetO = prevProps.bank.nets.find(n => n.id === `${prevProps.bank.id}.net_O`);
    const nextNetO = nextProps.bank.nets.find(n => n.id === `${nextProps.bank.id}.net_O`);
    return prevProps.bank === nextProps.bank && 
           prevProps.index === nextProps.index &&
           prevNetO?.value === nextNetO?.value;
});

const BusNetDisplay = React.memo(({ net }: { net: Net }) => {
    if (net.points.length < 2) return null;
    return <LineSegment value={net.value} baseX={0} baseY={0} points={net.points} colour={"rgb(68, 68, 68)"} />;
}, (prevProps, nextProps) => {
    return prevProps.net.value === nextProps.net.value && prevProps.net.points === nextProps.net.points;
});

// --- Main renderer ---

const LogicCellRenderer = React.memo(() => {
    const { logicCells, switchMatrices, pips, ioBanks, busNets, togglePip, selectMatrix, selectCell, toggleIONet, simulate } = useSimulator();

    return (
        <g shapeRendering="geometricPrecision">
            {busNets.map((net, i) =>
                <BusNetDisplay key={net.id || i} net={net} />
            )}
            {switchMatrices.map((matrix, i) =>
                <MatrixDisplay key={matrix.id} matrix={matrix} index={i} onSelect={selectMatrix} />
            )}
            {logicCells.map(cell =>
                <CellDisplay key={cell.id} cell={cell} onSelect={selectCell} />
            )}
            {ioBanks.map((bank, i) =>
                <IODisplay key={bank.id} bank={bank} index={i} onToggle={toggleIONet} onSimulate={simulate} />
            )}
            {pips.map((pip, i) =>
                <PipDisplay key={pip.id || i} pip={pip} index={i} onToggle={togglePip} />
            )}
        </g>
    );
});

export default LogicCellRenderer;
