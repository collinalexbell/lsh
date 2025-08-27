# MyCobot320 React Web Controller 🤖

A modern, React-powered web controller for the MyCobot320 robotic arm featuring individual servo reset functionality, sticky camera interface, and comprehensive robot control capabilities.

## ✨ Key Features

### 🎯 Advanced Robot Control
- **Individual Servo Reset**: Reset any joint to its last saved position with dedicated reset buttons
- **Manual Joint Control**: Real-time slider control for all 6 joints with safety limits  
- **Smart Position Management**: Save, load, and manage named robot positions
- **Basic Movements**: Demo routines, home position, extend position with one-click execution
- **Live Angle Feedback**: Real-time display of current joint positions

### 📹 Sticky Camera Interface
- **Floating Camera Feed**: Camera follows you while scrolling, stays visible in top-right corner
- **Smart Controls**: Minimize/expand, sticky toggle, and scroll-to-top functionality
- **Live Video Stream**: Real-time MJPEG feed with automatic reconnection
- **Screenshot Capture**: Instant photo capture with auto-download and stream refresh
- **Video Recording**: Record robot operations with start/stop controls
- **Mobile Responsive**: Adaptive camera interface for all screen sizes

### ⚛️ Modern React Architecture
- **TypeScript Frontend**: Type-safe React components with modern hooks
- **Reactive State Management**: Context-based state eliminates DOM manipulation issues
- **Component-Based Design**: Modular, maintainable, and extensible codebase
- **Vite Build System**: Fast development and optimized production builds
- **Real-time Updates**: Automatic UI updates when robot state changes

### 🛡️ Safety & Reliability
- **Joint Limits**: Software-enforced angle constraints for each servo
- **Error Recovery**: Automatic reconnection for video streams and robot communication
- **Power Management**: Safe robot power control with status feedback
- **Position Validation**: Input validation and safety checks for all movements

## 🚀 Quick Start

### Prerequisites
- **Hardware**: MyCobot320 robotic arm
- **OS**: Raspberry Pi OS or Linux system with camera support
- **Node.js**: 18+ (for React development)
- **Python**: 3.8+ (for robot control backend)

### Installation

1. **Clone and setup**:
   ```bash
   git clone https://github.com/collinalexbell/lsh.git
   cd lsh
   pip install -r requirements.txt
   ```

2. **Hardware connections**:
   - MyCobot320 → `/dev/ttyAMA0` (115200 baud)
   - USB Camera → `/dev/video0`

3. **Start the application**:
   ```bash
   python -m src.main
   ```

4. **Access the interface**:
   Open `http://localhost:5000` or `http://[your-device-ip]:5000`

## 🎮 How to Use

### Individual Servo Reset (Key Feature)
1. **Move to any saved position** using the blue position buttons
2. **Adjust individual servos** using the manual control sliders  
3. **Click orange RESET buttons** next to any joint to restore it to the saved position
4. **Reset buttons persist** across page reloads for 24 hours

### Sticky Camera Operation
1. **Start camera** and begin scrolling down the page
2. **Camera automatically follows** - becomes sticky in top-right corner
3. **Use controls**: 📌 (toggle sticky), ⬇️ (minimize), ⬆️ (scroll to top)
4. **Full functionality maintained** - screenshot and recording work in sticky mode

### Position Management
1. **Create positions**: Move robot manually → enter name → save current position  
2. **Quick access**: Use saved position buttons for instant movement
3. **Enable/disable**: Configure which positions appear in interface
4. **Individual reset**: Use reset buttons to restore specific joints

## 🏗️ Architecture

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── CameraFeed.tsx   # Sticky camera with controls
│   │   ├── JointControl.tsx # Individual servo with reset button
│   │   ├── RobotController.tsx # Main robot interface
│   │   ├── PositionManager.tsx # Saved positions
│   │   └── SavePosition.tsx # Position creation
│   ├── contexts/
│   │   └── RobotContext.tsx # Global state management
│   └── types/
│       └── robot.ts         # TypeScript definitions
├── package.json             # Node.js dependencies
├── vite.config.ts          # Build configuration
└── dist/ → static/react-build/ # Production build
```

### Backend (Flask + Python)
```
src/
├── api/                     # REST API routes
│   ├── robot_routes.py     # Robot movement endpoints
│   ├── camera_routes.py    # Camera and video endpoints
│   ├── position_routes.py  # Position management
│   └── react_routes.py     # Frontend serving
├── services/               # Business logic
│   ├── robot_controller.py # MyCobot320 interface
│   ├── camera_service.py   # Video streaming
│   └── position_service.py # Position storage
└── main.py                 # Application entry point
```

## 🔌 API Reference

### Robot Control
- `GET /api/joints/get_current` - Get current joint angles
- `POST /api/joint/move` - Move individual joint
- `POST /api/demo` - Run demonstration sequence  
- `POST /api/home` - Move to home position
- `POST /api/extend` - Move to extended position

### Position Management
- `GET /api/positions` - Get all saved positions
- `POST /api/positions/save` - Save current position
- `POST /api/positions/move_to/<name>` - Move to saved position
- `POST /api/positions/delete` - Delete position

### Camera & Media
- `GET /video_feed` - MJPEG video stream
- `POST /api/camera/start` - Start camera stream
- `POST /api/camera/stop` - Stop camera stream  
- `POST /api/camera/screenshot` - Capture screenshot
- `POST /api/video/start` - Start video recording
- `POST /api/video/stop` - Stop video recording

## 🔧 Development

### Frontend Development
```bash
cd frontend
npm install
npm run dev    # Development server with hot reload
npm run build  # Production build
```

### React Component Development  
- **State Management**: Use `useRobot()` hook for global state
- **TypeScript**: All components are fully typed
- **Styling**: CSS modules with responsive design
- **Testing**: Components designed for easy testing

### Backend Development
- **Modular Architecture**: Clean separation of concerns
- **Error Handling**: Comprehensive error reporting
- **Real-time Updates**: WebSocket support via Socket.IO
- **API Documentation**: RESTful endpoints with clear responses

## 📱 Responsive Design

### Desktop Experience
- **Two-column layout**: Robot controls left, sticky camera right
- **Full feature set**: All functionality accessible
- **Keyboard shortcuts**: Enhanced productivity features

### Mobile Experience  
- **Single-column layout**: Optimized for touch interaction
- **Sticky camera bar**: Full-width camera at top when scrolling
- **Touch-friendly controls**: Large buttons and gesture support

## 🚀 Advanced Features

### Individual Servo Reset System
- **Smart tracking**: Automatically remembers last used saved position
- **Persistent storage**: Uses localStorage with 24-hour expiry
- **Visual feedback**: Orange reset buttons with tooltips
- **Selective reset**: Reset any combination of joints independently

### Sticky Camera Technology
- **Scroll detection**: Activates after 100px scroll
- **Smooth transitions**: CSS animations for professional feel
- **State preservation**: Maintains all camera functionality when sticky
- **User preferences**: Toggle sticky behavior on/off

### Position Management
- **JSON storage**: Positions saved in `saved_positions.json`
- **Configuration system**: Enable/disable positions in `position_config.json`
- **Real-time updates**: UI updates immediately when positions change

## 🧪 Testing

Automated test suite included:
```bash
python3 test_screenshot.py      # Screenshot functionality
python3 test_video_recording.py # Video capture  
python3 test_camera_freeze.py   # Stream reliability
```

## 🔗 Legacy Support

Original jQuery interface available at:
- **Main controller**: `http://localhost:5000/legacy`
- **Position management**: `http://localhost:5000/legacy/positions`  
- **Command center**: `http://localhost:5000/legacy/command-center`

## ⚠️ Troubleshooting

### React App Issues
- **Build errors**: Run `cd frontend && npm install && npm run build`
- **TypeScript errors**: Check component imports and types
- **State issues**: Verify React Context provider is wrapping components

### Robot Connection
- **Permission**: `sudo chmod 666 /dev/ttyAMA0`
- **Baud rate**: Ensure 115200 baud rate setting
- **Power**: Verify robot is powered on and connected

### Camera Problems  
- **Device access**: Check `/dev/video*` permissions
- **Stream freezing**: Refresh page or restart camera service
- **Mobile issues**: Try landscape orientation for better experience

### Performance Optimization
- **Slow UI**: Check browser console for errors
- **Memory usage**: Restart Flask server if running for extended periods
- **Network latency**: Use device IP instead of localhost for remote access

## 🤝 Contributing

1. **Fork** the repository
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Frontend changes**: Work in `frontend/src/` with TypeScript
4. **Backend changes**: Follow Flask blueprint patterns in `src/api/`  
5. **Test thoroughly**: Use provided test scripts
6. **Submit PR**: Include description of changes and testing performed

## 🏆 What's New in React Version

### Major Improvements
- **✅ Individual servo reset buttons** - The core requested feature
- **✅ Sticky camera interface** - Follows you while scrolling
- **✅ Modern React architecture** - Eliminates DOM manipulation issues
- **✅ TypeScript support** - Type-safe development
- **✅ Mobile responsive** - Works perfectly on all devices
- **✅ Better error handling** - Graceful failure and recovery
- **✅ Component modularity** - Easy to extend and maintain

### Performance Benefits
- **Faster rendering** with React's virtual DOM
- **Optimized builds** with Vite bundling
- **Reduced network requests** with efficient state management
- **Better caching** with modern build tools

---

**Built with ❤️ using React, TypeScript, and modern web technologies for seamless robot control.**