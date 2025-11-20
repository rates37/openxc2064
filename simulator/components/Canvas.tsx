import React, { useRef, useEffect, useState, useCallback } from 'react';
import { BoxEntity, LineEntity, SimulationMode, Size } from '../types';
import { clearCanvas, drawGrid, drawBox, drawLine } from '../services/renderService';
import { updatePhysics, calculateProximityLines } from '../services/simulationEngine';

interface CanvasProps {
  entities: BoxEntity[];
  setEntities: React.Dispatch<React.SetStateAction<BoxEntity[]>>;
  mode: SimulationMode;
  showGrid: boolean;
  showConnections: boolean;
}

const Canvas: React.FC<CanvasProps> = ({ 
  entities, 
  setEntities, 
  mode, 
  showGrid,
  showConnections 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState<Size>({ width: 800, height: 600 });
  const requestRef = useRef<number | null>(null);

  // Handle resize
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current;
        setDimensions({ width: clientWidth, height: clientHeight });
      }
    };

    window.addEventListener('resize', updateSize);
    updateSize(); // Initial

    return () => window.removeEventListener('resize', updateSize);
  }, []);

  // Main Animation Loop
  const animate = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 1. Update Physics (if running)
    let currentEntities = entities;
    if (mode === SimulationMode.RUNNING) {
      currentEntities = updatePhysics(entities, dimensions);
      setEntities(currentEntities);
    }

    // 2. Render
    // Clear
    clearCanvas(ctx, dimensions.width, dimensions.height);

    // Grid
    if (showGrid) {
      drawGrid(ctx, dimensions.width, dimensions.height);
    }

    // Dynamic Connections (Lines)
    if (showConnections) {
      const lines = calculateProximityLines(currentEntities);
      lines.forEach(line => {
        drawLine(ctx, line.start, line.end, `rgba(59, 130, 246, ${line.opacity})`, 1);
      });
    }

    // Boxes
    currentEntities.forEach(box => {
      drawBox(ctx, box);
    });

    if (mode === SimulationMode.RUNNING) {
      requestRef.current = requestAnimationFrame(animate);
    }
  }, [entities, mode, dimensions, setEntities, showGrid, showConnections]);

  // Trigger animation when mode or dependencies change
  useEffect(() => {
    if (mode === SimulationMode.RUNNING) {
      requestRef.current = requestAnimationFrame(animate);
    } else {
      // If paused/idle, we still want to draw one frame so visual state is preserved
      // We use a one-off requestAnimationFrame to ensure it draws after state updates
      requestAnimationFrame(() => {
          const canvas = canvasRef.current;
          if (!canvas) return;
          const ctx = canvas.getContext('2d');
          if (!ctx) return;
          
          clearCanvas(ctx, dimensions.width, dimensions.height);
          if (showGrid) drawGrid(ctx, dimensions.width, dimensions.height);
          
          if (showConnections) {
             const lines = calculateProximityLines(entities);
             lines.forEach(line => {
               drawLine(ctx, line.start, line.end, `rgba(59, 130, 246, ${line.opacity})`, 1);
             });
          }

          entities.forEach(box => drawBox(ctx, box));
      });
      
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    }

    return () => {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  }, [mode, animate, dimensions, entities, showGrid, showConnections]);

  return (
    <div ref={containerRef} className="flex-1 h-full w-full relative overflow-hidden bg-sim-bg">
      <canvas
        ref={canvasRef}
        width={dimensions.width}
        height={dimensions.height}
        className="block touch-none"
      />
      <div className="absolute bottom-4 right-4 bg-sim-panel/80 backdrop-blur text-xs text-gray-400 px-2 py-1 rounded border border-gray-700">
        {dimensions.width}x{dimensions.height} | {entities.length} Entities
      </div>
    </div>
  );
};

export default Canvas;
