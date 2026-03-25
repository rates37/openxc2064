import React, { useRef, useState, useCallback, useEffect } from "react";
import { useSimulator } from "../SimulatorContext";
import { CELL_WIDTH, CELL_HEIGHT, PIP_WIDTH, PIP_HEIGHT, MATRIX_WIDTH, MATRIX_HEIGHT, IO_WIDTH, IO_HEIGHT } from "../configs/constants";

import { LogicCell } from "../models/LogicCell";
import { SwitchMatrix } from "../models/SwitchMatrix";
import { IOBank, IOPad } from "../models/IOBank";
import { Net, Pip } from "../types";

// Initial view position
const INITIAL_VIEW = { x: -3500, y: -100, w: 7000, h: 5000 };

// Matrix mini-node offsets
const R = MATRIX_WIDTH / 2 - 2;
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

// --- Canvas drawing functions ---

function drawLineSegment(
    ctx: CanvasRenderingContext2D,
    baseX: number,
    baseY: number,
    points: { x: number; y: number; continuous?: boolean }[],
    value: boolean,
    colour?: string,
    overrideColour?: string
) {
    if (points.length < 2) return;
    if (overrideColour) ctx.strokeStyle = overrideColour;
    else ctx.strokeStyle = value ? "#ff0000" : colour || "#333";
    ctx.lineWidth = 4;
    ctx.lineCap = "round";

    for (let i = 1; i < points.length; i++) {
        if (points[i].continuous === false) continue;
        ctx.beginPath();
        ctx.moveTo(points[i - 1].x + baseX, points[i - 1].y + baseY);
        ctx.lineTo(points[i].x + baseX, points[i].y + baseY);
        ctx.stroke();
    }
}

function drawGrid(ctx: CanvasRenderingContext2D, viewBox: { x: number; y: number; w: number; h: number }) {
    const gridSize = 20;
    ctx.strokeStyle = "#7e7e7e";
    ctx.lineWidth = 0.5;

    const startX = Math.floor(viewBox.x / gridSize) * gridSize;
    const startY = Math.floor(viewBox.y / gridSize) * gridSize;
    const endX = viewBox.x + viewBox.w;
    const endY = viewBox.y + viewBox.h;

    ctx.beginPath();
    for (let x = startX; x <= endX; x += gridSize) {
        ctx.moveTo(x, viewBox.y);
        ctx.lineTo(x, endY);
    }
    for (let y = startY; y <= endY; y += gridSize) {
        ctx.moveTo(viewBox.x, y);
        ctx.lineTo(endX, y);
    }
    ctx.stroke();
}

function drawCell(ctx: CanvasRenderingContext2D, cell: LogicCell, highlightId?: string | null) {
    const { x, y } = cell.pos;
    const cx = x + CELL_WIDTH / 2;
    const cy = y + CELL_HEIGHT / 2;

    // Draw nets
    for (const net of cell.nets) {
        if (net.points.length > 0) {
            const fullId = `${cell.id}.${net.id}`;
            const override = fullId === highlightId ? "purple" : undefined;
            drawLineSegment(ctx, cx, cy, net.points, net.value, undefined, override);
        }
    }

    // Draw cell rectangle
    ctx.fillStyle = "#fff";
    ctx.strokeStyle = "#333";
    ctx.lineWidth = 8;
    ctx.beginPath();
    ctx.roundRect(x, y, CELL_WIDTH, CELL_HEIGHT, 5);
    ctx.fill();
    ctx.stroke();

    // Draw cell ID
    ctx.fillStyle = "#000";
    ctx.font = "48px Computer Modern, Latin Modern, STIXGeneral, Times New Roman, serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(cell.id, cx, cy);

    // Draw port labels
    ctx.fillStyle = "#666";
    ctx.font = "24px Computer Modern, Latin Modern, STIXGeneral, Times New Roman, serif";
    ctx.fillText("A", cx + 60, cy - 135);
    ctx.fillText("B", cx - 80, cy - 38);
    ctx.fillText("C", cx - 80, cy + 23);
    ctx.fillText("D", cx, y + CELL_HEIGHT - 18);
    ctx.fillText("X", cx + 80, cy + 23);
    ctx.fillText("Y", cx + 80, cy + 102);
    ctx.fillText("K", cx - 80, cy + 83);
}

function drawMatrixBox(ctx: CanvasRenderingContext2D, matrix: SwitchMatrix, highlightId?: string | null) {
    const { x, y } = matrix.pos;
    const cx = x + MATRIX_WIDTH / 2;
    const cy = y + MATRIX_HEIGHT / 2;

    // Draw matrix rectangle
    ctx.fillStyle = "#fff";
    ctx.strokeStyle = "#333";
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.roundRect(x, y, MATRIX_WIDTH, MATRIX_HEIGHT, 5);
    ctx.fill();
    ctx.stroke();

    // Draw connection lines
    const lines: { from: number; to: number }[] = [];
    for (let i = 0; i < 8; i++) {
        for (let j = i + 1; j < 8; j++) {
            if (matrix.connections[i]?.[j] || matrix.connections[j]?.[i]) {
                lines.push({ from: i, to: j });
            }
        }
    }

    ctx.strokeStyle = "#55848a";
    ctx.lineWidth = 3;
    for (const { from, to } of lines) {
        ctx.beginPath();
        ctx.moveTo(cx + miniNodeOffsets[from].dx, cy + miniNodeOffsets[from].dy);
        ctx.lineTo(cx + miniNodeOffsets[to].dx, cy + miniNodeOffsets[to].dy);
        ctx.stroke();
    }
    
    // Draw matrix rectangle
    ctx.fillStyle = "#fff";
    ctx.strokeStyle = "#333";
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.roundRect(x, y, MATRIX_WIDTH, MATRIX_HEIGHT, 5);
    ctx.stroke();


    // // Draw mini nodes
    // ctx.fillStyle = "#333";
    // for (const off of miniNodeOffsets) {
    //     ctx.beginPath();
    //     ctx.arc(cx + off.dx, cy + off.dy, 2, 0, Math.PI * 2);
    //     ctx.fill();
    // }
}

function drawMatrixNets(ctx: CanvasRenderingContext2D, matrix: SwitchMatrix, highlightId?: string | null) {
    const { x, y } = matrix.pos;
    const cx = x + MATRIX_WIDTH / 2;
    const cy = y + MATRIX_HEIGHT / 2;

    
    
    // Draw nets
    for (let i = 0; i < Math.min(4, matrix.nets.length); i++) {
        const net = matrix.nets[i];
        if (net && net.points.length > 0) {
            const override = net.id === highlightId ? "purple" : undefined;
            drawLineSegment(ctx, cx, cy, net.points, net.value, "rgb(199, 199, 199)", override);
        }
    }

}

function drawPip(ctx: CanvasRenderingContext2D, pip: Pip) {
    const { x, y } = pip.pos;
    ctx.fillStyle = pip.enabled ? "#696969" : "#ffffff";
    ctx.strokeStyle = pip.bidirectional ? "rgb(167, 167, 167)" : "rgb(94, 94, 94)";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.rect(x - PIP_WIDTH / 2, y - PIP_HEIGHT / 2, PIP_WIDTH, PIP_HEIGHT);
    ctx.fill();
    ctx.stroke();
}

function drawIOBank(ctx: CanvasRenderingContext2D, bank: IOBank, highlightId?: string | null) {
    const { x, y } = bank.pos;
    const netO = bank.nets.find((n) => n.id === `${bank.id}.net_I`);
    const isActive = netO?.value ?? false;

    // Draw IO bank rectangle
    ctx.fillStyle = "#fff";
    ctx.strokeStyle = isActive ? "#f00" : "#333";
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.roundRect(x, y, bank.size.width, bank.size.height, 5);
    ctx.fill();
    ctx.stroke();

    // Draw Bank ID
    const cx = x + bank.size.width / 2;
    const cy = y + bank.size.height / 2;
    ctx.fillStyle = "#000";
    ctx.font = "30px Computer Modern, Latin Modern, STIXGeneral, Times New Roman, serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(bank.id, cx, cy);

    // Draw nets
    for (const net of bank.nets) {
        if (net.points.length > 0) {
            const override = net.id === highlightId ? "purple" : undefined;
            drawLineSegment(ctx, x + IO_WIDTH / 2, y + IO_HEIGHT / 2, net.points, net.value, "#333", override);
        }
    }
}

function drawIOPad(ctx: CanvasRenderingContext2D, bank: IOBank, highlightId?: string | null) {
    const pad = bank.pad;

    if (!pad) return;

    const { x, y } = { x: pad.pos.x + bank.pos.x, y: pad.pos.y + bank.pos.y };
    const netO = bank.nets.find((n) => n.id === `${bank.id}.net_pad`);
    const isActive = netO?.value ?? false;

    // Draw IO bank rectangle
    ctx.fillStyle = isActive ? "rgb(255, 112, 112)" : "#fff";
    ctx.strokeStyle = isActive ? "#f00" : "#333";
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.roundRect(x, y, pad.size.width, pad.size.height, 5);
    ctx.fill();
    ctx.stroke();

}

function drawBusNet(ctx: CanvasRenderingContext2D, net: Net, highlightId?: string | null) {
    if (net.points.length < 2) return;
    const isActive = net.value;

    // console.log(`Drawing bus net ${net.id} with value ${net.value} and points:`, net.points);
    const override = net.id === highlightId ? "purple" : undefined;
    drawLineSegment(ctx, 0, 0, net.points, net.value, "rgba(199, 199, 199, 1)", override);
}

// --- Main component ---

const SimulationCanvas: React.FC = () => {
    const {
        logicCells,
        switchMatrices,
        pips,
        ioBanks,
        busNets,
        showGrid,
        togglePip,
        selectMatrix,
        selectCell,
        toggleIONet,
        simulate,
        tick,
        drivers,
        hasDriver,
        setDriver,
        removeDriver,
        searchQuery,
        selectIOBank,
    } = useSimulator();
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [viewBox, setViewBox] = useState(INITIAL_VIEW);
    const [isPanning, setIsPanning] = useState(false);
    const panStart = useRef({ x: 0, y: 0 });
    const [canvasSize, setCanvasSize] = useState({ width: 800, height: 600, cssWidth: 800, cssHeight: 600 });

    // Update canvas size on resize
    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;

        const updateSize = () => {
            const { clientWidth, clientHeight } = el;
            const dpr = window.devicePixelRatio || 1;
            setCanvasSize({
                width: Math.round(clientWidth * dpr),
                height: Math.round(clientHeight * dpr),
                cssWidth: clientWidth,
                cssHeight: clientHeight,
            });
            // Adjust viewBox to maintain aspect ratio
            const aspect = clientWidth / clientHeight;
            setViewBox((v) => ({ ...v, w: v.h * aspect }));
        };

        updateSize();
        const resizeObserver = new ResizeObserver(updateSize);
        resizeObserver.observe(el);
        return () => resizeObserver.disconnect();
    }, []);

    // Use a ref to track the latest viewBox for event handlers
    const viewBoxRef = useRef(viewBox);
    viewBoxRef.current = viewBox;

    // Convert screen coordinates to world coordinates
    const screenToWorld = useCallback((screenX: number, screenY: number) => {
        const canvas = canvasRef.current;
        if (!canvas) return { x: 0, y: 0 };
        const rect = canvas.getBoundingClientRect();
        const vb = viewBoxRef.current;
        const x = vb.x + ((screenX - rect.left) / rect.width) * vb.w;
        const y = vb.y + ((screenY - rect.top) / rect.height) * vb.h;
        return { x, y };
    }, []);

    // Handle panning
    const onPointerDown = useCallback((e: React.PointerEvent) => {
        setIsPanning(true);
        panStart.current = { x: e.clientX, y: e.clientY };
        (e.target as Element).setPointerCapture(e.pointerId);
    }, []);

    const onPointerMove = useCallback(
        (e: React.PointerEvent) => {
            if (!isPanning) return;
            const canvas = canvasRef.current;
            if (!canvas) return;
            const rect = canvas.getBoundingClientRect();
            const vb = viewBoxRef.current;
            const scaleX = vb.w / rect.width;
            const scaleY = vb.h / rect.height;
            const dx = (e.clientX - panStart.current.x) * scaleX;
            const dy = (e.clientY - panStart.current.y) * scaleY;
            panStart.current = { x: e.clientX, y: e.clientY };
            setViewBox((v) => ({ ...v, x: v.x - dx, y: v.y - dy }));
        },
        [isPanning]
    );

    const onPointerUp = useCallback(() => {
        setIsPanning(false);
    }, []);

    // Handle zooming
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const handleWheel = (e: WheelEvent) => {
            e.preventDefault();
            const scale = e.deltaY > 0 ? 1.1 : 0.9;
            const world = screenToWorld(e.clientX, e.clientY);
            const vb = viewBoxRef.current;
            const newW = vb.w * scale;
            const newH = vb.h * scale;
            setViewBox({
                x: world.x - (world.x - vb.x) * scale,
                y: world.y - (world.y - vb.y) * scale,
                w: newW,
                h: newH,
            });
        };

        canvas.addEventListener("wheel", handleWheel, { passive: false });
        return () => canvas.removeEventListener("wheel", handleWheel);
    }, [screenToWorld]);

    // Handle click events for interaction
    const onClick = useCallback(
        (e: React.MouseEvent) => {
            const world = screenToWorld(e.clientX, e.clientY);

            // Check PIPs first (smallest clickable area)
            for (let i = 0; i < pips.length; i++) {
                const pip = pips[i];
                if (
                    world.x >= pip.pos.x - PIP_WIDTH / 2 &&
                    world.x <= pip.pos.x + PIP_WIDTH / 2 &&
                    world.y >= pip.pos.y - PIP_HEIGHT / 2 &&
                    world.y <= pip.pos.y + PIP_HEIGHT / 2
                ) {
                    if (pip.bidirectional) {
                        const srcDriver = hasDriver(pip.source);
                        const dstDriver = hasDriver(pip.destination);

                        if (!pip.enabled && !srcDriver && !dstDriver) {
                            alert(`Failed to toggle pip. Both ${pip.source} and ${pip.destination} have no driver.`);
                            return;
                        }

                        if (!pip.enabled && srcDriver && dstDriver) {
                            alert(`Failed to toggle pip. Both ${pip.source} and ${pip.destination} already have drivers.`);
                            return;
                        }

                        if (!pip.enabled) {
                            if (srcDriver) {
                                setDriver(pip.source, pip.destination);
                            } else {
                                setDriver(pip.destination, pip.source);
                            }
                        } else {
                            if (srcDriver && drivers.find(d => d.destination === pip.source).source === pip.destination) {
                                removeDriver(pip.source);
                            }

                            if (dstDriver && drivers.find(d => d.destination === pip.destination).source === pip.source) {
                                removeDriver(pip.destination);
                            }
                        }

                    } else {
                        if (!pip.enabled && hasDriver(pip.destination)) {
                            alert(`Cannot enable PIP ${pip.id} because destination (${pip.destination}) net already has a driver.`);
                            return;
                        }

                        pip.enabled ? removeDriver(pip.destination) : setDriver(pip.source, pip.destination);
                    }

                    togglePip(i);

                    return;
                }
            }

            // Check IO banks - open modal instead of toggling net
            for (let i = 0; i < ioBanks.length; i++) {
                const bank = ioBanks[i];
                if (
                    world.x >= bank.pos.x &&
                    world.x <= bank.pos.x + bank.size.width &&
                    world.y >= bank.pos.y &&
                    world.y <= bank.pos.y + bank.size.height
                ) {
                    // open the IO bank modal for editing
                    selectIOBank(bank);
                    return;
                }

                const pad = bank.pad;
                if (
                    pad &&
                    world.x >= bank.pos.x + pad.pos.x &&
                    world.x <= bank.pos.x + pad.pos.x + pad.size.width &&
                    world.y >= bank.pos.y + pad.pos.y &&
                    world.y <= bank.pos.y + pad.pos.y + pad.size.height
                ) {
                    // open the IO bank modal for editing
                    toggleIONet(i);
                    return;
                }
            }


            // Check switch matrices
            for (const matrix of switchMatrices) {
                if (
                    world.x >= matrix.pos.x &&
                    world.x <= matrix.pos.x + MATRIX_WIDTH &&
                    world.y >= matrix.pos.y &&
                    world.y <= matrix.pos.y + MATRIX_HEIGHT
                ) {
                    selectMatrix(matrix);
                    return;
                }
            }

            // Check logic cells
            for (const cell of logicCells) {
                if (
                    world.x >= cell.pos.x &&
                    world.x <= cell.pos.x + CELL_WIDTH &&
                    world.y >= cell.pos.y &&
                    world.y <= cell.pos.y + CELL_HEIGHT
                ) {
                    selectCell(cell);
                    return;
                }
            }
        },
        [screenToWorld, pips, ioBanks, switchMatrices, logicCells, togglePip, toggleIONet, simulate, selectMatrix, selectCell, hasDriver, setDriver, removeDriver, drivers]
    );

    // Render the canvas
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        // Set canvas size for device pixel ratio
        const dpr = window.devicePixelRatio || 1;
        canvas.width = canvasSize.width;
        canvas.height = canvasSize.height;
        canvas.style.width = `${canvasSize.cssWidth}px`;
        canvas.style.height = `${canvasSize.cssHeight}px`;

        // Enable anti-aliasing for smooth rendering when zoomed out
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = "high";

        // Clear canvas
        ctx.fillStyle = "#fff";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Set up transform: scale and translate to show viewBox
        ctx.save();
        const scaleX = canvas.width / viewBox.w;
        const scaleY = canvas.height / viewBox.h;
        ctx.scale(scaleX, scaleY);
        ctx.translate(-viewBox.x, -viewBox.y);

        // Draw grid
        if (showGrid) {
            drawGrid(ctx, viewBox);
        }

        // Draw bus nets
        for (const net of busNets) {
            drawBusNet(ctx, net, searchQuery);
        }

        // Draw switch matrices
        for (const matrix of switchMatrices) {
            drawMatrixNets(ctx, matrix, searchQuery);
        }
        for (const matrix of switchMatrices) {
            drawMatrixBox(ctx, matrix, searchQuery);
        }

        // Draw logic cells
        for (const cell of logicCells) {
            drawCell(ctx, cell, searchQuery);
        }

        // Draw IO banks
        for (const bank of ioBanks) {
            drawIOBank(ctx, bank, searchQuery);
            drawIOPad(ctx, bank, searchQuery);
        }

        // Draw PIPs
        for (const pip of pips) {
            drawPip(ctx, pip);
        }


        ctx.restore();
    }, [viewBox, showGrid, logicCells, switchMatrices, pips, ioBanks, busNets, tick, canvasSize, searchQuery]);

    return (
        <div
            ref={containerRef}
            style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                height: "calc(100vh - 50px)",
                width: "100%",
            }}
        >
            <canvas
                ref={canvasRef}
                style={{
                    border: "1px solid #ccc",
                    borderRadius: "8px",
                    boxShadow: "0 0 6px rgba(0, 0, 0, 0.08)",
                    cursor: isPanning ? "grabbing" : "grab",
                    touchAction: "none",
                    width: `${canvasSize.cssWidth}px`,
                    height: `${canvasSize.cssHeight}px`,
                }}
                onPointerDown={onPointerDown}
                onPointerMove={onPointerMove}
                onPointerUp={onPointerUp}
                onPointerLeave={onPointerUp}
                onClick={onClick}
            />
        </div>
    );
};

export default SimulationCanvas;

