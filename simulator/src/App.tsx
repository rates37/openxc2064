import React, { useState, useEffect } from 'react';
import LogicArray from './LogicArray';
import { LogicElement } from './models/LogicElement';
import { XC2064 } from './constants';
import { SimulatorContext, SimulatorContextType } from './context/SimulatorContext';


const App: React.FC = () => {
  return <>
    <LogicArray />
  </>
}

export default App;
