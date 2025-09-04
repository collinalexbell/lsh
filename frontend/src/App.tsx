import { RobotProvider } from './contexts/RobotContext';
import { RobotController } from './components/RobotController';
import { PositionManager } from './components/PositionManager';
import { SavePosition } from './components/SavePosition';
import { ProcedureManager } from './components/ProcedureManager';
import { CreateProcedure } from './components/CreateProcedure';
import { CameraFeed } from './components/CameraFeed';
import { AprilTagDetector } from './components/AprilTagDetector';
import { WallCalibration } from './components/WallCalibration';
// import EndEffectorController from './components/EndEffectorController'; // Removed from app
import './App.css';

function App() {
  return (
    <RobotProvider>
      <div className="app">
        <header className="app-header">
          <h1>🤖 MyCobot320 Web Controller</h1>
          <p>React-powered robot control with individual servo reset functionality</p>
        </header>
        
        <main className="app-main">
          <div className="app-grid">
            <div className="left-column">
              <PositionManager />
              <SavePosition />
              <ProcedureManager />
              <CreateProcedure />
              <WallCalibration />
              <RobotController />
            </div>
            <div className="right-column">
              <CameraFeed />
              <AprilTagDetector />
            </div>
          </div>
        </main>
      </div>
    </RobotProvider>
  );
}

export default App;
