import React, { useState, useEffect } from 'react';
import LogicArray from './LogicArray';
import { LogicElement } from './models/LogicElement';
import { XC2064 } from './constants';
import { SimulatorContext, SimulatorContextType } from './context/SimulatorContext';


const App: React.FC = () => {
  return <>
  <div style={{userSelect: 'none'}}>
    <LogicArray />
  </div>
  </>
}

export default App;
