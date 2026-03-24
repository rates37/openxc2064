import React from 'react';
import { useSimulator } from '../SimulatorContext';

const SimulationToolbar: React.FC = () => {
  const { simulate, isRunning, showGrid, toggleGrid, cursorPos, exportState, importState, searchQuery, setSearchQuery, drivers } = useSimulator();

  // Find the driver for the searched net (if any)
  const searchedNetDriver = searchQuery ? drivers.find((d) => d.destination === searchQuery)?.source : null;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '8px 16px',
      borderBottom: '1px solid #ddd',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
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
            padding: '6px 16px',
            cursor: 'pointer',
          }}
        >
          {showGrid ? 'Hide Grid' : 'Show Grid'}
        </button>
        <button
          onClick={exportState}
          style={{
            padding: '6px 16px',
            cursor: 'pointer',
          }}
        >
          Export Config
        </button>
        <button
          onClick={importState}
          style={{
            padding: '6px 16px',
            cursor: 'pointer',
          }}
        >
          Import Config
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <input
            aria-label="Search net"
            placeholder="Search net (e.g. AA.net_0)"
            value={searchQuery ?? ''}
            onChange={(e) => setSearchQuery(e.target.value.trim() === '' ? null : e.target.value)}
            style={{
              padding: '6px 10px',
              borderRadius: 4,
              border: '1px solid #ccc',
              minWidth: 220,
            }}
          />
          {searchedNetDriver && (
            <span style={{ fontFamily: 'monospace', fontSize: '12px', color: '#0066cc', whiteSpace: 'nowrap' }}>
              driver: {searchedNetDriver}
            </span>
          )}
        </div>
      </div>
      <span style={{ fontFamily: 'monospace', fontSize: '13px', color: '#555' }}>
        {cursorPos ? `X: ${cursorPos.x}  Y: ${cursorPos.y}` : ''}
      </span>
    </div>
  );
};

export default SimulationToolbar;
