import { useState, useEffect, useRef } from 'react';
import { useRobot } from '../contexts/RobotContext';
import './AprilTagDetector.css';

interface AprilTagDetection {
  tag_id: number;
  center: [number, number];
  corners: number[][];
  distance_cm?: number;
  distance_meters?: number;
  distance_inches?: number;
  hamming: number;
  decision_margin: number;
  pose?: {
    translation: number[];
    rotation_vector: number[];
    distance_from_pose: number;
  };
}

interface AprilTagConfig {
  tag_size_mm: number;
  camera_resolution: {
    width: number;
    height: number;
  };
  focal_length: number;
}

export function AprilTagDetector() {
  const { state } = useRobot();
  const [detections, setDetections] = useState<AprilTagDetection[]>([]);
  const [config, setConfig] = useState<AprilTagConfig | null>(null);
  const [tagSizeMm, setTagSizeMm] = useState(50); // 50mm default
  const [isDetecting, setIsDetecting] = useState(false);
  const [actualDistance, setActualDistance] = useState('');
  const [showCalibration, setShowCalibration] = useState(false);
  const [detectionImage, setDetectionImage] = useState<string | null>(null);
  const [autoDetect, setAutoDetect] = useState(false);
  const intervalRef = useRef<number | null>(null);

  // Load configuration on mount
  useEffect(() => {
    loadConfig();
  }, []);

  // Auto-detection loop
  useEffect(() => {
    if (autoDetect && state.cameraActive) {
      intervalRef.current = setInterval(detectTags, 1000); // Detect every 1 second
      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
  }, [autoDetect, state.cameraActive]);

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/apriltag/config');
      const data = await response.json();
      
      if (data.success) {
        setConfig(data.config);
        setTagSizeMm(data.config.tag_size_mm);
      }
    } catch (error) {
      console.error('Failed to load AprilTag config:', error);
    }
  };

  const updateTagSize = async () => {
    try {
      const response = await fetch('/api/apriltag/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tag_size_mm: tagSizeMm
        })
      });
      
      const data = await response.json();
      if (data.success) {
        console.log('Tag size updated to', data.tag_size_mm, 'mm');
        await loadConfig(); // Reload config
      } else {
        console.error('Failed to update tag size:', data.message);
      }
    } catch (error) {
      console.error('Network error:', error);
    }
  };

  const detectTags = async () => {
    if (!state.cameraActive) {
      console.log('Camera not active');
      return;
    }

    setIsDetecting(true);
    
    try {
      // Get image with detections
      const response = await fetch('/api/apriltag/image');
      const data = await response.json();
      
      if (data.success) {
        setDetections(data.detections);
        setDetectionImage(data.image);
        console.log(`Detected ${data.count} AprilTags`);
      } else {
        console.error('Detection failed:', data.message);
        setDetections([]);
        setDetectionImage(null);
      }
    } catch (error) {
      console.error('Network error:', error);
      setDetections([]);
      setDetectionImage(null);
    } finally {
      setIsDetecting(false);
    }
  };

  const calibrateDistance = async () => {
    const distance = parseFloat(actualDistance);
    if (!distance || distance <= 0) {
      alert('Please enter a valid distance in cm');
      return;
    }

    try {
      const response = await fetch('/api/apriltag/calibrate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          actual_distance_cm: distance
        })
      });
      
      const data = await response.json();
      if (data.success) {
        alert(`Calibration successful! Correction factor: ${data.correction_factor.toFixed(3)}`);
        await loadConfig(); // Reload config
        setShowCalibration(false);
        setActualDistance('');
        // Re-detect to show updated measurements
        await detectTags();
      } else {
        alert('Calibration failed: ' + data.message);
      }
    } catch (error) {
      console.error('Network error:', error);
      alert('Network error during calibration');
    }
  };

  const formatDistance = (detection: AprilTagDetection) => {
    if (!detection.distance_cm) return 'N/A';
    
    const cm = detection.distance_cm;
    const inches = detection.distance_inches || 0;
    return `${cm.toFixed(1)}cm (${inches.toFixed(1)}in)`;
  };

  const formatPose = (detection: AprilTagDetection) => {
    if (!detection.pose) return null;
    
    const [x, y, z] = detection.pose.translation;
    return `X:${(x*100).toFixed(1)} Y:${(y*100).toFixed(1)} Z:${(z*100).toFixed(1)}cm`;
  };

  return (
    <div className="apriltag-detector">
      <div className="apriltag-header">
        <h2>🏷️ AprilTag Detection</h2>
        <div className="apriltag-controls">
          <button
            onClick={() => setAutoDetect(!autoDetect)}
            className={`btn-small ${autoDetect ? 'btn-warning' : 'btn-secondary'}`}
            title={autoDetect ? 'Stop auto-detection' : 'Start auto-detection'}
            disabled={!state.cameraActive}
          >
            {autoDetect ? '⏸️' : '▶️'}
          </button>
          <button
            onClick={detectTags}
            disabled={isDetecting || !state.cameraActive}
            className="btn-primary btn-small"
            title="Detect AprilTags now"
          >
            {isDetecting ? '🔄' : '🔍'}
          </button>
        </div>
      </div>

      {!state.cameraActive && (
        <div className="apriltag-notice">
          <p>📹 Start the camera to begin AprilTag detection</p>
        </div>
      )}

      {/* Configuration Section */}
      <div className="apriltag-config">
        <h3>Configuration</h3>
        <div className="config-controls">
          <div className="config-item">
            <label>Tag Size (mm):</label>
            <input
              type="number"
              value={tagSizeMm}
              onChange={(e) => setTagSizeMm(parseFloat(e.target.value) || 50)}
              min="1"
              max="1000"
              className="tag-size-input"
            />
            <button onClick={updateTagSize} className="btn-secondary btn-small">
              Update
            </button>
          </div>
          
          <div className="config-item">
            <button
              onClick={() => setShowCalibration(!showCalibration)}
              className="btn-secondary"
            >
              📏 Calibrate Distance
            </button>
          </div>
        </div>

        {config && (
          <div className="config-info">
            <p>Camera: {config.camera_resolution.width}×{config.camera_resolution.height}</p>
            <p>Focal Length: {config.focal_length.toFixed(1)} pixels</p>
          </div>
        )}

        {/* Calibration Panel */}
        {showCalibration && (
          <div className="calibration-panel">
            <h4>Distance Calibration</h4>
            <p>Place AprilTag at a known distance and enter the actual distance:</p>
            <div className="calibration-controls">
              <input
                type="number"
                value={actualDistance}
                onChange={(e) => setActualDistance(e.target.value)}
                placeholder="Distance in cm"
                className="distance-input"
              />
              <button onClick={calibrateDistance} className="btn-primary">
                Calibrate
              </button>
              <button 
                onClick={() => setShowCalibration(false)} 
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detection Results */}
      {detections.length > 0 && (
        <div className="detection-results">
          <h3>Detected Tags ({detections.length})</h3>
          <div className="detection-list">
            {detections.map((detection, index) => (
              <div key={index} className="detection-item">
                <div className="detection-header">
                  <span className="tag-id">ID: {detection.tag_id}</span>
                  <span className="tag-distance">{formatDistance(detection)}</span>
                </div>
                <div className="detection-details">
                  <p>Center: ({detection.center[0].toFixed(1)}, {detection.center[1].toFixed(1)})</p>
                  <p>Quality: H:{detection.hamming} M:{detection.decision_margin.toFixed(2)}</p>
                  {detection.pose && (
                    <p>Pose: {formatPose(detection)}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Detection Image */}
      {detectionImage && (
        <div className="detection-image">
          <h3>Detection Visualization</h3>
          <img 
            src={detectionImage} 
            alt="AprilTag Detection" 
            className="detection-img"
          />
        </div>
      )}

      {/* No Detections Message */}
      {state.cameraActive && detections.length === 0 && !isDetecting && detectionImage && (
        <div className="no-detections">
          <p>📋 No AprilTags detected in current frame</p>
          <p>Make sure tags are visible and properly lit</p>
        </div>
      )}
    </div>
  );
}