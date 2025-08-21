"""Production configuration overrides"""

# Override default settings for production
DEBUG = False
SECRET_KEY = 'change-this-secret-key-in-production-environment'

# Production-specific camera settings
CAMERA_DEVICE = '/dev/video0'

# Production-specific paths (if different)
# BASE_DIR = '/opt/mycobot'
# VIDEOS_DIR = '/opt/mycobot/videos'

# Production server settings
# HOST = '192.168.1.100'  # Specific IP instead of 0.0.0.0