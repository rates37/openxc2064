import React from 'react';
import { useSimulator } from '../SimulatorContext';

const SimulationToolbar: React.FC = () => {
  const { simulate, isRunning } = useSimulator();

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      padding: '8px 16px',
      borderBottom: '1px solid #ddd',
    }}>
      <button
        onClick={simulate}
        disabled={isRunning}
        style={{
          padding: '6px 16px',
          cursor: isRunning ? 'not-allowed' : 'pointer',
        }}
      >
        {isRunning ? 'Simulating...' : 'Simulate'}
      </button>
    </div>
  );
};

export default SimulationToolbar;
