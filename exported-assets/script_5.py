# Create utility modules

# 1. Configuration module - utils/config.py
config_py_code = '''
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
'''

# 2. Database utility module - utils/database.py
database_py_code = '''
"""
Database Management for Attendance System
Handles CSV-based data storage and retrieval
"""

import csv
import sqlite3
import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import datetime
import logging
from utils.config import Config

class Database:
    """
    Database interface for the attendance system
    Supports both CSV and SQLite backends
    """
    
    def __init__(self, db_type: str = "csv"):
        """
        Initialize database connection
        
        Args:
            db_type: Database type ("csv" or "sqlite")
        """
        self.db_type = db_type
        self.config = Config()
        self.db_path = self.config.DATA_DIR / "attendance_system.db"
        
        if db_type == "sqlite":
            self._init_sqlite()
        else:
            self._init_csv()
    
    def _init_sqlite(self):
        """Initialize SQLite database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create people table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS people (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    person_id TEXT,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Create attendance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id INTEGER,
                    name TEXT NOT NULL,
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    day_of_week TEXT,
                    status TEXT DEFAULT 'Present',
                    entry_type TEXT DEFAULT 'automatic',
                    FOREIGN KEY (person_id) REFERENCES people (id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_name ON attendance(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_timestamp ON attendance(timestamp)')
            
            conn.commit()
            conn.close()
            
            logging.info("SQLite database initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing SQLite database: {str(e)}")
            raise
    
    def _init_csv(self):
        """Initialize CSV-based storage"""
        # Create people registry file if it doesn't exist
        people_file = self.config.DATA_DIR / "people_registry.csv"
        
        if not people_file.exists():
            with open(people_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['name', 'person_id', 'date_added', 'active'])
        
        logging.info("CSV database initialized successfully")
    
    def add_person(self, name: str, person_id: Optional[str] = None) -> bool:
        """
        Add a new person to the database
        
        Args:
            name: Person's name
            person_id: Optional person ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.db_type == "sqlite":
                return self._add_person_sqlite(name, person_id)
            else:
                return self._add_person_csv(name, person_id)
        except Exception as e:
            logging.error(f"Error adding person {name}: {str(e)}")
            return False
    
    def _add_person_sqlite(self, name: str, person_id: Optional[str] = None) -> bool:
        """Add person using SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO people (name, person_id) VALUES (?, ?)",
                (name, person_id)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            logging.warning(f"Person {name} already exists in database")
            return False
        finally:
            conn.close()
    
    def _add_person_csv(self, name: str, person_id: Optional[str] = None) -> bool:
        """Add person using CSV"""
        people_file = self.config.DATA_DIR / "people_registry.csv"
        
        # Check if person already exists
        if self._person_exists_csv(name):
            logging.warning(f"Person {name} already exists in database")
            return False
        
        # Add new person
        with open(people_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                name,
                person_id or "",
                datetime.datetime.now().isoformat(),
                "True"
            ])
        
        return True
    
    def remove_person(self, name: str) -> bool:
        """
        Remove a person from the database
        
        Args:
            name: Person's name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.db_type == "sqlite":
                return self._remove_person_sqlite(name)
            else:
                return self._remove_person_csv(name)
        except Exception as e:
            logging.error(f"Error removing person {name}: {str(e)}")
            return False
    
    def _remove_person_sqlite(self, name: str) -> bool:
        """Remove person using SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE people SET active = 0 WHERE name = ?", (name,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def _remove_person_csv(self, name: str) -> bool:
        """Remove person using CSV"""
        people_file = self.config.DATA_DIR / "people_registry.csv"
        temp_file = people_file.with_suffix('.tmp')
        
        found = False
        
        with open(people_file, 'r', encoding='utf-8') as infile, \
             open(temp_file, 'w', newline='', encoding='utf-8') as outfile:
            
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            
            for row in reader:
                if len(row) > 0 and row[0] != name:
                    writer.writerow(row)
                elif len(row) > 0 and row[0] == name:
                    found = True
        
        if found:
            temp_file.replace(people_file)
            return True
        else:
            temp_file.unlink()
            return False
    
    def get_all_people(self) -> List[Tuple[str, str, str]]:
        """
        Get all registered people
        
        Returns:
            List of tuples (name, person_id, date_added)
        """
        try:
            if self.db_type == "sqlite":
                return self._get_all_people_sqlite()
            else:
                return self._get_all_people_csv()
        except Exception as e:
            logging.error(f"Error getting all people: {str(e)}")
            return []
    
    def _get_all_people_sqlite(self) -> List[Tuple[str, str, str]]:
        """Get all people using SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT name, person_id, date_added FROM people WHERE active = 1"
            )
            return cursor.fetchall()
        finally:
            conn.close()
    
    def _get_all_people_csv(self) -> List[Tuple[str, str, str]]:
        """Get all people using CSV"""
        people_file = self.config.DATA_DIR / "people_registry.csv"
        people = []
        
        if people_file.exists():
            with open(people_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('active', 'True').lower() == 'true':
                        people.append((
                            row['name'],
                            row.get('person_id', ''),
                            row.get('date_added', '')
                        ))
        
        return people
    
    def _person_exists_csv(self, name: str) -> bool:
        """Check if person exists in CSV database"""
        people_file = self.config.DATA_DIR / "people_registry.csv"
        
        if not people_file.exists():
            return False
        
        with open(people_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['name'].lower() == name.lower() and row.get('active', 'True').lower() == 'true':
                    return True
        
        return False
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """
        Create a backup of the database
        
        Args:
            backup_path: Optional custom backup path
            
        Returns:
            Path to the backup file
        """
        if backup_path is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.config.DATA_DIR / f"backup_{timestamp}"
        
        backup_dir = Path(backup_path)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            import shutil
            
            if self.db_type == "sqlite":
                # Copy SQLite database
                shutil.copy2(self.db_path, backup_dir / "attendance_system.db")
            else:
                # Copy all CSV files
                for csv_file in self.config.DATA_DIR.glob("*.csv"):
                    shutil.copy2(csv_file, backup_dir)
            
            # Copy encodings
            encodings_dir = backup_dir / "encodings"
            encodings_dir.mkdir(exist_ok=True)
            
            for encoding_file in self.config.ENCODINGS_DIR.glob("*"):
                shutil.copy2(encoding_file, encodings_dir)
            
            logging.info(f"Database backed up to {backup_dir}")
            return str(backup_dir)
            
        except Exception as e:
            logging.error(f"Error creating database backup: {str(e)}")
            raise
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {
            'database_type': self.db_type,
            'total_people': len(self.get_all_people()),
            'database_size': 0
        }
        
        try:
            if self.db_type == "sqlite" and self.db_path.exists():
                stats['database_size'] = self.db_path.stat().st_size
            else:
                # Calculate total size of CSV files
                total_size = 0
                for csv_file in self.config.DATA_DIR.glob("*.csv"):
                    total_size += csv_file.stat().st_size
                stats['database_size'] = total_size
        except Exception as e:
            logging.error(f"Error calculating database stats: {str(e)}")
        
        return stats
'''

print("Config Module (utils/config.py) created successfully!")
print("File size:", len(config_py_code), "characters")
print("\nDatabase Module (utils/database.py) created successfully!")
print("File size:", len(database_py_code), "characters")