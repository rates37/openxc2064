import React, { useState, useEffect } from "react";
import "../../styles/Modal.css";
import "../../styles/SwitchMatrixModal.css";
import { SwitchMatrix } from "../../models/SwitchMatrix";

type SwitchMatrixModalProps = {
    isOpen: boolean;
    onClose: () => void;
    element: SwitchMatrix | null;
    onSave: (element: SwitchMatrix) => void;
};

const SwitchMatrixModal: React.FC<SwitchMatrixModalProps> = ({ isOpen, onClose, element, onSave }) => {
    const [connections, setConnections] = useState<(0 | 1)[][]>([]);

    useEffect(() => {
        if (element) {
            setConnections(element.connections);
        }
    }, [element]);

    if (!isOpen || !element) return null;

    const handleToggle = (row: number, col: number) => {
        if (element.possibleConnections[row][col] === 0) return; // Cannot toggle if not possible

        const newConnections = connections.map((r, rIndex) =>
            r.map((val, cIndex) => (rIndex === row && cIndex === col ? (val === 0 ? 1 : 0) : val))
        );
        setConnections(newConnections);
        element.updateConnections(newConnections);
    };

    const handleSave = () => {
        onSave(element);
        onClose();
    };

    return (
        <div className="modal-overlay switch-matrix-overlay">
            <div className="modal-content switch-matrix-content">
                <h2>Switch Matrix: {element.id}</h2>
                
                <div className="switch-matrix-container">
                    {/* Header Row */}
                    <div className="switch-matrix-header-cell"></div>
                    {[0, 1, 2, 3, 4, 5, 6, 7].map(col => (
                        <div key={`h-${col}`} className="switch-matrix-header-cell">{col}</div>
                    ))}

                    {/* Grid Rows */}
                    {connections.map((row, rowIndex) => (
                        <React.Fragment key={`row-${rowIndex}`}>
                            <div className="switch-matrix-row-label">{rowIndex}</div>
                            {row.map((val, colIndex) => {
                                const isPossible = element.possibleConnections[rowIndex][colIndex] === 1;
                                return (
                                    <button
                                        key={`${rowIndex}-${colIndex}`}
                                        className={`switch-matrix-cell ${val === 1 ? "active" : ""} ${!isPossible ? "disabled" : ""}`}
                                        onClick={() => handleToggle(rowIndex, colIndex)}
                                        disabled={!isPossible}
                                        title={isPossible ? `Toggle connection ${rowIndex}-${colIndex}` : "Connection not available"}
                                    />
                                );
                            })}
                        </React.Fragment>
                    ))}
                </div>

                <div className="modal-actions">
                    <button onClick={handleSave}>Save</button>
                    <button onClick={onClose}>Cancel</button>
                </div>
            </div>
        </div>
    );
};

export default SwitchMatrixModal;