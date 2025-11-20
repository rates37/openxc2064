import { BoxEntity, LineEntity, Vector2 } from '../types';
import { COLORS } from '../constants';

/**
 * Clears the entire canvas.
 */
export const clearCanvas = (
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number
) => {
  ctx.clearRect(0, 0, width, height);
  // Draw background
  ctx.fillStyle = COLORS.background;
  ctx.fillRect(0, 0, width, height);
};

/**
 * Draws a subtle grid background.
 */
export const drawGrid = (
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  step: number = 50
) => {
  ctx.beginPath();
  ctx.strokeStyle = COLORS.grid;
  ctx.lineWidth = 1;

  for (let x = 0; x <= width; x += step) {
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
  }

  for (let y = 0; y <= height; y += step) {
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
  }

  ctx.stroke();
};

/**
 * Draws a filled rectangle with an optional border and label.
 */
export const drawBox = (ctx: CanvasRenderingContext2D, box: BoxEntity) => {
  const { position, size, color, label } = box;

  // Shadow for depth
  ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
  ctx.shadowBlur = 10;
  ctx.shadowOffsetX = 4;
  ctx.shadowOffsetY = 4;

  // Main Box
  ctx.fillStyle = color;
  ctx.fillRect(position.x, position.y, size.width, size.height);

  // Reset Shadow
  ctx.shadowColor = 'transparent';
  ctx.shadowBlur = 0;
  ctx.shadowOffsetX = 0;
  ctx.shadowOffsetY = 0;

  // Border
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
  ctx.lineWidth = 2;
  ctx.strokeRect(position.x, position.y, size.width, size.height);

  // Label
  if (label) {
    ctx.fillStyle = COLORS.text;
    ctx.font = '10px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(
      label,
      position.x + size.width / 2,
      position.y + size.height + 12
    );
  }
};

/**
 * Draws a line between two points.
 */
export const drawLine = (
  ctx: CanvasRenderingContext2D,
  start: Vector2,
  end: Vector2,
  color: string,
  width: number = 1
) => {
  ctx.beginPath();
  ctx.moveTo(start.x, start.y);
  ctx.lineTo(end.x, end.y);
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.stroke();
};

/**
 * Helper to draw a line entity.
 */
export const drawLineEntity = (ctx: CanvasRenderingContext2D, line: LineEntity) => {
  drawLine(ctx, line.start, line.end, line.color, line.width);
};
