import React, { createContext, useState, useContext, useCallback, useEffect } from 'react';

interface LineSegmentProps {
    baseX: number;
    baseY: number;
    points: { x: number; y: number, continuous?: boolean }[];
    value: boolean;
    colour?: string;
}

export const LineSegment = React.memo(function LineSegment({ baseX, baseY, points, value, colour }: LineSegmentProps) {
    return (
        <g>
            {points.map((point, index) => {
                if (index === 0 || point.continuous == false) {
                    return;
                }

                return (
                    <line
                        key={`${baseX}-${baseY}-${index}`}
                        x1={points[index - 1].x + baseX} y1={points[index - 1].y + baseY}
                        x2={point.x + baseX} y2={point.y + baseY}
                        stroke={value ? "#ff0000" : colour ? colour : "#333"} strokeWidth={4}
                    />
                );
            }
            )}
        </g>
    );
});