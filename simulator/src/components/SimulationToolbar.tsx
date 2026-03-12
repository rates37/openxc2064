import React from 'react';
import { useSimulator } from '../SimulatorContext';

const SimulationToolbar: React.FC = () => {
  const { simulate, isRunning, showGrid, toggleGrid, cursorPos, exportState, importState } = useSimulator();

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '8px 16px',
      borderBottom: '1px solid #ddd',
    }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
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
        <button
          onClick={exportState}
          style={{
            marginLeft: '8px',
            padding: '6px 16px',
            cursor: 'pointer',
          }}
        >
          Export Config
        </button>
        <button
          onClick={importState}
          style={{
            marginLeft: '8px',
            padding: '6px 16px',
            cursor: 'pointer',
          }}
        >
          Import Config
        </button>
      </div>
      <span style={{ fontFamily: 'monospace', fontSize: '13px', color: '#555' }}>
        {cursorPos ? `X: ${cursorPos.x}  Y: ${cursorPos.y}` : ''}
      </span>
    </div>
  );
};

export default SimulationToolbar;
