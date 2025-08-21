"""Default configuration for MyCobot320 Web Controller"""
import os

# Flask Configuration
SECRET_KEY = 'mycobot-web-controller-secret-change-in-production'
DEBUG = True

# Robot Configuration
ROBOT_PORT = "/dev/ttyAMA0"
ROBOT_BAUDRATE = 115200

# File Paths
BASE_DIR = '/home/er/lsh'
POSITIONS_FILE = os.path.join(BASE_DIR, 'saved_positions.json')
CONFIG_FILE = os.path.join(BASE_DIR, 'position_config.json')
VIDEOS_DIR = os.path.join(BASE_DIR, 'videos')

# Camera Configuration
CAMERA_DEVICE = '/dev/video0'
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# Video Recording
VIDEO_CODEC = 'mp4v'
VIDEO_FPS = 20.0

# Robot Limits and Positions
ANGLE_LIMITS = [
    (-168, 168),  # Joint 1
    (-135, 135),  # Joint 2
    (-145, 145),  # Joint 3
    (-148, 148),  # Joint 4
    (-168, 168),  # Joint 5
    (-180, 180),  # Joint 6
]

HOME_POSITION = [7.11, -135, 142.91, 36.56, 83.67, -0.79]
EXTEND_POSITION = [0, 0, 0, 0, 0, 0]

# Server Configuration
HOST = '0.0.0.0'
PORT = 5000

# SocketIO Configuration
CORS_ALLOWED_ORIGINS = "*"