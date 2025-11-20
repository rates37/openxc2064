import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './src/App';
import { SimulatorContext, SimulatorContextProvider } from './src/context/SimulatorContext';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <SimulatorContextProvider>
        <App />
    </SimulatorContextProvider>
  </React.StrictMode>
);