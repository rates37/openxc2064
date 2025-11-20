import React, { useState, useEffect } from 'react';
import Canvas from './components/Canvas';
import Controls from './components/Controls';
import { SimulationMode, BoxEntity } from './types';
import { generateInitialBoxes } from './services/simulationEngine';
import { DEFAULT_CONFIG } from './constants';

const App: React.FC = () => {
  const [mode, setMode] = useState<SimulationMode>(SimulationMode.RUNNING);
  const [entities, setEntities] = useState<BoxEntity[]>([]);
  const [showGrid, setShowGrid] = useState(true);
  const [showConnections, setShowConnections] = useState(true);

  // Initialize with random data
  useEffect(() => {
    // We use a default size for initial load, the canvas will resize itself
    const initial = generateInitialBoxes(DEFAULT_CONFIG.boxCount, { width: 800, height: 600 });
    setEntities(initial);
  }, []);

  const handleReset = () => {
    // Reset to default random state
    // Note: In a real app, we might want to read current canvas dims
    const width = window.innerWidth - 320; // Approx canvas width (screen - sidebar)
    const height = window.innerHeight;
    setEntities(generateInitialBoxes(DEFAULT_CONFIG.boxCount, { width, height }));
    setMode(SimulationMode.IDLE);
  };

  const handleAddBox = () => {
    const width = window.innerWidth - 320;
    const height = window.innerHeight;
    const newBox = generateInitialBoxes(1, { width, height })[0];
    setEntities(prev => [...prev, newBox]);
  };

  return (
    <div className="flex h-screen w-screen bg-sim-bg text-white overflow-hidden font-sans selection:bg-sim-accent selection:text-white">
      {/* Main Simulation Area */}
      <Canvas 
        entities={entities} 
        setEntities={setEntities}
        mode={mode}
        showGrid={showGrid}
        showConnections={showConnections}
      />

      {/* Sidebar Controls */}
      <Controls
        mode={mode}
        setMode={setMode}
        onReset={handleReset}
        onAddBox={handleAddBox}
        setEntities={setEntities}
        canvasWidth={window.innerWidth - 320}
        canvasHeight={window.innerHeight}
        showGrid={showGrid}
        toggleGrid={() => setShowGrid(!showGrid)}
        showConnections={showConnections}
        toggleConnections={() => setShowConnections(!showConnections)}
      />
    </div>
  );
};

export default App;
