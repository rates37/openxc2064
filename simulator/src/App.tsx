import React from 'react';
import { SimulatorProvider } from './SimulatorContext';
import SimulationToolbar from './components/SimulationToolbar';
import SimulationCanvas from './components/SimulationCanvas';
import SwitchMatrixEditor from './components/SwitchMatrixEditor';
import LogicElementModal from './components/LogicElementModal';
import IOBankModal from './components/IOBankModal';

const App: React.FC = () => {
  return (
    <SimulatorProvider>
      <div style={{ userSelect: 'none' }}>
        <SimulationToolbar />
        <SimulationCanvas />
        <SwitchMatrixEditor />
        <LogicElementModal />
        <IOBankModal />
      </div>
    </SimulatorProvider>
  );
}

export default App;
