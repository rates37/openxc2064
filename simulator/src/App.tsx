import React from 'react';
import { SimulatorProvider } from './SimulatorContext';
import SimulationToolbar from './components/SimulationToolbar';
import SimulationCanvas from './components/SimulationCanvas';
import SwitchMatrixEditor from './components/modals/SwitchMatrixEditor';
import LogicElementModal from './components/modals/LogicElementModal';
import IOBankModal from './components/modals/IOBankModal';

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
