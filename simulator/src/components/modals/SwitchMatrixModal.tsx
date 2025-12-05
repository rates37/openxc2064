import React from "react";
import "../../styles/Modal.css";
import { LogicElement } from "../../models/LogicElement";


type LogicElementModalProps = {
    isOpen: boolean;
    onClose: () => void;
    element: SwitchMatrix;
    onSave: (element: LogicElement) => void;
};

const LogicElementModal: React.FC<LogicElementModalProps> = ({ isOpen, onClose, element, onSave }) => {





}