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
  id?: string;
  highlighted?: boolean;
  activated?: boolean;
  onMouseEnter?: (id: string) => void;
  onMouseLeave?: () => void;
}

export const Wire: React.FC<WireProps> = ({ 
  d, stroke = "#000000", strokeWidth = 1, id, highlighted, activated, onMouseEnter, onMouseLeave 
}) => (
  <path 
    d={d} 
    fill="none" 
    stroke={highlighted ? "#2563eb" : (activated ? "#ef4444" : stroke)} 
    strokeWidth={highlighted || activated ? (strokeWidth + 2) : strokeWidth} 
    strokeMiterlimit="10" 
    onMouseEnter={() => id && onMouseEnter && onMouseEnter(id)}
    onMouseLeave={() => onMouseLeave && onMouseLeave()}
    style={{ cursor: id ? 'pointer' : 'default' }}
  />
);



interface MuxProps extends SvgShapeProps {
  x: number;
  y: number;
  rotation?: number;
  selection?: number;
  numInputs?: number;
}

export const Mux: React.FC<MuxProps> = ({ 
  x, y, rotation = 90, stroke = "#000000", fill = "#ffffff", selection = 0, numInputs = 2, onClick 
}) => {
  const pathData = "M -20 6.26 L -14.84 -6.26 L 14.84 -6.26 L 20 6.26 Z";
  
  const transform = `translate(${x}, ${y}) rotate(${rotation})`;

  let inputX = 0;
  if (numInputs === 2) {
    inputX = selection === 0 ? -10 : 10;
  } else if (numInputs === 3) {
    if (selection === 0) inputX = -13;
    else if (selection === 1) inputX = 0;
    else inputX = 13;
  }
  
  return (
    <g transform={transform} onClick={onClick} className="cursor-pointer hover:opacity-80 transition-opacity">
      <path 
        d={pathData} 
        fill={fill} 
        stroke={stroke} 
        strokeWidth="1" 
        strokeMiterlimit="10" 
      />
      <line 
        x1="0" y1="-6.26" 
        x2={inputX} y2="6.26" 
        stroke="black" 
        strokeWidth="2" 
      />
      <circle cx={inputX} cy="6.26" r="2" fill="black" />
    </g>
  );
};


interface LutProps extends SvgShapeProps {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  config?: number[];
  onChange?: (index: number) => void;
}

export const Lut: React.FC<LutProps> = ({ 
  x, y, width, height, label, config = [0,0,0,0,0,0,0,0], onChange, stroke = "#000000", fill = "#ffffff", onClick 
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
      <foreignObject x={0} y={0} width={width} height={height}>
         <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2px', overflow: 'hidden', boxSizing: 'border-box' }}>
            <div style={{ fontSize: '10px', fontWeight: 'bold', marginBottom: '4px' }}>{label}</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'auto auto', gridTemplateRows: 'repeat(4, auto)', gridAutoFlow: 'column', gap: '6px 10px', justifyContent: 'center' }}>
                {config.map((bit, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', fontSize: '12px', padding: '1px', height: '12px' }}>
                        <span style={{ fontFamily: 'monospace', display: 'flex', alignItems: 'center', justifyContent: 'center', height: '12px', padding: '0 2px' }}>{i.toString(2).padStart(3, '0')}</span>
                        <button 
                            style={{ 
                                width: '12px', 
                                height: '12px', 
                                display: 'flex', 
                                alignItems: 'center', 
                                justifyContent: 'center', 
                                border: '1px solid black', 
                                borderRadius: 0,
                                fontSize: '8px', 
                                margin: 0,
                                padding: 0,
                                backgroundColor: bit ? '#3b82f6' : '#ffffff',
                                color: bit ? '#ffffff' : '#000000',
                                cursor: 'pointer'
                            }}
                            onClick={(e) => {
                                e.stopPropagation();
                                onChange && onChange(i);
                            }}
                        >
                            {bit}
                        </button>
                    </div>
                ))}
            </div>
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

export const InputButton: React.FC<{
  x: number;
  y: number;
  label: string;
  value: 0 | 1;
  onChange: (val: 0 | 1) => void;
}> = ({ x, y, label, value, onChange }) => {
  return (
    <g 
        transform={`translate(${x}, ${y})`} 
        onClick={(e) => {
            e.stopPropagation();
            onChange(value === 0 ? 1 : 0);
        }} 
        className="cursor-pointer hover:opacity-80"
    >
      <rect 
        x="-12" 
        y="-12" 
        width="24" 
        height="24" 
        fill={value ? "#3b82f6" : "#ffffff"} 
        stroke="#000000" 
        rx="4"
      />
      <text 
        dy="0.3em"
        fill={value ? "#ffffff" : "#000000"} 
        textAnchor="middle" 
        className="select-none font-bold"
        style={{ fontSize: '12px' }}
      >
        {label}
      </text>
    </g>
  );
};

export const ConnectionDot: React.FC<{
  x: number; 
  y: number;
  id?: string;
  highlighted?: boolean;
  activated?: boolean;
  onMouseEnter?: (id: string) => void;
  onMouseLeave?: () => void;
}> = ({ x, y, id, highlighted, activated, onMouseEnter, onMouseLeave }) => (
  <rect 
    x={highlighted ? x - 1 : x} 
    y={highlighted ? y - 1 : y} 
    width={highlighted ? 6 : 4} 
    height={highlighted ? 6 : 4} 
    fill={highlighted ? "#2563eb" : (activated ? "#ef4444" : "#000000")} 
    onMouseEnter={() => id && onMouseEnter && onMouseEnter(id)}
    onMouseLeave={() => onMouseLeave && onMouseLeave()}
    style={{ cursor: id ? 'pointer' : 'default' }}
  />
);

export const EllipseNode: React.FC<{cx: number, cy: number}> = ({ cx, cy }) => (
    <ellipse cx={cx} cy={cy} rx={2} ry={2} fill="#ffffff" stroke="#000000" />
);
