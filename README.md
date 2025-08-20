# MyCobot320 Web Controller 🤖

A comprehensive web-based controller for the MyCobot320 robotic arm with live webcam streaming, video recording, and advanced joint control capabilities.

## Features

### 🎯 Robot Control
- **Basic Movement**: Demo routines, home position, extend position
- **Manual Joint Control**: Real-time slider control for all 6 joints with safety limits
- **Choreography Recording**: Record and playback custom movement sequences
- **Mouse Jiggler Mode**: Continuous movement using recorded choreographies

### 📹 Camera & Media
- **Live Webcam Streaming**: Real-time video feed from connected camera
- **Screenshot Capture**: Take and download instant photos from webcam
- **Video Recording**: Record live video while controlling the robot
- **Auto Download**: Screenshots and videos automatically download to browser

### 🌐 Web Interface
- **Responsive Design**: Modern glassmorphism UI that works on desktop and mobile
- **Real-time Status**: Live joint angles, connection status, and operation feedback
- **WebSocket Integration**: Real-time updates via Socket.IO
- **Progress Tracking**: Visual feedback for all operations

### 🛡️ Safety Features
- **Joint Limits**: Software-enforced angle limits for each joint
- **Power Management**: Controlled power on/off functionality
- **Error Handling**: Comprehensive error reporting and recovery

## Requirements

- **Hardware**: MyCobot320 robotic arm
- **OS**: Raspberry Pi OS or Linux system
- **Camera**: USB webcam (tested with /dev/video0)
- **Python**: 3.8+

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd mycobot-web-controller
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Connect hardware**:
   - Connect MyCobot320 to `/dev/ttyAMA0` at 115200 baud rate
   - Connect USB webcam to `/dev/video0`

4. **Run the application**:
   ```bash
   python3 app.py
   ```

5. **Access the web interface**:
   Open `http://localhost:5000` in your browser

## Usage

### Basic Operation
1. **Start Camera**: Click "Start Camera" to begin webcam streaming
2. **Control Robot**: Use manual joint sliders or preset movements
3. **Record Movements**: Start recording, move joints manually, capture positions
4. **Playback**: Play recorded choreographies or enable jiggle mode

### Media Capture
1. **Screenshots**: Click "📸 Screenshot" while camera is active
2. **Video Recording**: Click "🎥 Start Recording", control robot, then "⏹️ Stop Recording"
3. **Downloads**: Media files automatically download to your browser

### Safety Guidelines
- Always ensure robot has clear movement space
- Use "Home Position" to return to safe starting position
- Power off robot when not in use
- Monitor joint limits displayed in the interface

## API Endpoints

### Robot Control
- `POST /api/demo` - Run demonstration sequence
- `POST /api/home` - Move to home position
- `POST /api/extend` - Move to extended position
- `POST /api/joint/move` - Move individual joint
- `POST /api/robot/power_off` - Power off robot

### Choreography
- `POST /api/record/start` - Start recording movements
- `POST /api/record/capture` - Capture current position
- `POST /api/record/stop` - Stop recording
- `POST /api/choreography/play` - Play recorded sequence
- `POST /api/choreography/clear` - Clear recorded movements

### Camera & Media
- `GET /video_feed` - MJPEG video stream
- `POST /api/camera/start` - Start camera
- `POST /api/camera/stop` - Stop camera
- `POST /api/camera/screenshot` - Capture screenshot
- `POST /api/video/start` - Start video recording
- `POST /api/video/stop` - Stop video recording
- `GET /api/video/download/<filename>` - Download recorded video

## File Structure

```
mycobot-web-controller/
├── app.py                 # Main Flask application
├── templates/
│   └── index.html        # Web interface
├── videos/               # Recorded videos (created at runtime)
├── requirements.txt      # Python dependencies
├── test_screenshot.py    # Screenshot functionality test
├── test_video_recording.py # Video recording test
└── README.md            # This file
```

## Technical Details

### Video Recording
- **Format**: MP4 (H.264)
- **Resolution**: 640x480
- **Frame Rate**: 20 FPS
- **Storage**: Local filesystem with web download

### Joint Control
- **6 DOF Control**: All MyCobot320 joints supported
- **Safety Limits**: Per-joint angle constraints
- **Real-time Feedback**: Live angle display and status updates

### Communication
- **Serial**: Direct USB/UART communication with MyCobot320
- **WebSocket**: Real-time browser updates via Socket.IO
- **REST API**: Standard HTTP endpoints for all operations

## Development & Testing

The project includes automated test scripts:

- **Screenshot Test**: `python3 test_screenshot.py`
- **Video Recording Test**: `python3 test_video_recording.py`

Tests use Playwright for browser automation and validate full functionality.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is open source. Please ensure compliance with MyCobot320 usage guidelines.

## Troubleshooting

### Robot Connection Issues
- Verify `/dev/ttyAMA0` permissions: `sudo chmod 666 /dev/ttyAMA0`
- Check baud rate setting (115200)
- Ensure robot is powered on

### Camera Issues
- Verify camera device: `ls /dev/video*`
- Test camera: `v4l2-ctl --list-devices`
- Check permissions: `sudo usermod -a -G video $USER`

### Web Interface Issues
- Clear browser cache
- Check console for JavaScript errors
- Verify Flask server is running on correct port

---

Built with ❤️ for robotics automation and remote control applications.