import { RobotProvider } from './contexts/RobotContext';
import { RobotController } from './components/RobotController';
import { PositionManager } from './components/PositionManager';
import { SavePosition } from './components/SavePosition';
import { CameraFeed } from './components/CameraFeed';
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
              <RobotController />
            </div>
            <div className="right-column">
              <CameraFeed />
            </div>
          </div>
        </main>
      </div>
    </RobotProvider>
  );
}

export default App;
