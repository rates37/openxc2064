import React from "react";
import { useContext, useState, useEffect, useRef, useCallback } from "react";
import { SimulatorContext, SimulatorContextType } from "./context/SimulatorContext";
import { LogicElement } from "./models/LogicElement";
import { LogicElementComponent } from "./components/LogicElementComponent";
import "./styles/LogicArray.css";
import { NodeComponent } from "./components/NodeComponent";
import { BusComponent } from "./components/BusComponent";
import { XC2064 } from "./constants";
import LogicElementModal from "./components/modals/LogicElementModal";
import SwitchMatrixModal from "./components/modals/SwitchMatrixModal";
import { SwitchMatrix } from "./models/SwitchMatrix";

const LogicArray: React.FC = () => {
    const context: SimulatorContextType = useContext(SimulatorContext);
    const [logicElementDisplay, setLogicElementDisplay] = useState<React.JSX.Element | null>(null);
    const [scale, setScale] = useState(1);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const [selectedElement, setSelectedElement] = useState<LogicElement | null>(null);
    const [selectedSwitchMatrix, setSelectedSwitchMatrix] = useState<SwitchMatrix | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isSwitchModalOpen, setIsSwitchModalOpen] = useState(false);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [viewportSize, setViewportSize] = useState({ width: 0, height: 0 });

    // Refs for global layers
    const bussesLayerRef = useRef<SVGGElement>(null);
    const switchesLayerRef = useRef<SVGGElement>(null);
    const nodesLayerRef = useRef<SVGGElement>(null);
    const [layersReady, setLayersReady] = useState(false);

    const handleLogicElementClick = useCallback((element: LogicElement) => {
        setSelectedElement(element);
        setIsModalOpen(true);
    }, []);

    const handleSwitchClick = useCallback((matrix: SwitchMatrix) => {
        // Check if matrix exists in context, if so use that one
        const existingMatrix = context.switchMatrices.find(m => m.id === matrix.id);
        setSelectedSwitchMatrix(existingMatrix || matrix);
        setIsSwitchModalOpen(true);
    }, [context.switchMatrices]);

    const handleSaveElement = (element: LogicElement) => {
        context.updateLogicElement(element);
    };

    const handleSaveSwitchMatrix = (matrix: SwitchMatrix) => {
        context.updateSwitchMatrix(matrix);
    };

    const viewportWidth = 2000;
    const viewportHeight = 2000;
    const OFFSET = 400;

    // Memoize the logic elements grid to prevent re-rendering on every pan/zoom
    // We only re-render if the actual logic elements data changes
    const logicElementsGrid = React.useMemo(() => {
        if (!layersReady) return []; // Wait for layers to be mounted

        return context.logicElements.map((logicElementRow, y) =>
            logicElementRow.map((logicElement, x) => {
                const elX = x * 190 + OFFSET;
                const elY = y * 190 + OFFSET;

                context.logicElements[y][x].x = elX;
                context.logicElements[y][x].y = elY;

                return (
                    <LogicElementComponent
                        key={`${y}-${x}`}
                        i={y}
                        j={x}
                        x={elX}
                        y={elY}
                        onClick={handleLogicElementClick}
                        onSwitchClick={handleSwitchClick}
                        bussesContainer={bussesLayerRef.current}
                        switchesContainer={switchesLayerRef.current}
                        nodesContainer={nodesLayerRef.current}
                    />
                );
            })
        );
    }, [handleLogicElementClick, handleSwitchClick, layersReady]); // Add layersReady dependency


    setTimeout(() => {
        setLogicElementDisplay(<>{logicElementsGrid}</>);
    }, 10);

    useEffect(() => {
        // Signal that the SVG layers are mounted and ready to receive portals
        if (bussesLayerRef.current && switchesLayerRef.current && nodesLayerRef.current) {
            setLayersReady(true);
        }
    }, []);

    useEffect(() => {
        if (containerRef.current) {
            setViewportSize({
                width: containerRef.current.clientWidth,
                height: containerRef.current.clientHeight
            });
        }
        
        const handleResize = () => {
            if (containerRef.current) {
                setViewportSize({
                    width: containerRef.current.clientWidth,
                    height: containerRef.current.clientHeight
                });
            }
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    useEffect(() => {
        if (canvasRef.current) {
            context.setCanvas(canvasRef.current);
        }

        console.log("LogicArray useEffect - context", context);
    }, []);

    useEffect(() => {
        const container = containerRef.current;
        if (container) {
            const onWheel = (e: WheelEvent) => {
                e.preventDefault();
            };
            container.addEventListener("wheel", onWheel, { passive: false });
            return () => {
                container.removeEventListener("wheel", onWheel);
            };
        }
    }, []);

    const handleMouseDown = (e: React.MouseEvent) => {
        setIsDragging(true);
    };

    const handleMouseUp = () => {
        setIsDragging(false);
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        if (isDragging) {
            setPosition((prev) => ({
                x: prev.x + e.movementX,
                y: prev.y + e.movementY,
            }));
        }
    };

    const handleWheel = (e: React.WheelEvent) => {
        const scaleAmount = -e.deltaY * 0.001;
        const newScale = Math.max(0.1, Math.min(scale + scaleAmount, 5));

        if (containerRef.current) {
            const rect = containerRef.current.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const mouseX = (x - position.x) / scale;
            const mouseY = (y - position.y) / scale;

            const newX = x - mouseX * newScale;
            const newY = y - mouseY * newScale;

            setPosition({ x: newX, y: newY });
            setScale(newScale);
        }
    };

    return (
        <>
            <button onClick={() => {
                const timeBefore = performance.now();
                context.simulate();
                const timeAfter = performance.now();
                console.log(`Simulation took ${timeAfter - timeBefore} milliseconds`);
            }}>Simulate</button>
            <div
                className="LogicArrayViewport"
                ref={containerRef}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                onWheel={handleWheel}
                onContextMenu={(e) => e.preventDefault()}
            >
                <div style={{
                    transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
                    transformOrigin: '0 0',
                    width: viewportWidth,
                    height: viewportHeight,
                    position: 'absolute'
                }}>
                    <svg
                        className="LogicArray"
                        width={viewportWidth}
                        height={viewportHeight}
                        style={{ position: 'absolute', top: 0, left: 0, userSelect: 'none' }}
                    >
                        {/* Global Layers for Stacking Order */}
                        <g ref={bussesLayerRef} id="global-busses-layer" style={{ outline: 'none' }} />
                        <g ref={switchesLayerRef} id="global-switches-layer" style={{ outline: 'none' }} />
                        
                        {/* Logic Elements (Rects) are rendered here directly */}
                        {logicElementDisplay}

                        <g ref={nodesLayerRef} id="global-nodes-layer" style={{ outline: 'none' }} />
                    </svg>
                    <canvas
                        ref={canvasRef}
                        width={viewportWidth}
                        height={viewportHeight}
                        style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
                    />
                </div>
            </div>

            <LogicElementModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                element={selectedElement}
                onSave={handleSaveElement}
            />

            <SwitchMatrixModal
                isOpen={isSwitchModalOpen}
                onClose={() => setIsSwitchModalOpen(false)}
                element={selectedSwitchMatrix}
                onSave={handleSaveSwitchMatrix}
            />
        </>
    );
};

export default LogicArray;
