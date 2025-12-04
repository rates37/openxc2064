import React from "react";
import "../../styles/Modal.css";
import { LogicElement } from "../../models/LogicElement";
import { Mux, Wire, Lut, Label, FlipFlop, ConnectionDot, EllipseNode } from "../modals/LogicElementPrimitives";


type LogicElementModalProps = {
    isOpen: boolean;
    onClose: () => void;
    element: LogicElement | null;
    onSave: (element: LogicElement) => void;
};

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
            numOutputs,
        });
        onClose();
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <h2>{element.id} - Logic Element</h2>

                <svg className="le-diagram modal-logic" viewBox="0 0 800 560" xmlns="http://www.w3.org/2000/svg">
                    <defs />
                    <rect fill="#ffffff" width="100%" height="100%" x="0" y="0" />

                    {/* --- Static Wiring Layer (Reconstructed from SVG data) --- */}
                    <g className="wires">
                        {/* Top/Initial Wires */}
                        <Wire d="M 241.11 76 L 349.43 76 L 349.43 394 L 457.74 394.04" />
                        <Wire d="M 137.11 40.04 L 121.1 40 L 121.1 62 L 137.11 62.04" />
                        <Wire d="M 149.63 30.04 L 161.11 30.04" />
                        <Wire d="M 149.63 72.04 L 161.11 72.04" />
                        <Wire d="M 149.63 117.41 L 161.1 117.38 L 161.11 114.04" />
                        <Wire d="M 137.11 117.41 L 78.57 117.38 L 20 118.29" />
                        {/* Complex routing mid-section */}
                        <Wire d="M 137.11 129.09 L 70 129.1 L 70 440 L 540 440 L 540 308 L 524 308" />
                        <Wire d="M 137.11 105.72 L 121.1 105.71 L 121.1 82 L 137.11 82.04" />
                        <Wire d="M 241.11 216 L 360 216 L 360 308 L 464 308" />
                        <Wire d="M 137.11 180.04 L 121.1 180 L 121.1 202 L 137.11 202.04" />
                        <Wire d="M 149.63 170.04 L 161.11 170.04" />
                        <Wire d="M 149.63 212.04 L 161.11 212.04" />
                        <Wire d="M 149.63 257.41 L 161.1 257.38 L 161.11 254.04" />
                        <Wire d="M 137.11 269.09 L 104.05 269.1 L 70 269" />
                        <Wire d="M 137.11 245.72 L 121.1 245.71 L 121.1 222 L 137.11 222.04" />
                        <Wire d="M 20 19.9 L 78.57 19.9 L 137.11 20.04" />
                        <Wire d="M 20 51.41 L 121 51" />
                        <Wire d="M 20 93.41 L 121 93" />
                        <Wire d="M 110.5 22 L 110.52 160 L 137.11 160.04" />
                        <Wire d="M 100.5 53 L 100.52 191 L 121 191" />
                        <Wire d="M 90.5 95 L 90.52 233 L 121 233" />
                        <Wire d="M 90.5 95 L 90.52 334.1 L 384.11 334.06" />
                        <Wire d="M 80.5 119 L 80.52 257 L 137.1 257" />
                        {/* Output section wires */}
                        <Wire d="M 524 308.1 L 540 308.1 L 540 132 L 707.1 132" />
                        <Wire d="M 470.26 404.04 L 494 404.05 L 494 363.78" />
                        <Wire d="M 457.74 404.04 L 81 404 L 80.5 119" />
                        <Wire d="M 384.11 345.74 L 364 345.71 L 364 539 L 364 540" />
                        <Wire d="M 384.11 322.37 L 350 322.39" />
                        <Wire d="M 470.26 170.04 L 494 170.05 L 494 277.78" />
                        <Wire d="M 457.74 160.04 L 360 160 L 360 0 L 110 0 L 110 18 L 109 18" />
                        <Wire d="M 457.74 180.04 L 440 180 L 440 200" />
                        {/* Right side outputs */}
                        <Wire d="M 707.11 49.86 L 540 49.9 L 540 308.1 L 524 308.11" />
                        <Wire d="M 719.63 49.86 L 749.81 49.86 L 780 49.86" />
                        <Wire d="M 719.63 132.34 L 749.81 132.33 L 780 132.34" />
                        <Wire d="M 690 142 L 690 61.52 L 707.11 61.54" />
                        <Wire d="M 653 38 L 680.05 38 L 707.11 38.17" />
                        <Wire d="M 651 40 L 651 120.71 L 707.11 120.65" />
                        <Wire d="M 349 74 L 349 38 L 649 38" />
                        <Wire d="M 360 214 L 360 170 L 457.74 170.04" />
                        <Wire d="M 362 216 L 690 216 L 690 146" />
                        <Wire d="M 690 144 L 710 144" />
                        {/* Triangle / Inverter */}
                        <path d="M 464 324.56 L 477 334.06 L 464 343.56 Z" fill="#ffffff" stroke="#000000" strokeMiterlimit="10" />
                        {/* Small detail wires (Grounds) */}
                        <Wire d="M 435 200 L 445 200" /> <Wire d="M 436 202 L 444 202" /> <Wire d="M 437 204 L 443 204" />{" "}
                        <Wire d="M 438 206 L 442 206" />
                        <Wire d="M 458 414 L 440 414 L 440 430" />
                        <Wire d="M 435 430 L 445 430" /> <Wire d="M 436 432 L 444 432" /> <Wire d="M 437 434 L 443 434" />{" "}
                        <Wire d="M 438 436 L 442 436" />
                        <Wire d="M 446.89 334.06 L 464 334.06" />
                        <Wire d="M 434.37 334.06 L 396.63 334.06" />
                        <Wire d="M 434.37 322.37 L 415.71 322.38 L 415.74 333.84" />
                        <Wire d="M 434 346 L 416 346 L 416 362" />
                        <Wire d="M 411 362 L 421 362" /> <Wire d="M 412 364 L 420 364" /> <Wire d="M 413 366 L 419 366" />{" "}
                        <Wire d="M 414 368 L 418 368" />
                    </g>

                    {/* --- Connection Dots --- */}
                    <g className="connections">
                        <ConnectionDot x={688} y={142} />
                        <ConnectionDot x={538} y={306} />
                        <ConnectionDot x={348} y={320} />
                        <ConnectionDot x={538} y={131} />
                        <ConnectionDot x={649} y={36} />
                        <ConnectionDot x={347} y={74} />
                        <ConnectionDot x={358} y={214} />
                        <ConnectionDot x={68} y={267} />
                        <ConnectionDot x={79} y={255} />
                        <ConnectionDot x={89} y={231} />
                        <ConnectionDot x={119} y={231} />
                        <ConnectionDot x={119} y={189} />
                        <ConnectionDot x={78} y={116} />
                        <ConnectionDot x={88} y={91} />
                        <ConnectionDot x={120} y={91} />
                        <ConnectionDot x={99} y={50} />
                        <ConnectionDot x={108} y={18} />
                        <ConnectionDot x={119} y={49} />
                        <ConnectionDot x={414} y={332} />
                    </g>

                    <EllipseNode cx={432} cy={322} />

                    {/* --- Editable Components --- */}
                    <Mux key={"m6"} x={143.37} y={30.04} rotation={90} selected={false} />
                    <Mux key={"m8"} x={143.37} y={72.04} rotation={90} selected={false} />
                    <Mux key={"m13"} x={143.37} y={117.41} rotation={90} selected={false} />
                    <Mux key={"m18"} x={143.37} y={170.04} rotation={90} selected={false} />
                    <Mux key={"m20"} x={143.37} y={212.04} rotation={90} selected={false} />
                    <Mux key={"m24"} x={143.37} y={257.41} rotation={90} selected={false} />
                    <Mux key={"m46"} x={464} y={404.04} rotation={90} selected={false} />
                    <Mux key={"m51"} x={390.37} y={334.06} rotation={90} selected={false} />
                    <Mux key={"m56"} x={464} y={170.04} rotation={90} selected={false} />
                    <Mux key={"m59"} x={713.37} y={49.86} rotation={90} selected={false} />
                    <Mux key={"m61"} x={713.37} y={132.34} rotation={90} selected={false} />
                    <Mux key={"m100"} x={440.63} y={334.06} rotation={90} selected={false} />

                    {/* LUTs */}
                    <Lut x={161.11} y={16} width={80} height={120} label={"LUT 1"} />
                    <Lut x={161.11} y={156} width={80} height={120} label={"LUT 2"} />

                    {/* D Flip-Flop */}
                    <FlipFlop x={464} y={277.78} width={60} height={86} label={"D Flip-Flop"} />

                    {/* Labels */}
                    <Label x={10} y={23} text={"A"} bold={true} />
                    <Label x={10} y={55} text={"B"} bold={true} />
                    <Label x={10} y={97} text={"C"} bold={true} />
                    <Label x={10} y={122} text={"D"} bold={true} />
                    <Label x={250} y={210} text={"F"} bold={true} />
                    <Label x={251} y={69} text={"G"} bold={true} />
                    <Label x={364} y={554} text={"K"} bold={true} />
                    <Label x={474} y={310} text={"D"} bold={true} />
                    <Label x={514} y={310} text={"Q"} bold={true} />
                    <Label x={494} y={353} text={"R"} bold={true} />
                    <Label x={494} y={291} text={"S"} bold={true} />
                    <Label x={790} y={53} text={"X"} bold={true} />
                    <Label x={790} y={136} text={"Y"} bold={true} />


                </svg>

                <div className="modal-info">
                    <p>
                        <strong>Element ID:</strong> {element.id}
                    </p>
                    <p>
                        <strong>Inputs:</strong> A, B, C, D, Clock
                    </p>
                    <p>
                        <strong>Outputs:</strong> X, Y
                    </p>
                    <p>
                        <strong>Components:</strong> Combinational Logic, MUXes, D Flip-Flop
                    </p>
                </div>

                <button onClick={onClose}>Close</button>
            </div>
        </div>
    );
};

export default LogicElementModal;
