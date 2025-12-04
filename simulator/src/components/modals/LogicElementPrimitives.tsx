import React from "react";



interface SvgShapeProps {
  stroke?: string;
  fill?: string;
  strokeWidth?: number;
  className?: string;
  onClick?: (e: React.MouseEvent) => void;
  style?: React.CSSProperties;
}

interface WireProps {
  d: string;
  stroke?: string;
  strokeWidth?: number;
}

export const Wire: React.FC<WireProps> = ({ d, stroke = "#000000", strokeWidth = 1 }) => (
  <path d={d} fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeMiterlimit="10" />
);



interface MuxProps extends SvgShapeProps {
  x: number;
  y: number;
  rotation?: number;
  selected?: boolean;
}

export const Mux: React.FC<MuxProps> = ({ 
  x, y, rotation = 90, stroke = "#000000", fill = "#ffffff", selected, onClick 
}) => {
  // Standard trapezoid shape from the original SVG
  // Original path: M 123.37 36.3 L 128.53 23.78 L 158.21 23.78 L 163.37 36.3 Z
  // Center roughly at 143, 30. Normalized to 0,0 for transform.
  
  // Width approx 40, Height approx 12.5.
  // We draw it centered then rotate.
  
  const pathData = "M -20 6.26 L -14.84 -6.26 L 14.84 -6.26 L 20 6.26 Z";
  
  const transform = `translate(${x}, ${y}) rotate(${rotation})`;
  
  return (
    <g transform={transform} onClick={onClick} className="cursor-pointer hover:opacity-80 transition-opacity">
      <path 
        d={pathData} 
        fill={selected ? "#bfdbfe" : fill} 
        stroke={selected ? "#2563eb" : stroke} 
        strokeWidth="1" 
        strokeMiterlimit="10" 
      />
    </g>
  );
};


interface LutProps extends SvgShapeProps {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  onLabelChange?: (newLabel: string) => void;
}

export const Lut: React.FC<LutProps> = ({ 
  x, y, width, height, label, stroke = "#000000", fill = "#ffffff", onClick 
}) => {
  return (
    <g transform={`translate(${x}, ${y})`} onClick={onClick} className="cursor-pointer group">
      <rect 
        width={width} 
        height={height} 
        fill={fill} 
        stroke={stroke} 
        className="group-hover:stroke-blue-500 transition-colors"
      />
      <foreignObject x={0} y={0} width={width} height={height} className="pointer-events-none">
         <div className="h-full w-full flex items-center justify-center">
            {/* <span className="text-xs font-sans text-center select-none">{label}</span> */}
         </div>
      </foreignObject>
    </g>
  );
};

export const FlipFlop: React.FC<LutProps> = ({ 
  x, y, width, height, label, stroke = "#000000", fill = "#ffffff", onClick 
}) => {
  return (
    <g transform={`translate(${x}, ${y})`} onClick={onClick} className="cursor-pointer group">
      <rect 
        width={width} 
        height={height} 
        fill={fill} 
        stroke={stroke} 
        className="group-hover:stroke-blue-500 transition-colors"
      />
      <foreignObject x={0} y={0} width={width} height={height} className="pointer-events-none">
         <div className="h-full w-full flex items-center justify-center">
            {/* <span className="text-xs font-sans text-center select-none">{label}</span> */}
         </div>
      </foreignObject>
    </g>
  );
};

interface LabelProps extends SvgShapeProps {
  id: string;
  x: number;
  y: number;
  text: string;
  onClick: () => void;
}

export const Label: React.FC<LabelProps> = ({ x, y, text, onClick }) => {
  return (
    <g transform={`translate(${x}, ${y})`} onClick={onClick} className="cursor-pointer hover:scale-110 transition-transform origin-center">
      <rect x="-10" y="-10" width="20" height="20" fill="transparent" />
      <text 
        dy="0.3em"
        fill="#000000" 
        textAnchor="middle" 
        className="select-none font-bold"
      >
        {text}
      </text>
    </g>
  );
};

export const ConnectionDot: React.FC<{x: number, y: number}> = ({ x, y }) => (
  <rect x={x} y={y} width={4} height={4} fill="#000000" />
);

export const EllipseNode: React.FC<{cx: number, cy: number}> = ({ cx, cy }) => (
    <ellipse cx={cx} cy={cy} rx={2} ry={2} fill="#ffffff" stroke="#000000" />
);