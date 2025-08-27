export interface JointAngles {
  [key: number]: number;
}

export interface SavedPosition {
  angles: number[];
  created: string;
}

export interface SavedPositions {
  [name: string]: SavedPosition;
}

export interface PositionConfig {
  [name: string]: {
    enabled: boolean;
  };
}

export interface RobotState {
  currentAngles: number[];
  lastSavedPosition: {
    name: string;
    angles: number[];
  } | null;
  savedPositions: SavedPositions;
  positionConfig: PositionConfig;
  cameraActive: boolean;
  isRecording: boolean;
  connectionStatus: 'connected' | 'disconnected' | 'checking';
}

export interface JointLimits {
  min: number;
  max: number;
}

export const JOINT_LIMITS: JointLimits[] = [
  { min: -168, max: 168 }, // Base
  { min: -135, max: 135 }, // Shoulder
  { min: -145, max: 145 }, // Elbow
  { min: -148, max: 148 }, // Wrist 1
  { min: -168, max: 168 }, // Wrist 2
  { min: -180, max: 180 }, // Wrist 3
];

export const JOINT_NAMES = [
  'Base',
  'Shoulder', 
  'Elbow',
  'Wrist 1',
  'Wrist 2',
  'Wrist 3'
];