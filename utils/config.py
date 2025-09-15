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

    @classmethod
    def get_face_detection_config(cls, method: str = "HOG") -> Dict[str, Any]:
        """Get configuration for specific face detection method"""
        method = method.upper()
        
        base_config = {
            'method': method,
            'min_face_size': (30, 30),
            'scale_factor': 1.1,
            'min_neighbors': 5
        }
        
        if method == "HAAR":
            base_config.update({
                'cascade_file': 'haarcascade_frontalface_default.xml'
            })
        elif method == "HOG":
            base_config.update({
                'upsampling': 1
            })
        elif method == "CNN":
            base_config.update({
                'upsampling': 1,
                'confidence_threshold': 0.5
            })
        elif method == "DNN":
            base_config.update({
                'input_size': (300, 300),
                'mean_values': [104, 117, 123],
                'confidence_threshold': 0.7
            })
        
        return base_config
    
    @classmethod
    def setup_directories(cls):
        """Create necessary directories if they don't exist"""
        directories = [
            cls.DATA_DIR,
            cls.FACES_DIR,
            cls.ENCODINGS_DIR,
            cls.ATTENDANCE_DIR,
            cls.LOGS_DIR,
            cls.MODELS_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            'type': 'csv',  # or 'sqlite', 'mysql'
            'attendance_file_pattern': 'attendance_{date}.csv',
            'encoding_file': 'face_encodings.pkl',
            'names_file': 'face_names.pkl'
        }
    
    @classmethod
    def get_camera_config(cls) -> Dict[str, Any]:
        """Get camera configuration"""
        return {
            'index': cls.DEFAULT_CAMERA_INDEX,
            'width': cls.FRAME_WIDTH,
            'height': cls.FRAME_HEIGHT,
            'fps': cls.FPS,
            'buffer_size': 1
        }
    
    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            'level': cls.LOG_LEVEL,
            'format': cls.LOG_FORMAT,
            'file': cls.LOGS_DIR / cls.LOG_FILE,
            'max_bytes': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5
        }

# Environment-specific configurations
class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    LOG_LEVEL = logging.DEBUG
    DEFAULT_TOLERANCE = 0.5  # More lenient for testing
    
class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    LOG_LEVEL = logging.WARNING
    DEFAULT_TOLERANCE = 0.35  # More strict for production
    AUTO_BACKUP_ENABLED = True
    
class TestingConfig(Config):
    """Testing environment configuration"""
    DEBUG = True
    LOG_LEVEL = logging.DEBUG
    FACES_DIR = Config.BASE_DIR / "test_data" / "faces"
    ATTENDANCE_DIR = Config.BASE_DIR / "test_data" / "attendance"
