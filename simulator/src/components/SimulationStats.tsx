import React from 'react';
import { useSimulator } from '../SimulatorContext';

const SimulationStats: React.FC = () => {
  const { simStats } = useSimulator();

  if (!simStats) {
    return null;
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '16px',
        right: '16px',
        backgroundColor: 'rgba(30, 30, 30, 0.95)',
        color: '#fff',
        padding: '12px 16px',
        borderRadius: '4px',
        fontSize: '12px',
        fontFamily: 'monospace',
        border: '1px solid #444',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
        zIndex: 1000,
        lineHeight: '1.6',
      }}
    >
      <div style={{ fontWeight: 'bold', marginBottom: '8px', fontSize: '13px' }}>
        Simulation Stats
      </div>
      <div>Avg Steps: {simStats.avg_steps.toFixed(2)}</div>
      <div>Avg Time: {simStats.avg_time.toFixed(1)} ms</div>
      <div>Min Time: {simStats.min_time.toFixed(1)} ms</div>
      <div>Max Time: {simStats.max_time.toFixed(1)} ms</div>
      <div>Sim FMAX: {(0.5 / (simStats.max_time * 0.001)).toFixed(2)} Hz</div>
    </div>
  );
};

export default SimulationStats;
