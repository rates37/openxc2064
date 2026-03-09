import React, { useRef, useState, useCallback, useEffect } from 'react';
import { useSimulator } from '../SimulatorContext';
import LogicCellRenderer from './LogicCellRenderer';

const CELL_SPACING_X = 220;
const CELL_SPACING_Y = 300;
const CELLS_PER_ROW = 8;

const SimulationCanvas: React.FC = () => {
  const { logicCells } = useSimulator();
  const svgRef = useRef<SVGSVGElement>(null);
  const [viewBox, setViewBox] = useState({ x: 0, y: 0, w: 2000, h: 2000 });
  const [isPanning, setIsPanning] = useState(false);
  const panStart = useRef({ x: 0, y: 0 });

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    setIsPanning(true);
    panStart.current = { x: e.clientX, y: e.clientY };
    (e.target as Element).setPointerCapture(e.pointerId);
  }, []);

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (!isPanning || !svgRef.current) return;
    const svg = svgRef.current;
    const ctm = svg.getScreenCTM();
    if (!ctm) return;
    const dx = (e.clientX - panStart.current.x) / ctm.a;
    const dy = (e.clientY - panStart.current.y) / ctm.d;
    panStart.current = { x: e.clientX, y: e.clientY };
    setViewBox((v) => ({ ...v, x: v.x - dx, y: v.y - dy }));
  }, [isPanning]);

  const onPointerUp = useCallback(() => {
    setIsPanning(false);
  }, []);

  // Use a ref to track the latest viewBox so the native listener never goes stale.
  const viewBoxRef = useRef(viewBox);
  viewBoxRef.current = viewBox;

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const scale = e.deltaY > 0 ? 1.1 : 0.9;
      const rect = svg.getBoundingClientRect();
      const vb = viewBoxRef.current;
      const cx = vb.x + ((e.clientX - rect.left) / rect.width) * vb.w;
      const cy = vb.y + ((e.clientY - rect.top) / rect.height) * vb.h;
      const newW = vb.w * scale;
      const newH = vb.h * scale;
      setViewBox({
        x: cx - (cx - vb.x) * scale,
        y: cy - (cy - vb.y) * scale,
        w: newW,
        h: newH,
      });
    };
    svg.addEventListener('wheel', handleWheel, { passive: false });
    return () => svg.removeEventListener('wheel', handleWheel);
  }, []);

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: 'calc(100vh - 50px)',
    }}>
      <svg
        ref={svgRef}
        viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`}
        style={{
          width: '100%',
          height: '100%',
          border: '1px solid #ccc',
          borderRadius: '8px',
          boxShadow: '0 0 6px rgba(0, 0, 0, 0.08)',
          cursor: isPanning ? 'grabbing' : 'grab',
          touchAction: 'none',
        }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
      >
        <LogicCellRenderer />
      </svg>
    </div>
  );
};

export default SimulationCanvas;
