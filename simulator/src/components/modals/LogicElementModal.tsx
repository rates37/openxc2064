import React from 'react';
import "../../styles/Modal.css";
import { LogicElement } from '../../models/LogicElement';

type LogicElementModalProps = {
    isOpen: boolean;
    onClose: () => void;
    element: LogicElement | null;
    onSave: (element: LogicElement) => void;
};

// Helper function to create a MUX trapezoid
const Mux2 = ({ x, y, width = 20, height = 40 }: { x: number; y: number; width?: number; height?: number }) => {
    const slope = 7;
    const points = `${x},${y - height / 2} ${x + width},${y - height / 2 + slope} ${x + width},${y + height / 2 - slope} ${x},${y + height / 2}`;
    return <polygon points={points} fill="none" stroke="#000" strokeWidth="2" />;
};

const Mux4 = ({ x, y, width = 20, height = 60 }: { x: number; y: number; width?: number; height?: number }) => {
    const slope = 7;
    const points = `${x},${y - height / 2} ${x + width},${y - height / 2 + slope} ${x + width},${y + height / 2 - slope} ${x},${y + height / 2}`;
    return <polygon points={points} fill="none" stroke="#000" strokeWidth="2" />;
} 

// Helper function to create a connection dot
const ConnectionDot = ({ x, y, r = 3 }: { x: number; y: number; r?: number }) => {
    return <circle cx={x} cy={y} r={r} fill="#000" />;
};

// Helper function to create a label
const Label = ({ x, y, text, bold = false, size = 14 }: { x: number; y: number; text: string; bold?: boolean; size?: number }) => {
    return <text x={x} y={y} fontSize={size} fontWeight={bold ? "bold" : "normal"}>{text}</text>;
};

// Helper function to create a wire/line
const Wire = ({ x1, y1, x2, y2 }: { x1: number; y1: number; x2: number; y2: number }) => {
    return <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#000" strokeWidth="2" />;
};

// Helper function to create a flip-flop
const FlipFlop = ({ x, y, width = 60, height = 60 }: { x: number; y: number; width?: number; height?: number }) => {
    return (
        <>
            <rect x={x} y={y} width={width} height={height} fill="none" stroke="#000" strokeWidth="2" />
            <Label x={x + 10} y={y + 20} text="D" bold={true} />
            <Label x={x + width - 15} y={y + 20} text="Q" bold={true} />
            <Label x={x + 10} y={y + height - 10} text="S" size={12} />
            <Label x={x + width - 15} y={y + height - 10} text="R" size={12} />
        </>
    );
};

const LUT = ({ x, y, width = 100, height = 140 }: { x: number; y: number; width?: number; height?: number }) => {
    return (
        <>
            <rect x={x} y={y} width={width} height={height} fill="none" stroke="#000" strokeWidth="2" />
            <Label x={x + 38} y={y + 75} text="LUT" bold={true} />
        </>
    );
}

const LogicElementModal: React.FC<LogicElementModalProps> = ({ isOpen, onClose, element, onSave }) => {
    if (!isOpen || !element) return null;

    const [name, setName] = React.useState(element.name);
    const [numInputs, setNumInputs] = React.useState(element.numInputs);
    const [numOutputs, setNumOutputs] = React.useState(element.numOutputs);

    // TODO: Implement logic element state changes
    const handleSave = () => {
        onSave({
            ...element,
            name,
            numInputs,
            numOutputs
        });
        onClose();
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <h2>{element.id} - Logic Element</h2>
                
                <svg className="le-diagram modal-logic" viewBox="0 0 800 560" xmlns="http://www.w3.org/2000/svg">
                    {/* Grid - 5px spacing */}
                    {/* <defs>
                        <pattern id="smallGrid" width="5" height="5" patternUnits="userSpaceOnUse">
                            <path d="M 5 0 L 0 0 0 5" fill="none" stroke="rgba(200,200,200,0.3)" strokeWidth="0.5"/>
                        </pattern>
                        <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
                            <rect width="50" height="50" fill="url(#smallGrid)"/>
                            <path d="M 50 0 L 0 0 0 50" fill="none" stroke="rgba(150,150,150,0.5)" strokeWidth="1"/>
                        </pattern>
                    </defs>
                    <rect width="100%" height="100%" fill="url(#grid)" /> */}
                    
                    {/* Input labels */}
                    <Label x={10} y={15} text="Inputs" bold={true} />
                    <Label x={10} y={52} text="A" />
                    <Label x={10} y={89} text="B" />
                    <Label x={10} y={140} text="C" />
                    <Label x={10} y={174} text="D" />

                    {/* Input lines - staggered for readability */}
                    <Wire x1={30} y1={48} x2={180} y2={48} />
                    <Wire x1={30} y1={85.3} x2={160} y2={85.3} />
                    <Wire x1={30} y1={136.8} x2={140} y2={136.8} />
                    <Wire x1={30} y1={170} x2={120} y2={170} />

                    {/* A - vertical wire at x=180 */}
                    <Wire x1={180} y1={48} x2={180} y2={223} />
                    <ConnectionDot x={180} y={48} />
                    <Wire x1={180} y1={48} x2={220} y2={48} />
                    
                    {/* B - vertical wire at x=160 */}
                    <Wire x1={160} y1={85.3} x2={160} y2={260.3} />
                    <ConnectionDot x={160} y={85.3} />
                    
                    {/* C - vertical wire at x=140 */}
                    <Wire x1={140} y1={136.8} x2={140} y2={311.8} />
                    <ConnectionDot x={140} y={136.8} />

                    {/* D - vertical wire at x=120 */}
                    <Wire x1={120} y1={170} x2={120} y2={345} />
                    <ConnectionDot x={120} y={170} />

                    {/* Input MUX */}
                    <Mux2 x={85} y={325} />
                    
                    {/* Combinational Logic block - LUT 1 */}
                    <LUT x={250} y={45} />
                    <Mux2 x={220} y={57} />
                    <Mux2 x={220} y={113.6} />
                    <Mux4 x={220} y={170} />
                    <Wire x1={240} y1={57} x2={250} y2={57} />
                    <Wire x1={240} y1={113.6} x2={250} y2={113.6} />
                    <Wire x1={240} y1={170} x2={250} y2={170} />

                    {/* LUT1 - B input branches at center (85.3) between MUX1 and MUX2 */}
                    <Wire x1={160} y1={85.3} x2={200} y2={85.3} />
                    <ConnectionDot x={200} y={85.3} />
                    <Wire x1={200} y1={85.3} x2={200} y2={66} />
                    <Wire x1={200} y1={66} x2={220} y2={66} />
                    <Wire x1={200} y1={85.3} x2={200} y2={104.6} />
                    <Wire x1={200} y1={104.6} x2={220} y2={104.6} />
                    
                    {/* LUT1 - C input branches at center (136.8) between MUX2 and MUX3 */}
                    <Wire x1={140} y1={136.8} x2={200} y2={136.8} />
                    <ConnectionDot x={200} y={136.8} />
                    <Wire x1={200} y1={136.8} x2={200} y2={122.6} />
                    <Wire x1={200} y1={122.6} x2={220} y2={122.6} />
                    <Wire x1={200} y1={136.8} x2={200} y2={150} />
                    <Wire x1={200} y1={150} x2={220} y2={150} />
                    
                    {/* LUT1 - D input to MUX3 middle */}
                    <Wire x1={120} y1={170} x2={220} y2={170} />
                    <Wire x1={200} y1={190} x2={220} y2={190} />

                    {/* Combinational Logic block - LUT 2 */}
                    <LUT x={250} y={220} />
                    <Mux2 x={220} y={232} />
                    <Mux2 x={220} y={288.6} />
                    <Mux4 x={220} y={345} />
                    <Wire x1={240} y1={232} x2={250} y2={232} />
                    <Wire x1={240} y1={288.6} x2={250} y2={288.6} />
                    <Wire x1={240} y1={345} x2={250} y2={345} />

                    {/* LUT2 - A input from vertical wire */}
                    <Wire x1={180} y1={223} x2={220} y2={223} />
                    
                    {/* LUT2 - B input branches at center (260.3) between MUX1 and MUX2 */}
                    <Wire x1={160} y1={260.3} x2={200} y2={260.3} />
                    <ConnectionDot x={160} y={260.3} />
                    <ConnectionDot x={200} y={260.3} />
                    <Wire x1={200} y1={260.3} x2={200} y2={241} />
                    <Wire x1={200} y1={241} x2={220} y2={241} />
                    <Wire x1={200} y1={260.3} x2={200} y2={279.6} />
                    <Wire x1={200} y1={279.6} x2={220} y2={279.6} />
                    
                    {/* LUT2 - C input branches at center (311.8) between MUX2 and MUX3 */}
                    <Wire x1={140} y1={311.8} x2={200} y2={311.8} />
                    <ConnectionDot x={140} y={311.8} />
                    <ConnectionDot x={200} y={311.8} />
                    <Wire x1={200} y1={311.8} x2={200} y2={297.6} />
                    <Wire x1={200} y1={297.6} x2={220} y2={297.6} />
                    <Wire x1={200} y1={311.8} x2={200} y2={325} />
                    <Wire x1={200} y1={325} x2={220} y2={325} />

                    
                    {/* LUT2 - D input to MUX3 middle */}
                    <Wire x1={120} y1={345} x2={220} y2={345} />
                    <ConnectionDot x={120} y={345} />
                    <Wire x1={200} y1={365} x2={220} y2={365} />

                    {/* Output from LUT1 (labeled F) */}
                    <Wire x1={350} y1={115} x2={420} y2={115} />
                    <Label x={380} y={110} text="F" bold={true} />
                    <ConnectionDot x={420} y={115} />
                    
                    {/* Output from LUT2 (labeled G) */}
                    <Wire x1={350} y1={290} x2={420} y2={290} />
                    <Label x={380} y={285} text="G" bold={true} />
                    <ConnectionDot x={420} y={290} />

                    {/* F branches to output MUX and flip-flop MUX */}
                    <Wire x1={420} y1={115} x2={420} y2={50} />
                    <Wire x1={420} y1={50} x2={545} y2={50} />
                    <Wire x1={420} y1={115} x2={480} y2={115} />

                    {/* G branches to flip-flop MUX and lower output MUX */}
                    <Wire x1={420} y1={290} x2={420} y2={220} />
                    <Wire x1={420} y1={220} x2={480} y2={220} />
                    <Wire x1={420} y1={290} x2={420} y2={335} />
                    <Wire x1={420} y1={335} x2={545} y2={335} />
                    <ConnectionDot x={420} y={220} />
                    <ConnectionDot x={420} y={335} />

                    {/* Flip-flop D-Q */}
                    <FlipFlop x={480} y={135} width={60} height={60} />
                    
                    {/* K MUX (controls flip-flop input) */}
                    <Mux2 x={480} y={167.5} />
                    <Label x={455} y={172} text="K" bold={true} />
                    <Wire x1={500} y1={167.5} x2={510} y2={167.5} />
                    <Wire x1={510} y1={167.5} x2={510} y2={152} />
                    
                    {/* D input to flip-flop */}
                    <Wire x1={480} y1={152} x2={480} y2={150} />
                    
                    {/* Q output from flip-flop */}
                    <Wire x1={540} y1={152} x2={570} y2={152} />
                    <ConnectionDot x={570} y={152} />
                    
                    {/* Q feedback to K MUX top */}
                    <Wire x1={570} y1={152} x2={570} y2={120} />
                    <Wire x1={570} y1={120} x2={460} y2={120} />
                    <Wire x1={460} y1={120} x2={460} y2={157.5} />
                    <Wire x1={460} y1={157.5} x2={480} y2={157.5} />
                    
                    {/* Q forward to output MUXes */}
                    <Wire x1={570} y1={152} x2={570} y2={68} />
                    <Wire x1={570} y1={68} x2={545} y2={68} />
                    <Wire x1={570} y1={152} x2={570} y2={325} />
                    <Wire x1={570} y1={325} x2={545} y2={325} />

                    {/* Clock input at bottom */}
                    <Label x={10} y={450} text="Clock" bold={true} />
                    <Wire x1={50} y1={446} x2={510} y2={446} />
                    <Wire x1={510} y1={446} x2={510} y2={195} />
                    
                    {/* S and R inputs to flip-flop */}
                    <Label x={465} y={205} text="S" size={12} />
                    <Label x={555} y={205} text="R" size={12} />
                    
                    {/* Output MUXes */}
                    {/* X output MUX */}
                    <Mux2 x={545} y={59} />
                    <Wire x1={565} y1={59} x2={620} y2={59} />
                    <Wire x1={620} y1={59} x2={620} y2={100} />
                    <Mux2 x={620} y={100} />
                    <Wire x1={640} y1={100} x2={680} y2={100} />
                    <Wire x1={680} y1={100} x2={680} y2={90} />
                    <Wire x1={680} y1={90} x2={720} y2={90} />
                    <Label x={730} y={95} text="X" bold={true} size={16} />
                    
                    {/* Y output MUX */}
                    <Mux2 x={545} y={330} />
                    <Wire x1={565} y1={330} x2={620} y2={330} />
                    <Wire x1={620} y1={330} x2={620} y2={280} />
                    <Mux2 x={620} y={280} />
                    <Wire x1={640} y1={280} x2={680} y2={280} />
                    <Wire x1={680} y1={280} x2={680} y2={290} />
                    <Wire x1={680} y1={290} x2={720} y2={290} />
                    <Label x={730} y={295} text="Y" bold={true} size={16} />
                    
                    {/* Output labels */}
                    <Label x={730} y={15} text="Outputs" bold={true} />

                </svg>
                
                <div className="modal-info">
                    <p><strong>Element ID:</strong> {element.id}</p>
                    <p><strong>Inputs:</strong> A, B, C, D, Clock</p>
                    <p><strong>Outputs:</strong> X, Y</p>
                    <p><strong>Components:</strong> Combinational Logic, MUXes, D Flip-Flop</p>
                </div>
                
                <button onClick={onClose}>Close</button>
            </div>
        </div>
    );
}

export default LogicElementModal;