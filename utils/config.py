"""
Configuration Management for Facial Recognition Attendance System
Centralized configuration settings and constants
"""

import os
from pathlib import Path
from typing import Dict, Any
import logging

class Config:
    """
    Configuration class for the attendance system
    Manages all system settings and constants
    """
    
    # Base directories
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    FACES_DIR = DATA_DIR / "faces"
    ENCODINGS_DIR = DATA_DIR / "encodings"
    ATTENDANCE_DIR = DATA_DIR / "attendance"
    LOGS_DIR = BASE_DIR / "logs"
    MODELS_DIR = BASE_DIR / "models"
    
    # Face detection settings
    FACE_DETECTION_METHODS = {
        'HAAR': {
            'name': 'Haar Cascade',
            'accuracy': 'Medium',
            'speed': 'Fast',
            'use_case': 'Real-time applications'
        },
        'HOG': {
            'name': 'HOG + Linear SVM',
            'accuracy': 'Good',
            'speed': 'Fast',
            'use_case': 'Balanced performance'
        },
        'CNN': {
            'name': 'CNN (dlib)',
            'accuracy': 'High',
            'speed': 'Slow',
            'use_case': 'High accuracy needed'
        },
        'DNN': {
            'name': 'Deep Neural Network',
            'accuracy': 'High',
            'speed': 'Medium',
            'use_case': 'Production systems'
        }
    }
    
    # Face recognition settings
    DEFAULT_TOLERANCE = 0.4
    NUM_JITTERS = 1
    FACE_ENCODING_MODEL = "large"  # or "small"
    
    # Camera settings
    DEFAULT_CAMERA_INDEX = 0
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    FPS = 30
    
    # Attendance settings
    DUPLICATE_CHECK_ENABLED = True
    AUTO_BACKUP_ENABLED = True
    BACKUP_INTERVAL_DAYS = 7
    
    # UI settings
    STREAMLIT_THEME = "light"
    PAGE_TITLE = "Facial Recognition Attendance System"
    PAGE_ICON = "🎯"
    
    # Logging settings
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = "attendance_system.log"
    
    # Performance settings
    MAX_FACES_PER_FRAME = 10
    PROCESSING_SCALE_FACTOR = 0.25
    RECOGNITION_CONFIDENCE_THRESHOLD = 0.4
    
    # Security settings
    ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp']
    MAX_IMAGE_SIZE_MB = 10
    MAX_ENCODINGS_PER_PERSON = 15
