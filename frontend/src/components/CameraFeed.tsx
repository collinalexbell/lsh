import { useState, useEffect, useRef } from 'react';
import { useRobot } from '../contexts/RobotContext';
import './CameraFeed.css';

export function CameraFeed() {
  const { state, setCameraActive } = useRobot();
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [videoStatus, setVideoStatus] = useState('');
  const [isRecordingVideo, setIsRecordingVideo] = useState(false);
  const videoRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    // Check initial camera state
    checkCameraState();
  }, []);

  // Update video stream when camera state changes
  useEffect(() => {
    if (state.cameraActive && videoRef.current) {
      reconnectVideoFeed();
    } else if (!state.cameraActive && videoRef.current) {
      videoRef.current.src = '';
    }
  }, [state.cameraActive]);

  const checkCameraState = () => {
    // Auto-reconnect video feed if camera was active
    if (videoRef.current) {
      reconnectVideoFeed();
    }
  };

  const reconnectVideoFeed = () => {
    if (videoRef.current) {
      console.log('Reconnecting video feed...');
      
      videoRef.current.onload = () => {
        console.log('Video stream connected successfully');
      };
      
      videoRef.current.onerror = (error) => {
        console.log('Video stream error:', error);
        setTimeout(() => {
          if (state.cameraActive && videoRef.current) {
            console.log('Retrying video stream connection...');
            videoRef.current.src = `/video_feed?t=${new Date().getTime()}`;
          }
        }, 1000);
      };
      
      // Force reload with cache-busting parameter
      const streamUrl = `/video_feed?t=${new Date().getTime()}`;
      console.log('Setting video src to:', streamUrl);
      videoRef.current.src = streamUrl;
    } else {
      console.log('Video ref not available');
    }
  };

  const startCamera = async () => {
    setIsStarting(true);
    try {
      const response = await fetch('/api/camera/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      
      if (data.success) {
        setCameraActive(true);
        reconnectVideoFeed();
        console.log('Camera started successfully');
      } else {
        console.error('Failed to start camera:', data.message);
      }
    } catch (error) {
      console.error('Network error:', error);
    } finally {
      setIsStarting(false);
    }
  };

  const stopCamera = async () => {
    setIsStopping(true);
    try {
      // Stop video recording if active
      if (isRecordingVideo) {
        await stopVideoRecording();
      }
      
      const response = await fetch('/api/camera/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      
      if (data.success) {
        setCameraActive(false);
        console.log('Camera stopped');
      }
    } catch (error) {
      console.error('Network error:', error);
    } finally {
      setIsStopping(false);
    }
  };

  const takeScreenshot = async () => {
    try {
      const response = await fetch('/api/camera/screenshot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      
      if (data.success) {
        // Create download link
        const link = document.createElement('a');
        link.href = data.image;
        link.download = `screenshot_${new Date().toISOString().replace(/[:.]/g, '-')}.jpg`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Refresh video stream to prevent freezing
        setTimeout(() => {
          refreshVideoStream();
        }, 500);
        
        console.log('Screenshot captured and downloaded');
      } else {
        console.error('Screenshot failed:', data.message);
      }
    } catch (error) {
      console.error('Network error:', error);
    }
  };

  const refreshVideoStream = () => {
    if (videoRef.current && state.cameraActive) {
      videoRef.current.src = `/video_feed?t=${new Date().getTime()}`;
    }
  };

  const startVideoRecording = async () => {
    try {
      const response = await fetch('/api/video/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      
      if (data.success) {
        setIsRecordingVideo(true);
        setVideoStatus(`Recording: ${data.filename}`);
        console.log('Video recording started');
      } else {
        console.error('Failed to start video recording:', data.message);
      }
    } catch (error) {
      console.error('Network error:', error);
    }
  };

  const stopVideoRecording = async () => {
    try {
      const response = await fetch('/api/video/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      
      if (data.success) {
        setIsRecordingVideo(false);
        setVideoStatus(`Recording stopped. Download: ${data.filename}`);
        console.log('Video recording stopped');
      } else {
        console.error('Failed to stop video recording:', data.message);
      }
    } catch (error) {
      console.error('Network error:', error);
    }
  };

  return (
    <div className="camera-feed">
      <h2>📹 Camera Feed</h2>
      
      <div className="video-container">
        {state.cameraActive ? (
          <img 
            ref={videoRef}
            className="video-stream" 
            alt="Camera Feed"
          />
        ) : (
          <div className="video-placeholder">
            Camera Off<br/>
            <small>Click Start Camera to begin streaming</small>
          </div>
        )}
      </div>

      <div className="camera-controls">
        <div className="camera-buttons">
          <button 
            onClick={startCamera} 
            disabled={isStarting || state.cameraActive}
            className="btn-primary"
          >
            {isStarting ? 'Starting...' : 'Start Camera'}
          </button>
          
          <button 
            onClick={stopCamera} 
            disabled={isStopping || !state.cameraActive}
            className="btn-danger"
          >
            {isStopping ? 'Stopping...' : 'Stop Camera'}
          </button>
          
          <button 
            onClick={takeScreenshot} 
            disabled={!state.cameraActive}
            className="btn-warning"
          >
            📸 Screenshot
          </button>
        </div>

        <div className="video-controls">
          <button 
            onClick={startVideoRecording} 
            disabled={!state.cameraActive || isRecordingVideo}
            className="btn-primary"
          >
            🎥 Start Recording
          </button>
          
          <button 
            onClick={stopVideoRecording} 
            disabled={!isRecordingVideo}
            className="btn-danger"
          >
            ⏹️ Stop Recording
          </button>
        </div>

        {videoStatus && (
          <div className="video-status">
            {videoStatus}
          </div>
        )}
      </div>
    </div>
  );
}