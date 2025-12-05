import React from "react";
import { useContext, useState, useEffect, useRef } from "react";
import { SimulatorContext, SimulatorContextType } from "./context/SimulatorContext";
import { LogicElement } from "./models/LogicElement";
import { LogicElementComponent } from "./components/LogicElementComponent";
import "./styles/LogicArray.css";
import { NodeComponent } from "./components/NodeComponent";
import { BusComponent } from "./components/BusComponent";
import { XC2064 } from "./constants";
import LogicElementModal from "./components/modals/LogicElementModal";

const LogicArray: React.FC = () => {
    const context: SimulatorContextType = useContext(SimulatorContext);
    const [logicElementDisplay, setLogicElementDisplay] = useState<React.JSX.Element | null>(null);
    const [scale, setScale] = useState(1);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const [selectedElement, setSelectedElement] = useState<LogicElement | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const handleLogicElementClick = (element: LogicElement) => {
        setSelectedElement(element);
        setIsModalOpen(true);
    };

    const handleSaveElement = (element: LogicElement) => {
        context.updateLogicElement(element);
    };

    setTimeout(() => {
        const elements = context.logicElements.map((logicElementRow, y) =>
            logicElementRow.map((logicElement, x) => (
                <LogicElementComponent
                    key={`${y}-${x}`}
                    i={y}
                    j={x}
                    x={x * 190}
                    y={y * 190}
                    onClick={handleLogicElementClick}
                />
            ))
        );

        setLogicElementDisplay(<>{elements}</>);
    }, 100);

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

            const ratio = newScale / scale;

            setPosition((prev) => ({
                x: x - (x - prev.x) * ratio,
                y: y - (y - prev.y) * ratio,
            }));

            setScale(newScale);
        }
    };

    const viewportWidth = 2000;
    const viewportHeight = 2000;

    return (
        <>
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
                <svg
                    className="LogicArray"
                    width={viewportWidth}
                    height={viewportHeight}
                    style={{
                        transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
                    }}
                >
                    {logicElementDisplay}
                </svg>
            </div>

            <LogicElementModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                element={selectedElement}
                onSave={handleSaveElement}
            />
        </>
    );
};

export default LogicArray;
