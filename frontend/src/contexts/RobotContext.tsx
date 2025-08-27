import React, { createContext, useContext, useReducer, useEffect } from 'react';
import type { RobotState, SavedPositions, PositionConfig } from '../types/robot';

interface RobotContextType {
  state: RobotState;
  updateCurrentAngles: (angles: number[]) => void;
  setLastSavedPosition: (name: string, angles: number[]) => void;
  setSavedPositions: (positions: SavedPositions, config: PositionConfig) => void;
  setCameraActive: (active: boolean) => void;
  setConnectionStatus: (status: 'connected' | 'disconnected' | 'checking') => void;
}

const RobotContext = createContext<RobotContextType | undefined>(undefined);

type RobotAction =
  | { type: 'UPDATE_CURRENT_ANGLES'; payload: number[] }
  | { type: 'SET_LAST_SAVED_POSITION'; payload: { name: string; angles: number[] } }
  | { type: 'SET_SAVED_POSITIONS'; payload: { positions: SavedPositions; config: PositionConfig } }
  | { type: 'SET_CAMERA_ACTIVE'; payload: boolean }
  | { type: 'SET_CONNECTION_STATUS'; payload: 'connected' | 'disconnected' | 'checking' };

const initialState: RobotState = {
  currentAngles: [0, 0, 0, 0, 0, 0],
  lastSavedPosition: null,
  savedPositions: {},
  positionConfig: {},
  cameraActive: false,
  isRecording: false,
  connectionStatus: 'checking',
};

function robotReducer(state: RobotState, action: RobotAction): RobotState {
  switch (action.type) {
    case 'UPDATE_CURRENT_ANGLES':
      return { ...state, currentAngles: action.payload };
    case 'SET_LAST_SAVED_POSITION':
      return { ...state, lastSavedPosition: action.payload };
    case 'SET_SAVED_POSITIONS':
      return { 
        ...state, 
        savedPositions: action.payload.positions,
        positionConfig: action.payload.config
      };
    case 'SET_CAMERA_ACTIVE':
      return { ...state, cameraActive: action.payload };
    case 'SET_CONNECTION_STATUS':
      return { ...state, connectionStatus: action.payload };
    default:
      return state;
  }
}

export function RobotProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(robotReducer, initialState);

  // Load last saved position from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem('lastSavedPosition');
      if (saved) {
        const data = JSON.parse(saved);
        if (Date.now() - data.timestamp < 24 * 60 * 60 * 1000) {
          dispatch({
            type: 'SET_LAST_SAVED_POSITION',
            payload: { name: data.name, angles: data.angles }
          });
        } else {
          localStorage.removeItem('lastSavedPosition');
        }
      }
    } catch (e) {
      console.log('Could not load from localStorage:', e);
    }
  }, []);

  const updateCurrentAngles = (angles: number[]) => {
    dispatch({ type: 'UPDATE_CURRENT_ANGLES', payload: angles });
  };

  const setLastSavedPosition = (name: string, angles: number[]) => {
    dispatch({ type: 'SET_LAST_SAVED_POSITION', payload: { name, angles } });
    
    // Persist to localStorage
    try {
      localStorage.setItem('lastSavedPosition', JSON.stringify({
        name,
        angles,
        timestamp: Date.now()
      }));
    } catch (e) {
      console.log('Could not save to localStorage:', e);
    }
  };

  const setSavedPositions = (positions: SavedPositions, config: PositionConfig) => {
    dispatch({ type: 'SET_SAVED_POSITIONS', payload: { positions, config } });
  };

  const setCameraActive = (active: boolean) => {
    dispatch({ type: 'SET_CAMERA_ACTIVE', payload: active });
  };

  const setConnectionStatus = (status: 'connected' | 'disconnected' | 'checking') => {
    dispatch({ type: 'SET_CONNECTION_STATUS', payload: status });
  };

  return (
    <RobotContext.Provider value={{
      state,
      updateCurrentAngles,
      setLastSavedPosition,
      setSavedPositions,
      setCameraActive,
      setConnectionStatus,
    }}>
      {children}
    </RobotContext.Provider>
  );
}

export function useRobot() {
  const context = useContext(RobotContext);
  if (context === undefined) {
    throw new Error('useRobot must be used within a RobotProvider');
  }
  return context;
}