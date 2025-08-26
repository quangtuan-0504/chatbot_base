
import os
def _load_env():
    """Load configuration from environment variables"""
    config = {}
    for key, value in os.environ.items():
        config[key] = value
    return config

cf = _load_env()
print("Environment Variables Loaded:", cf)