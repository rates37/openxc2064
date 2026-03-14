import React from 'react';

interface LineSegmentProps {
    baseX: number;
    baseY: number;
    points: { x: number; y: number, continuous?: boolean }[];
    value: boolean;
    colour?: string;
}

export const LineSegment = React.memo(function LineSegment({ baseX, baseY, points, value, colour }: LineSegmentProps) {
    if (points.length < 2) return null;
    
    // Build a single path string instead of multiple <line> elements
    const strokeColor = value ? "#ff0000" : colour ? colour : "#333";
    
    let pathData = '';
    let isNewSegment = true;
    
    for (let i = 0; i < points.length; i++) {
        const point = points[i];
        const x = point.x + baseX;
        const y = point.y + baseY;
        
        if (point.continuous === false || isNewSegment) {
            pathData += `M${x},${y}`;
            isNewSegment = false;
        } else {
            pathData += `L${x},${y}`;
        }
        
        // Check if next point starts a new segment
        if (i < points.length - 1 && points[i + 1].continuous === false) {
            isNewSegment = true;
        }
    }
    
    return (
        <path
            d={pathData}
            stroke={strokeColor}
            strokeWidth={4}
            fill="none"
            shapeRendering="geometricPrecision"
        />
    );
}, (prevProps, nextProps) => {
    // Custom comparison - only re-render if value or points change
    return prevProps.value === nextProps.value &&
           prevProps.baseX === nextProps.baseX &&
           prevProps.baseY === nextProps.baseY &&
           prevProps.colour === nextProps.colour &&
           prevProps.points === nextProps.points;
});