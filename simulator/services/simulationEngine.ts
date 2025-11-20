import { BoxEntity, Size, Vector2 } from '../types';
import { DEFAULT_CONFIG } from '../constants';

/**
 * Generates a random set of box entities.
 */
export const generateInitialBoxes = (count: number, bounds: Size): BoxEntity[] => {
  const boxes: BoxEntity[] = [];
  for (let i = 0; i < count; i++) {
    boxes.push({
      id: `box-${i}`,
      position: {
        x: Math.random() * (bounds.width - 50),
        y: Math.random() * (bounds.height - 50),
      },
      velocity: {
        x: (Math.random() - 0.5) * DEFAULT_CONFIG.baseSpeed * 2,
        y: (Math.random() - 0.5) * DEFAULT_CONFIG.baseSpeed * 2,
      },
      size: { width: 30, height: 30 },
      color: `hsl(${Math.random() * 360}, 70%, 60%)`,
      label: `B${i}`,
    });
  }
  return boxes;
};

/**
 * Updates box positions based on velocity and handles wall collisions.
 */
export const updatePhysics = (boxes: BoxEntity[], bounds: Size): BoxEntity[] => {
  return boxes.map((box) => {
    let { x, y } = box.position;
    let { x: vx, y: vy } = box.velocity;

    x += vx;
    y += vy;

    // Wall Collision Detection
    if (x <= 0 || x + box.size.width >= bounds.width) {
      vx = -vx;
      x = Math.max(0, Math.min(x, bounds.width - box.size.width));
    }
    if (y <= 0 || y + box.size.height >= bounds.height) {
      vy = -vy;
      y = Math.max(0, Math.min(y, bounds.height - box.size.height));
    }

    return {
      ...box,
      position: { x, y },
      velocity: { x: vx, y: vy },
    };
  });
};

/**
 * Calculates dynamic lines based on proximity (Distance check).
 * This simulates a "network" or "constellation" effect.
 */
export const calculateProximityLines = (boxes: BoxEntity[]): Array<{ start: Vector2; end: Vector2; opacity: number }> => {
  const lines = [];
  const threshold = DEFAULT_CONFIG.connectionDistance;

  for (let i = 0; i < boxes.length; i++) {
    for (let j = i + 1; j < boxes.length; j++) {
      const b1 = boxes[i];
      const b2 = boxes[j];

      // Center points
      const c1 = { x: b1.position.x + b1.size.width / 2, y: b1.position.y + b1.size.height / 2 };
      const c2 = { x: b2.position.x + b2.size.width / 2, y: b2.position.y + b2.size.height / 2 };

      const dx = c1.x - c2.x;
      const dy = c1.y - c2.y;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist < threshold) {
        // Opacity based on distance (closer = more opaque)
        const opacity = 1 - dist / threshold;
        lines.push({ start: c1, end: c2, opacity });
      }
    }
  }
  return lines;
};
