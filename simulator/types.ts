export interface Vector2 {
  x: number;
  y: number;
}

export interface Size {
  width: number;
  height: number;
}

export interface BoxEntity {
  id: string;
  position: Vector2;
  velocity: Vector2;
  size: Size;
  color: string;
  label?: string;
}

export interface LineEntity {
  id: string;
  start: Vector2;
  end: Vector2;
  color: string;
  width: number;
}

export interface SimulationState {
  boxes: BoxEntity[];
  lines: LineEntity[]; // Static lines or specific connectors
  time: number;
  isRunning: boolean;
}

export enum SimulationMode {
  IDLE = 'IDLE',
  RUNNING = 'RUNNING',
  PAUSED = 'PAUSED',
}

export interface GeneratorConfig {
  boxCount: number;
  maxSpeed: number;
  canvasSize: Size;
}