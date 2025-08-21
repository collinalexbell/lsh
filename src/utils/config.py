"""Configuration management"""
import os
import sys

# Add config directory to Python path
config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
sys.path.insert(0, config_dir)

try:
    from default import *
    
    # Try to import production config if it exists
    try:
        from production import *
    except ImportError:
        pass
        
except ImportError as e:
    raise ImportError(f"Could not import configuration: {e}")

def get_config():
    """Get all configuration variables as a dictionary"""
    config = {}
    for name in dir():
        if not name.startswith('_') and name.isupper():
            config[name] = globals()[name]
    return config