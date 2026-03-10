import React from 'react';
import { SimulatorProvider } from './SimulatorContext';
import SimulationToolbar from './components/SimulationToolbar';
import SimulationCanvas from './components/SimulationCanvas';
import SwitchMatrixEditor from './components/SwitchMatrixEditor';
import LogicElementModal from './components/LogicElementModal';

const App: React.FC = () => {
  return (
    <SimulatorProvider>
      <div style={{ userSelect: 'none' }}>
        <SimulationToolbar />
        <SimulationCanvas />
        <SwitchMatrixEditor />
        <LogicElementModal />
      </div>
    </SimulatorProvider>
  );
}

export default App;
