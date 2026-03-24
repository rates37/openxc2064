import React from 'react';
import { useSimulator } from '../SimulatorContext';

const SimulationToolbar: React.FC = () => {
  const { simulate, isRunning, showGrid, toggleGrid, cursorPos, exportState, importState, searchQuery, setSearchQuery } = useSimulator();

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
        <input
          aria-label="Search net"
          placeholder="Search net (e.g. AA.net_0)"
          value={searchQuery ?? ''}
          onChange={(e) => setSearchQuery(e.target.value.trim() === '' ? null : e.target.value)}
          style={{
            marginLeft: '12px',
            padding: '6px 10px',
            borderRadius: 4,
            border: '1px solid #ccc',
            minWidth: 220,
          }}
        />
      </div>
      <span style={{ fontFamily: 'monospace', fontSize: '13px', color: '#555' }}>
        {cursorPos ? `X: ${cursorPos.x}  Y: ${cursorPos.y}` : ''}
      </span>
    </div>
  );
};

export default SimulationToolbar;
