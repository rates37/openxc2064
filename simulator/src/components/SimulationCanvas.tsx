import React, { useRef, useState, useCallback, useEffect } from 'react';
import { useSimulator } from '../SimulatorContext';
import LogicCellRenderer from './LogicCellRenderer';

// Full content bounds (8x8 grid with margins)
const CONTENT_X = -600;
const CONTENT_Y = -600;
const CONTENT_WIDTH = 5000;
const CONTENT_HEIGHT = 5200;

// Initial view position (top-left area showing first few cells)
const INITIAL_VIEW = { x: -3500, y: -100, w: 7000, h: 5000 };

const SimulationCanvas: React.FC = () => {
  const { logicCells, showGrid, setCursorPos } = useSimulator();
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [viewBox, setViewBox] = useState(INITIAL_VIEW);
  const [isPanning, setIsPanning] = useState(false);
  const panStart = useRef({ x: 0, y: 0 });

  // Set initial viewBox to match the container's aspect ratio
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const { clientWidth, clientHeight } = el;
    const aspect = clientWidth / clientHeight;
    setViewBox(v => ({ ...v, w: v.h * aspect }));
  }, []);

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    setIsPanning(true);
    panStart.current = { x: e.clientX, y: e.clientY };
    (e.target as Element).setPointerCapture(e.pointerId);
  }, []);

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (svgRef.current) {
      const svg = svgRef.current;
      const ctm = svg.getScreenCTM();
      if (ctm) {
        // const svgX = (e.clientX - ctm.e) / ctm.a;
        // const svgY = (e.clientY - ctm.f) / ctm.d;
        // setCursorPos({ x: Math.round(svgX), y: Math.round(svgY) });
      }
    }
    if (!isPanning || !svgRef.current) return;
    const svg = svgRef.current;
    const ctm = svg.getScreenCTM();
    if (!ctm) return;
    const dx = (e.clientX - panStart.current.x) / ctm.a;
    const dy = (e.clientY - panStart.current.y) / ctm.d;
    panStart.current = { x: e.clientX, y: e.clientY };
    setViewBox((v) => ({ ...v, x: v.x - dx, y: v.y - dy }));
  }, [isPanning, setCursorPos]);

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
    <div ref={containerRef} style={{
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
        {showGrid && (
          <>
            <defs>
              <pattern id="grid" width={20} height={20} patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#7e7e7e" strokeWidth={0.5} />
              </pattern>
            </defs>
            {/* Render grid over entire content area, not just viewBox */}
            <rect x={viewBox.x} y={viewBox.y} width={viewBox.w} height={viewBox.h} fill="url(#grid)" />
          </>
        )}
        <LogicCellRenderer />
      </svg>
    </div>
  );
};

export default SimulationCanvas;
