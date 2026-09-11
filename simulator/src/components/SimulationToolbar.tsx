import React, { useState } from 'react';
import { useSimulator } from '../SimulatorContext';
import ExamplesModal from './ExamplesModal';
import {
  IconGrid3x3,
  IconDownload,
  IconUpload,
  IconBook2,
} from '@tabler/icons-react';

const SimulationToolbar: React.FC = () => {
  const { showGrid, toggleGrid, cursorPos, hoveredPipId, exportState, importState, searchQuery, setSearchQuery, drivers } = useSimulator();
  const [showExamplesModal, setShowExamplesModal] = useState(false);

  // Find the driver for the searched net (if any)
  const searchedNetDriver = searchQuery ? drivers.find((d) => d.destination === searchQuery)?.source : null;

  const iconButtonStyle = {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#000',
    transition: 'all 0.2s ease',
    borderRadius: '6px',
  };

  return (
    <>
      {/* Top Toolbar */}
      <div style={{
        position: 'fixed',
        top: '16px',
        left: '50%',
        transform: 'translateX(-50%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '12px',
        padding: '12px 16px',
        backdropFilter: 'blur(8px)',
        backgroundColor: 'rgba(255, 255, 255, 0.5)',
        border: '1px solid rgba(0, 0, 0, 0.08)',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
        zIndex: 1000,
      }}>
        {/* Grid Toggle Button */}
        <button
          onClick={toggleGrid}
          title={showGrid ? 'Hide Grid' : 'Show Grid'}
          style={{
            ...iconButtonStyle,
            opacity: showGrid ? 0.8 : 0.6,
          }}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(0, 0, 0, 0.05)')}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
        >
          <IconGrid3x3 size={24} stroke={2} />
        </button>

        {/* Divider */}
        <div style={{ height: '24px', width: '1px', backgroundColor: 'rgba(0, 0, 0, 0.1)' }} />

        {/* Import Button */}
        <button
          onClick={importState}
          title="Import Config"
          style={iconButtonStyle}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(0, 0, 0, 0.05)')}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
        >
          <IconUpload size={24} stroke={2} />
        </button>

        {/* Export Button */}
        <button
          onClick={exportState}
          title="Export Config"
          style={iconButtonStyle}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(0, 0, 0, 0.05)')}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
        >
          <IconDownload size={24} stroke={2} />
        </button>

        {/* Divider */}
        <div style={{ height: '24px', width: '1px', backgroundColor: 'rgba(0, 0, 0, 0.1)' }} />

        {/* Examples Button */}
        <button
          onClick={() => setShowExamplesModal(true)}
          title="Load Examples"
          style={iconButtonStyle}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(0, 0, 0, 0.05)')}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
        >
          <IconBook2 size={24} stroke={2} />
        </button>

        <ExamplesModal isOpen={showExamplesModal} onClose={() => setShowExamplesModal(false)} />
      </div>

      {/* Top Right Info Panel */}
      <div style={{
        position: 'fixed',
        top: '12px',
        right: '16px',
        backdropFilter: 'blur(12px)',
        backgroundColor: 'rgba(255, 255, 255, 0.7)',
        border: '1px solid rgba(0, 0, 0, 0.1)',
        borderRadius: '8px',
        padding: '8px 12px',
        zIndex: 999,
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
      }}>
        {/* Search Input */}
        <input
          aria-label="Search net"
          placeholder="Search net..."
          value={searchQuery ?? ''}
          onChange={(e) => setSearchQuery(e.target.value.trim() === '' ? null : e.target.value)}
          style={{
            padding: '6px 8px',
            borderRadius: '4px',
            border: '1px solid rgba(0, 0, 0, 0.15)',
            backgroundColor: 'rgba(255, 255, 255, 0.8)',
            color: '#000',
            fontSize: '12px',
            minWidth: '140px',
            transition: 'all 0.2s ease',
          }}
          onFocus={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 1)';
            e.currentTarget.style.borderColor = 'rgba(0, 0, 0, 0.3)';
          }}
          onBlur={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
            e.currentTarget.style.borderColor = 'rgba(0, 0, 0, 0.15)';
          }}
        />

        {/* Status Info */}
        <div style={{
          fontSize: '11px',
          color: '#666',
          fontFamily: 'monospace',
          lineHeight: '1.3',
          minHeight: '16px',
        }}>
          {cursorPos && (
            <div>Pos: {cursorPos.x}, {cursorPos.y}</div>
          )}
          {hoveredPipId && (
            <div>PIP: {hoveredPipId}</div>
          )}
          {searchedNetDriver && (
            <div style={{ color: '#0066cc', fontSize: '10px' }}>Driver: {searchedNetDriver}</div>
          )}
        </div>
      </div>
    </>
  );
};

export default SimulationToolbar;
