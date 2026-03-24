import React from 'react';
import '../styles/Modal.css';
import { useSimulator } from '../SimulatorContext';

const IOBankModal: React.FC = () => {
  const { selectedIOBank, selectIOBank } = useSimulator();

  if (!selectedIOBank) return null;

  const handleClose = () => selectIOBank(null);

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{selectedIOBank.id} &mdash; IO Bank</h2>
          <button className="modal-close-btn" onClick={handleClose}>&times;</button>
        </div>
        <div className="modal-body">
          {/* Blank SVG canvas for user editing */}
          <svg className="le-diagram modal-logic" viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">
            <rect fill="#fff" width="100%" height="100%" rx={8} />
            {/* User can edit this SVG in the project as needed */}
          </svg>
        </div>
      </div>
    </div>
  );
};

export default IOBankModal;
