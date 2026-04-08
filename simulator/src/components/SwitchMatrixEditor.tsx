import React, { useState, useEffect } from 'react';
import { useSimulator } from '../SimulatorContext';

const SVG_SIZE = 360;
const CX = SVG_SIZE / 2;
const CY = SVG_SIZE / 2;
const NODE_RADIUS = 16;
const RING_RADIUS = 130;

// Nodes placed around the perimeter: top pair, right pair, bottom pair, left pair
const NODE_POSITIONS: { x: number; y: number }[] = [
    { x: CX - 30, y: CY - RING_RADIUS },  // 0 - top-left
    { x: CX + 30, y: CY - RING_RADIUS },  // 1 - top-right
    { x: CX + RING_RADIUS, y: CY - 30 },  // 2 - right-top
    { x: CX + RING_RADIUS, y: CY + 30 },  // 3 - right-bottom
    { x: CX + 30, y: CY + RING_RADIUS },  // 4 - bottom-right
    { x: CX - 30, y: CY + RING_RADIUS },  // 5 - bottom-left
    { x: CX - RING_RADIUS, y: CY + 30 },  // 6 - left-bottom
    { x: CX - RING_RADIUS, y: CY - 30 },  // 7 - left-top
];

const NET_LABELS = ['0', '1', '2', '3', '4', '5', '6', '7'];

const SwitchMatrixEditor: React.FC = () => {
    const { selectedMatrix, selectMatrix, switchMatrices, saveMatrixConnections, drivers, hasDriver, setDriver, removeDriver } = useSimulator();

    const [localConnections, setLocalConnections] = useState<number[][]>([]);
    const [selectedNode, setSelectedNode] = useState<number | null>(null);

    useEffect(() => {
        if (selectedMatrix) {
            setLocalConnections(selectedMatrix.connections.map(row => [...row]));
            setSelectedNode(null);
        }
    }, [selectedMatrix]);

    if (!selectedMatrix) return null;

    const matrixIndex = switchMatrices.indexOf(selectedMatrix);
    const { possibleConnections } = selectedMatrix;
    

    const handleNodeClick = (index: number) => {
        if (selectedNode === null) {
            setSelectedNode(index);
        } else if (selectedNode === index) {
            setSelectedNode(null);
        } else {
            const n1 = selectedMatrix.nets[selectedNode];
            const n2 = selectedMatrix.nets[index];
            
            // Toggle connection between selectedNode and index
            if (possibleConnections[selectedNode][index]) {
                let localDriver = null;
                if (!localConnections[selectedNode][index] && !localConnections[index][selectedNode]) {
                    console.log("Creating Connection")
                    if (hasDriver(n1.id)) {
                        if (hasDriver(n2.id)) {
                            alert(`Cannot connect net ${n1.id} to ${n2.id} because both have drivers. Please remove one driver first.`);
                            return;
                        }
                        
                        setDriver(n1.id, n2.id);
                        localDriver = n1.id;
                    } else {
                        if (hasDriver(n2.id)) {
                            setDriver(n2.id, n1.id);
                            localDriver = n2.id;
                        } else {
                            alert(`No drivers on either net. Please set a driver on one of them before connecting.`)
                            return;
                        }
                    }
                } else {
                    if (localConnections[index][selectedNode]) {
                        console.log(`Removing Connection - driver = ${n2.id}`)
                        removeDriver(n1.id);
                        localDriver = n2.id;
                    }

                    if (localConnections[selectedNode][index]) {
                        console.log(`Removing Connection - driver = ${n1.id}`)
                        console.log("Removing Connection")
                        removeDriver(n2.id);
                        localDriver = n1.id;
                    }
                }

                setLocalConnections(prev => prev.map((r, i) =>
                    i === (localDriver == n1.id ? selectedNode : index) ? r.map((c, j) => j === (localDriver == n2.id ? selectedNode : index) ? (c ? 0 : 1) : c) : [...r]
                ));
            }
            setSelectedNode(null);
        }
    };

    const handleSave = () => {
        saveMatrixConnections(matrixIndex, localConnections);
        selectMatrix(null);
    };

    const handleCancel = () => {
        selectMatrix(null);
    };

    // Collect all active connection lines (avoid drawing duplicates)
    const connectionLines: { from: number; to: number }[] = [];
    for (let i = 0; i < 8; i++) {
        for (let j = i + 1; j < 8; j++) {
            if (localConnections[i]?.[j] || localConnections[j]?.[i]) {
                connectionLines.push({ from: i, to: j });
            }
        }
    }

    return (
        <div style={{
            position: 'fixed',
            top: 0, left: 0, right: 0, bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'rgba(0,0,0,0.4)',
            zIndex: 1000,
        }} onClick={handleCancel}>
            <div style={{
                background: '#fff',
                borderRadius: 12,
                padding: 24,
                boxShadow: '0 8px 32px rgba(0,0,0,0.25)',
            }} onClick={e => e.stopPropagation()}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <h3 style={{ margin: 0 }}>{selectedMatrix.id}</h3>
                    <button onClick={handleCancel} style={{
                        background: 'none', border: 'none', fontSize: 20, cursor: 'pointer',
                    }}>&times;</button>
                </div>

                <svg width={SVG_SIZE} height={SVG_SIZE}>
                    {/* Active connection lines */}
                    {connectionLines.map(({ from, to }) => (
                        <line
                            key={`conn-${from}-${to}`}
                            x1={NODE_POSITIONS[from].x} y1={NODE_POSITIONS[from].y}
                            x2={NODE_POSITIONS[to].x} y2={NODE_POSITIONS[to].y}
                            stroke="#2196F3" strokeWidth={3}
                            pointerEvents="none"
                        />
                    ))}

                    {/* Possible-connection hints when a node is selected */}
                    {selectedNode !== null && Array.from({ length: 8 }, (_, j) => j)
                        .filter(j => {
                            if (j === selectedNode) return false;
                            if (!possibleConnections[selectedNode][j]) return false;
                            const netJ = selectedMatrix.nets?.[j] ?? null;
                            const connectedJ = !!netJ && netJ.id.split('.')?.[1] !== 'dummy';
                            return connectedJ;
                        })
                        .map(j => (
                            <line
                                key={`hint-${j}`}
                                x1={NODE_POSITIONS[selectedNode].x} y1={NODE_POSITIONS[selectedNode].y}
                                x2={NODE_POSITIONS[j].x} y2={NODE_POSITIONS[j].y}
                                stroke="#ccc" strokeWidth={2} strokeDasharray="6 4"
                                pointerEvents="none"
                            />
                        ))
                    }

                    {/* Nodes */}
                    {NODE_POSITIONS.map((pos, i) => {
                        const isSelected = selectedNode === i;
                        const isTarget = selectedNode !== null && selectedNode !== i && possibleConnections[selectedNode][i];
                        const hasConnection = localConnections[i]?.some((c, j) => c && j !== i) ||
                            localConnections.some((row, j) => j !== i && row[i]);

                        const net = selectedMatrix.nets?.[i] ?? null;
                        const isConnected = !!net && net.id.split('.')?.[1] !== 'dummy';

                        // Visual defaults for disconnected nodes
                        let fill = '#fff';
                        let stroke = '#333';
                        let cursorStyle: React.CSSProperties['cursor'] = 'pointer';
                        let labelColor = isSelected ? '#fff' : '#333';

                        if (!isConnected) {
                            // Grey out and disable selection
                            fill = '#f3f4f6';
                            stroke = '#cbd5e1';
                            cursorStyle = 'not-allowed';
                            labelColor = '#9ca3af';
                        } else if (isSelected) {
                            fill = '#2196F3'; stroke = '#1565C0'; labelColor = '#fff';
                        } else if (isTarget) {
                            fill = '#BBDEFB'; stroke = '#2196F3';
                        } else if (hasConnection) {
                            fill = '#E3F2FD'; stroke = '#333';
                        }

                        return (
                            <g key={`node-${i}`}
                                style={{ cursor: cursorStyle }}
                                onClick={() => isConnected && handleNodeClick(i)}
                            >
                                <circle
                                    cx={pos.x} cy={pos.y} r={NODE_RADIUS}
                                    fill={fill} stroke={stroke} strokeWidth={2}
                                />
                                <text
                                    x={pos.x} y={pos.y + 1}
                                    textAnchor="middle" dominantBaseline="central"
                                    fontSize={12} fontFamily="monospace" fontWeight="bold"
                                    fill={labelColor}
                                    pointerEvents="none"
                                >{NET_LABELS[i]}</text>
                            </g>
                        );
                    })}
                </svg>

                {selectedNode !== null && (
                    <p style={{ margin: '0 0 8px', fontSize: 13, color: '#666', textAlign: 'center' }}>
                        Click a highlighted node to toggle its connection to node {selectedNode}
                    </p>
                )}

                <div style={{ fontSize: 12, fontFamily: 'monospace', margin: '8px 0', padding: '8px', background: '#f5f5f5', borderRadius: 6 }}>
                    <div style={{ fontWeight: 'bold', marginBottom: 4, fontFamily: 'sans-serif', fontSize: 13 }}>Nets</div>
                    {Array.from({ length: 8 }).map((_, i) => {
                        const net = selectedMatrix.nets?.[i] ?? null;
                        return (
                            <div key={i} style={{ display: 'flex', gap: 8, color: net  && net.id.split('.')?.[1] !== 'dummy'  ? '#333' : '#aaa' }}>
                                <span>{i}:</span>
                                <span>{net && net.id.split('.')?.[1] !== 'dummy' ? net.id : '[ Disconnected ]'}</span>
                            </div>
                        );
                    })}
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
                    <button onClick={handleCancel} style={{
                        padding: '6px 16px', borderRadius: 6, border: '1px solid #ccc',
                        background: '#fff', cursor: 'pointer', fontSize: 14,
                    }}>Cancel</button>
                    <button onClick={handleSave} style={{
                        padding: '6px 16px', borderRadius: 6, border: 'none',
                        background: '#2196F3', color: '#fff', cursor: 'pointer', fontSize: 14,
                    }}>Save</button>
                </div>
            </div>
        </div>
    );
};

export default SwitchMatrixEditor;
