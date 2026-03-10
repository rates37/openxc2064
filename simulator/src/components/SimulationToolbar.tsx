import React from 'react';
import { useSimulator } from '../SimulatorContext';

const SimulationToolbar: React.FC = () => {
  const { simulate, isRunning, showGrid, toggleGrid } = useSimulator();

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
      <button
        onClick={toggleGrid}
        style={{
          marginLeft: '8px',
          padding: '6px 16px',
          cursor: 'pointer',
        }}
      >
        {showGrid ? 'Hide Grid' : 'Show Grid'}
      </button>
    </div>
  );
};

export default SimulationToolbar;
