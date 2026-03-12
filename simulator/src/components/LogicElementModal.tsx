import React from "react";
import "../styles/Modal.css";
import { LogicCell } from "../models/LogicCell";
import { Mux, Wire, Lut, Label, FlipFlop, ConnectionDot, EllipseNode, InputButton } from "./LogicElementPrimitives";
import { useSimulator } from "../SimulatorContext";

const LogicElementModal: React.FC = () => {
    const { selectedCell, selectCell, logicCells, setLogicCells } = useSimulator();

    const [muxConfig, setMuxConfig] = React.useState<Record<string, number>>({});
    const [lutConfig, setLutConfig] = React.useState<Record<string, number[]>>({});
    const [inputs, setInputs] = React.useState<Record<string, 0 | 1>>({ A: 0, B: 0, C: 0, D: 0, K: 0 });
    const [nets, setNets] = React.useState<Record<string, number>>({});
    const [mousePos, setMousePos] = React.useState({ x: 0, y: 0 });
    const [highlightedNode, setHighlightedNode] = React.useState<string | null>(null);

    // Sync local state when selectedCell changes
    React.useEffect(() => {
        if (!selectedCell) return;
        setMuxConfig(Object.fromEntries(selectedCell.muxes.map(m => [m.id, m.select])));
        setLutConfig(Object.fromEntries(selectedCell.luts.map(l => [l.id, l.truthTable.map(b => b ? 1 : 0)])));
        // Derive inputs from cell nets
        const inputKeys = ["A", "B", "C", "D", "K"];
        const inputState: Record<string, 0 | 1> = {};
        for (const key of inputKeys) {
            const net = selectedCell.nets.find(n => n.id === `net_${key}`);
            inputState[key] = net?.value ? 1 : 0;
        }
        setInputs(inputState);
        refreshNets(selectedCell);
    }, [selectedCell]);

    if (!selectedCell) return null;

    const refreshNets = (cell: LogicCell) => {
        const netMap: Record<string, number> = {};
        for (const net of cell.nets) {
            netMap[net.id] = net.value ? 1 : 0;
        }
        setNets(netMap);
    };

    const applyAndSimulate = (cell: LogicCell) => {
        cell.simulate();
        refreshNets(cell);
        setLogicCells([...logicCells]);
    };

    const handleMouseMove = (e: React.MouseEvent<SVGSVGElement, MouseEvent>) => {
        const svg = e.currentTarget;
        const pt = svg.createSVGPoint();
        pt.x = e.clientX;
        pt.y = e.clientY;
        const svgP = pt.matrixTransform(svg.getScreenCTM()?.inverse());
        setMousePos({ x: Math.round(svgP.x), y: Math.round(svgP.y) });
    };

    const handleMuxClick = (muxId: string, numInputs: number) => {
        const currentSelection = muxConfig[muxId] || 0;
        const nextSelection = (currentSelection + 1) % numInputs;
        const newConfig = { ...muxConfig, [muxId]: nextSelection };
        setMuxConfig(newConfig);

        // Push to model
        const mux = selectedCell.muxes.find(m => m.id === muxId);
        if (mux) mux.select = nextSelection;

        applyAndSimulate(selectedCell);
    };

    const handleLutChange = (lutId: string, index: number) => {
        const currentConfig = lutConfig[lutId] || Array(8).fill(0);
        const newConfig = [...currentConfig];
        newConfig[index] = newConfig[index] === 0 ? 1 : 0;
        const newLutConfig = { ...lutConfig, [lutId]: newConfig };
        setLutConfig(newLutConfig);

        // Push to model
        const lut = selectedCell.luts.find(l => l.id === lutId);
        if (lut) lut.truthTable[index] = !lut.truthTable[index];

        applyAndSimulate(selectedCell);
    };

    const handleInputChange = (key: string, value: 0 | 1) => {
        const newInputs = { ...inputs, [key]: value };
        setInputs(newInputs);

        // Push to model net
        const net = selectedCell.nets.find(n => n.id === `net_${key}`);
        if (net) net.value = value === 1;

        applyAndSimulate(selectedCell);
    };

    const handleMouseEnter = (id: string) => setHighlightedNode(id);
    const handleMouseLeave = () => setHighlightedNode(null);

    const handleClose = () => selectCell(null);

    return (
        <div className="modal-overlay" onClick={handleClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>{selectedCell.id} &mdash; Logic Element</h2>
                    <button className="modal-close-btn" onClick={handleClose}>&times;</button>
                </div>
                <div className="modal-body">

                <svg 
                    className="le-diagram modal-logic" 
                    viewBox="0 0 800 600" 
                    xmlns="http://www.w3.org/2000/svg"
                    onMouseMove={handleMouseMove}
                >
                    <defs />
                    <rect fill="#ffffff" width="100%" height="100%" x="0" y="0" rx="8" />

                    {/* --- Static Wiring Layer --- */}
                    <g className="wires">
                        <Wire d="M 241.11 76 L 349.43 76 L 349.43 394 L 457.74 394.04" id="net_G" activated={nets["net_G"] === 1} highlighted={highlightedNode === "net_G"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 137.11 40.04 L 121.1 40 L 121.1 62 L 137.11 62.04" id="net_B" activated={nets["net_B"] === 1} highlighted={highlightedNode === "net_B"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 149.63 30.04 L 161.11 30.04" id="net_m6_out" activated={nets["net_m6_out"] === 1} highlighted={highlightedNode === "net_m6_out"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 149.63 72.04 L 161.11 72.04" id="net_m8_out" activated={nets["net_m8_out"] === 1} highlighted={highlightedNode === "net_m8_out"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 149.63 117.41 L 161.1 117.38 L 161.11 114.04" id="net_m13_out" activated={nets["net_m13_out"] === 1} highlighted={highlightedNode === "net_m13_out"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 137.11 117.41 L 78.57 117.38 L 20 118.29" id="net_D" activated={nets["net_D"] === 1} highlighted={highlightedNode === "net_D"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 137.11 129.09 L 70 129.1 L 70 440 L 540 440 L 540 308 L 524 308" id="net_Q" activated={nets["net_Q"] === 1} highlighted={highlightedNode === "net_Q"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 137.11 105.72 L 121.1 105.71 L 121.1 82 L 137.11 82.04" id="net_C" activated={nets["net_C"] === 1} highlighted={highlightedNode === "net_C"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 241.11 216 L 360 216 L 360 308 L 464 308" id="net_F" activated={nets["net_F"] === 1} highlighted={highlightedNode === "net_F"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 137.11 180.04 L 121.1 180 L 121.1 202 L 137.11 202.04" id="net_B" activated={nets["net_B"] === 1} highlighted={highlightedNode === "net_B"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 149.63 170.04 L 161.11 170.04" id="net_m18_out" activated={nets["net_m18_out"] === 1} highlighted={highlightedNode === "net_m18_out"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 149.63 212.04 L 161.11 212.04" id="net_m20_out" activated={nets["net_m20_out"] === 1} highlighted={highlightedNode === "net_m20_out"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 149.63 257.41 L 161.1 257.38 L 161.11 254.04" id="net_m24_out" activated={nets["net_m24_out"] === 1} highlighted={highlightedNode === "net_m24_out"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 137.11 269.09 L 104.05 269.1 L 70 269" id="net_Q" activated={nets["net_Q"] === 1} highlighted={highlightedNode === "net_Q"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 137.11 245.72 L 121.1 245.71 L 121.1 222 L 137.11 222.04" id="net_C" activated={nets["net_C"] === 1} highlighted={highlightedNode === "net_C"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 20 19.9 L 78.57 19.9 L 137.11 20.04" id="net_A" activated={nets["net_A"] === 1} highlighted={highlightedNode === "net_A"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 20 51.41 L 121 51" id="net_B" activated={nets["net_B"] === 1} highlighted={highlightedNode === "net_B"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 20 93.41 L 121 93" id="net_C" activated={nets["net_C"] === 1} highlighted={highlightedNode === "net_C"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 110.5 22 L 110.52 160 L 137.11 160.04" id="net_A" activated={nets["net_A"] === 1} highlighted={highlightedNode === "net_A"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 100.5 53 L 100.52 191 L 121 191" id="net_B" activated={nets["net_B"] === 1} highlighted={highlightedNode === "net_B"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 90.5 95 L 90.52 233 L 121 233" id="net_C" activated={nets["net_C"] === 1} highlighted={highlightedNode === "net_C"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 90.5 95 L 90.52 334.1 L 384.11 334.06" id="net_C" activated={nets["net_C"] === 1} highlighted={highlightedNode === "net_C"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 80.5 119 L 80.52 257 L 137.1 257" id="net_D" activated={nets["net_D"] === 1} highlighted={highlightedNode === "net_D"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        {/* Output section wires */}
                        <Wire d="M 524 308.1 L 540 308.1 L 540 132 L 707.1 132" id="net_Q" activated={nets["net_Q"] === 1} highlighted={highlightedNode === "net_Q"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 470.26 404.04 L 494 404.05 L 494 363.78" id="net_R" activated={nets["net_R"] === 1} highlighted={highlightedNode === "net_R"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 457.74 404.04 L 81 404 L 80.5 119" id="net_D" activated={nets["net_D"] === 1} highlighted={highlightedNode === "net_D"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 384.11 345.74 L 364 345.71 L 364 539 L 364 540" id="net_K" activated={nets["net_K"] === 1} highlighted={highlightedNode === "net_K"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 384.11 322.37 L 350 322.39" id="net_G" activated={nets["net_G"] === 1} highlighted={highlightedNode === "net_G"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 470.26 170.04 L 494 170.05 L 494 277.78" id="net_S" activated={nets["net_S"] === 1} highlighted={highlightedNode === "net_S"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 457.74 160.04 L 360 160 L 360 0 L 110 0 L 110 18 L 109 18" id="net_A" activated={nets["net_A"] === 1} highlighted={highlightedNode === "net_A"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 457.74 180.04 L 440 180 L 440 200" id="net_GND" activated={nets["net_GND"] === 1} highlighted={highlightedNode === "net_GND"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        {/* Right side outputs */}
                        <Wire d="M 707.11 49.86 L 540 49.9 L 540 308.1 L 524 308.11" id="net_Q" activated={nets["net_Q"] === 1} highlighted={highlightedNode === "net_Q"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 719.63 49.86 L 749.81 49.86 L 780 49.86" id="net_X" activated={nets["net_X"] === 1} highlighted={highlightedNode === "net_X"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 719.63 132.34 L 749.81 132.33 L 780 132.34" id="net_Y" activated={nets["net_Y"] === 1} highlighted={highlightedNode === "net_Y"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 690 142 L 690 61.52 L 707.11 61.54" id="net_F" activated={nets["net_F"] === 1} highlighted={highlightedNode === "net_F"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 653 38 L 680.05 38 L 707.11 38.17" id="net_G" activated={nets["net_G"] === 1} highlighted={highlightedNode === "net_G"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 651 40 L 651 120.71 L 707.11 120.65" id="net_G" activated={nets["net_G"] === 1} highlighted={highlightedNode === "net_G"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 349 74 L 349 38 L 649 38" id="net_G" activated={nets["net_G"] === 1} highlighted={highlightedNode === "net_G"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 360 214 L 360 170 L 457.74 170.04" id="net_F" activated={nets["net_F"] === 1} highlighted={highlightedNode === "net_F"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 362 216 L 690 216 L 690 146" id="net_F" activated={nets["net_F"] === 1} highlighted={highlightedNode === "net_F"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 690 144 L 710 144" id="net_F" activated={nets["net_F"] === 1} highlighted={highlightedNode === "net_F"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        {/* Triangle / Inverter */}
                        <path 
                            d="M 464 324.56 L 477 334.06 L 464 343.56 Z" 
                            fill={highlightedNode === "net_clk_1_out" ? "red" : "#ffffff"} 
                            stroke={highlightedNode === "net_clk_1_out" ? "red" : "#000000"} 
                            strokeMiterlimit="10" 
                            onMouseEnter={() => handleMouseEnter("net_clk_1_out")}
                            onMouseLeave={handleMouseLeave}
                        />
                        {/* Ground symbols */}
                        <Wire d="M 435 200 L 445 200" id="net_GND" activated={nets["net_GND"] === 1} highlighted={highlightedNode === "net_GND"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 436 202 L 444 202" id="net_GND" activated={nets["net_GND"] === 1} highlighted={highlightedNode === "net_GND"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 437 204 L 443 204" id="net_GND" activated={nets["net_GND"] === 1} highlighted={highlightedNode === "net_GND"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 438 206 L 442 206" id="net_GND" activated={nets["net_GND"] === 1} highlighted={highlightedNode === "net_GND"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 458 414 L 440 414 L 440 430" id="net_GND" activated={nets["net_GND"] === 1} highlighted={highlightedNode === "net_GND"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 435 430 L 445 430" id="net_GND" activated={nets["net_GND"] === 1} highlighted={highlightedNode === "net_GND"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 436 432 L 444 432" id="net_GND" activated={nets["net_GND"] === 1} highlighted={highlightedNode === "net_GND"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 437 434 L 443 434" id="net_GND" activated={nets["net_GND"] === 1} highlighted={highlightedNode === "net_GND"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 438 436 L 442 436" id="net_GND" activated={nets["net_GND"] === 1} highlighted={highlightedNode === "net_GND"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 446.89 334.06 L 464 334.06" id="net_clk_2_out" activated={nets["net_clk_2_out"] === 1} highlighted={highlightedNode === "net_clk_2_out"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 434.37 334.06 L 396.63 334.06" id="net_clk_1_out" activated={nets["net_clk_1_out"] === 1} highlighted={highlightedNode === "net_clk_1_out"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 434.37 322.37 L 415.71 322.38 L 415.74 333.84" id="net_clk_1_out" activated={nets["net_clk_1_out"] === 1} highlighted={highlightedNode === "net_clk_1_out"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 434 346 L 416 346 L 416 362" id="net_GND" activated={nets["net_GND"] === 1} highlighted={highlightedNode === "net_GND"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 411 362 L 421 362" id="net_GND" activated={nets["net_GND"] === 1} highlighted={highlightedNode === "net_GND"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 412 364 L 420 364" id="net_GND" activated={nets["net_GND"] === 1} highlighted={highlightedNode === "net_GND"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 413 366 L 419 366" id="net_GND" activated={nets["net_GND"] === 1} highlighted={highlightedNode === "net_GND"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <Wire d="M 414 368 L 418 368" id="net_GND" activated={nets["net_GND"] === 1} highlighted={highlightedNode === "net_GND"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                    </g>

                    {/* --- Connection Dots --- */}
                    <g className="connections">
                        <ConnectionDot x={688} y={142} id="net_F" activated={nets["net_F"] === 1} highlighted={highlightedNode === "net_F"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <ConnectionDot x={538} y={306} id="net_Q" activated={nets["net_Q"] === 1} highlighted={highlightedNode === "net_Q"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <ConnectionDot x={348} y={320} id="net_G" activated={nets["net_G"] === 1} highlighted={highlightedNode === "net_G"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <ConnectionDot x={538} y={131} id="net_Q" activated={nets["net_Q"] === 1} highlighted={highlightedNode === "net_Q"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <ConnectionDot x={649} y={36} id="net_G" activated={nets["net_G"] === 1} highlighted={highlightedNode === "net_G"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <ConnectionDot x={347} y={74} id="net_G" activated={nets["net_G"] === 1} highlighted={highlightedNode === "net_G"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <ConnectionDot x={358} y={214} id="net_F" activated={nets["net_F"] === 1} highlighted={highlightedNode === "net_F"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <ConnectionDot x={68} y={267} id="net_Q" activated={nets["net_Q"] === 1} highlighted={highlightedNode === "net_Q"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <ConnectionDot x={79} y={255} id="net_D" activated={nets["net_D"] === 1} highlighted={highlightedNode === "net_D"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <ConnectionDot x={89} y={231} id="net_C" activated={nets["net_C"] === 1} highlighted={highlightedNode === "net_C"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <ConnectionDot x={119} y={49} id="net_B" activated={nets["net_B"] === 1} highlighted={highlightedNode === "net_B"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <ConnectionDot x={414} y={332} id="net_clk_1_out" activated={nets["net_clk_1_out"] === 1} highlighted={highlightedNode === "net_clk_1_out"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <ConnectionDot x={88} y={91} id="net_C" activated={nets["net_C"] === 1} highlighted={highlightedNode === "net_C"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <ConnectionDot x={120} y={91} id="net_C" activated={nets["net_C"] === 1} highlighted={highlightedNode === "net_C"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <ConnectionDot x={99} y={50} id="net_B" activated={nets["net_B"] === 1} highlighted={highlightedNode === "net_B"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <ConnectionDot x={108} y={18} id="net_A" activated={nets["net_A"] === 1} highlighted={highlightedNode === "net_A"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                        <ConnectionDot x={119} y={49} id="net_B" activated={nets["net_B"] === 1} highlighted={highlightedNode === "net_B"} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
                    </g>

                    <EllipseNode cx={432} cy={322} />

                    {/* --- Editable Components --- */}
                    <Mux key="m6"   x={143.37} y={30.04}  rotation={90} selection={muxConfig["m6"]  || 0} numInputs={2} onClick={() => handleMuxClick("m6", 2)} />
                    <Mux key="m8"   x={143.37} y={72.04}  rotation={90} selection={muxConfig["m8"]  || 0} numInputs={2} onClick={() => handleMuxClick("m8", 2)} />
                    <Mux key="m13"  x={143.37} y={117.41} rotation={90} selection={muxConfig["m13"] || 0} numInputs={3} onClick={() => handleMuxClick("m13", 3)} />
                    <Mux key="m18"  x={143.37} y={170.04} rotation={90} selection={muxConfig["m18"] || 0} numInputs={2} onClick={() => handleMuxClick("m18", 2)} />
                    <Mux key="m20"  x={143.37} y={212.04} rotation={90} selection={muxConfig["m20"] || 0} numInputs={2} onClick={() => handleMuxClick("m20", 2)} />
                    <Mux key="m24"  x={143.37} y={257.41} rotation={90} selection={muxConfig["m24"] || 0} numInputs={3} onClick={() => handleMuxClick("m24", 3)} />
                    <Mux key="m46"  x={464}    y={404.04} rotation={90} selection={muxConfig["m46"] || 0} numInputs={3} onClick={() => handleMuxClick("m46", 3)} />
                    <Mux key="m51"  x={390.37} y={334.06} rotation={90} selection={muxConfig["m51"] || 0} numInputs={3} onClick={() => handleMuxClick("m51", 3)} />
                    <Mux key="m56"  x={464}    y={170.04} rotation={90} selection={muxConfig["m56"] || 0} numInputs={3} onClick={() => handleMuxClick("m56", 3)} />
                    <Mux key="m59"  x={713.37} y={49.86}  rotation={90} selection={muxConfig["m59"] || 0} numInputs={3} onClick={() => handleMuxClick("m59", 3)} />
                    <Mux key="m61"  x={713.37} y={132.34} rotation={90} selection={muxConfig["m61"] || 0} numInputs={3} onClick={() => handleMuxClick("m61", 3)} />
                    <Mux key="m100" x={440.63} y={334.06} rotation={90} selection={muxConfig["m100"]|| 0} numInputs={3} onClick={() => handleMuxClick("m100", 3)} />

                    {/* LUTs */}
                    <Lut x={161.11} y={16}  width={100} height={120} label="LUT 1" config={lutConfig["lut_0"]} onChange={(i) => handleLutChange("lut_0", i)} />
                    <Lut x={161.11} y={156} width={100} height={120} label="LUT 2" config={lutConfig["lut_1"]} onChange={(i) => handleLutChange("lut_1", i)} />

                    {/* D Flip-Flop */}
                    <FlipFlop x={464} y={277.78} width={60} height={86} label="D Flip-Flop" />

                    {/* Labels & Inputs */}
                    <InputButton x={10} y={20}  label="A" value={inputs["A"]} onChange={(v) => handleInputChange("A", v)} />
                    <InputButton x={10} y={52}  label="B" value={inputs["B"]} onChange={(v) => handleInputChange("B", v)} />
                    <InputButton x={10} y={93}  label="C" value={inputs["C"]} onChange={(v) => handleInputChange("C", v)} />
                    <InputButton x={10} y={118} label="D" value={inputs["D"]} onChange={(v) => handleInputChange("D", v)} />
                    <Label x={270} y={205} text="F" onClick={() => {}} id="label_F" />
                    <Label x={271} y={69}  text="G" onClick={() => {}} id="label_G" />
                    <InputButton x={364} y={554} label="K" value={inputs["K"]} onChange={(v) => handleInputChange("K", v)} />
                    <Label x={474} y={310} text="D" onClick={() => {}} id="label_D_FF" />
                    <Label x={514} y={310} text="Q" onClick={() => {}} id="label_Q" />
                    <Label x={494} y={353} text="R" onClick={() => {}} id="label_R" />
                    <Label x={494} y={291} text="S" onClick={() => {}} id="label_S" />
                    <Label x={790} y={53}  text="X" onClick={() => {}} id="label_X" />
                    <Label x={790} y={136} text="Y" onClick={() => {}} id="label_Y" />
                </svg>

                <div className="modal-status-bar">
                    <span>x: {mousePos.x}, y: {mousePos.y}</span>
                    {highlightedNode && <span style={{ color: '#2563eb', fontWeight: 500 }}>Net: {highlightedNode}</span>}
                </div>

                </div>
            </div>
        </div>
    );
};

export default LogicElementModal;
