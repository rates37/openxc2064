import React from 'react';
import { SimulatorProvider } from './SimulatorContext';
import SimulationToolbar from './components/SimulationToolbar';
import SimulationCanvas from './components/SimulationCanvas';

const App: React.FC = () => {
  return (
    <SimulatorProvider>
      <div style={{ userSelect: 'none' }}>
        <SimulationToolbar />
        <SimulationCanvas />
      </div>
    </SimulatorProvider>
  );
}

export default App;
