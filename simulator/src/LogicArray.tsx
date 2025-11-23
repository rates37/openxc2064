import React from 'react';
import { useContext, useState, useEffect, useRef } from 'react';
import { SimulatorContext, SimulatorContextType } from './context/SimulatorContext';
import { LogicElement } from './models/LogicElement';
import { LogicElementComponent } from './components/LogicElementComponent';
import "./styles/LogicArray.css";
import { NodeComponent } from './components/NodeComponent';
import { BusComponent } from './components/BusComponent';
import { XC2064 } from './constants';
import LogicElementModal from './components/modals/LogicElementModal';

const LogicArray: React.FC = () => {
  const context: SimulatorContextType = useContext(SimulatorContext);
  const [logicElementDisplay, setLogicElementDisplay] = useState<React.JSX.Element | null>(null);
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [busses, setBuses] = useState<React.JSX.Element | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedElement, setSelectedElement] = useState<LogicElement | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // TODO: Handle logic element selection and modal display
  const handleLogicElementClick = (element: LogicElement) => {
    setSelectedElement(element);
    setIsModalOpen(true);
  };

  // TODO: Implement save logic for logic element changes
  const handleSaveElement = (element: LogicElement) => {
    // Save logic would go here
    console.log('Saving element:', element);
  };

  useEffect(() => {
    console.log("Logic elements updated:", context.logicElements);

    const elements = context.logicElements.map((logicElementRow, y) => (
      logicElementRow.map((logicElement, x) =>
        <LogicElementComponent 
          key={`${y}-${x}`} 
          logicElement={logicElement} 
          x={x * 190} 
          y={y * 190}
          onClick={handleLogicElementClick}
        />
      )
    ));

    setLogicElementDisplay(<>{elements}</>);

  }, [context.logicElements]);

  useEffect(() => {
    const container = containerRef.current;
    if (container) {
      const onWheel = (e: WheelEvent) => {
        e.preventDefault();
      };
      container.addEventListener('wheel', onWheel, { passive: false });
      return () => {
        container.removeEventListener('wheel', onWheel);
      };
    }
  }, []);



  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPosition(prev => ({
        x: prev.x + e.movementX,
        y: prev.y + e.movementY
      }));
    }
  };

  const handleWheel = (e: React.WheelEvent) => {
    const scaleAmount = -e.deltaY * 0.001;
    const newScale = Math.max(0.1, Math.min(scale + scaleAmount, 5));

    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const ratio = newScale / scale;

      setPosition(prev => ({
        x: x - (x - prev.x) * ratio,
        y: y - (y - prev.y) * ratio
      }));
      setScale(newScale);
    }
  };

  useEffect(() => {
    const allVBusses: number[] = [];
    const allHBusses: number[] = [];

    allVBusses.push(...XC2064.V_BUSSES);
    allHBusses.push(...XC2064.H_BUSSES);

    setBuses(<>{allHBusses.map((point) => <BusComponent key={point} horizontal={true} point={point} length={context.logicElements[0].length * 214} />)}{allVBusses.map((point) => <BusComponent key={point} horizontal={false} point={point} length={context.logicElements.length * 205} />)}</>);
  }, [context.logicElements]);


  return <>
    <div
      className="LogicArrayViewport"
      ref={containerRef}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onWheel={handleWheel}
      onContextMenu={(e) => e.preventDefault()}
    >
      <div
        className="LogicArray"
        style={{
          transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`
        }}
      >

        {logicElementDisplay}
        {busses}

      </div>

    </div>
    <LogicElementModal 
      isOpen={isModalOpen}
      onClose={() => setIsModalOpen(false)}
      element={selectedElement}
      onSave={handleSaveElement}
    />
  </>;
}




export default LogicArray;