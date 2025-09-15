"""
Helper Functions for Facial Recognition Attendance System
Common utility functions used across the application
"""

import os
import logging
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import cv2
import numpy as np
from PIL import Image
import streamlit as st

def setup_directories():
    """Create necessary directories for the application"""
    directories = [
        "data",
        "data/faces", 
        "data/encodings",
        "data/attendance",
        "logs",
        "models",
        "assets/images"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def setup_logging(log_file: str = "logs/attendance_system.log", 
                 level: int = logging.INFO):
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def log_activity(message: str, level: str = "info"):
    """Log activity with specified level"""
    logger = logging.getLogger(__name__)
    
    if level.lower() == "debug":
        logger.debug(message)
    elif level.lower() == "info":
        logger.info(message)
    elif level.lower() == "warning":
        logger.warning(message)
    elif level.lower() == "error":
        logger.error(message)
    elif level.lower() == "critical":
        logger.critical(message)

def validate_image(image_path: str) -> bool:
    """
    Validate if the image file is valid and readable
    
    Args:
        image_path: Path to the image file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            return False
        
        # Check file extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        file_ext = Path(image_path).suffix.lower()
        
        if file_ext not in valid_extensions:
            return False
        
        # Try to load the image
        image = cv2.imread(image_path)
        
        if image is None:
            return False
        
        # Check if image has valid dimensions
        if image.shape[0] < 10 or image.shape[1] < 10:
            return False
        
        return True
        
    except Exception:
        return False

def resize_image(image: np.ndarray, 
                max_width: int = 800, 
                max_height: int = 600) -> np.ndarray:
    """
    Resize image while maintaining aspect ratio
    
    Args:
        image: Input image as numpy array
        max_width: Maximum width
        max_height: Maximum height
        
    Returns:
        Resized image
    """
    h, w = image.shape[:2]
    
    # Calculate scaling factor
    scale_w = max_width / w
    scale_h = max_height / h
    scale = min(scale_w, scale_h, 1.0)  # Don't upscale
    
    if scale < 1.0:
        new_w = int(w * scale)
        new_h = int(h * scale)
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    return image

def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes"""
    try:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    except:
        return 0.0

def create_thumbnail(image_path: str, 
                    thumbnail_path: str,
                    size: Tuple[int, int] = (150, 150)):
    """
    Create thumbnail of an image
    
    Args:
        image_path: Path to original image
        thumbnail_path: Path to save thumbnail
        size: Thumbnail size (width, height)
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create thumbnail
            img.thumbnail(size, Image.LANCZOS)
            
            # Save thumbnail
            img.save(thumbnail_path, 'JPEG', quality=85)
            
    except Exception as e:
        logging.error(f"Error creating thumbnail: {str(e)}")

def format_timestamp(timestamp: datetime.datetime) -> str:
    """Format timestamp for display"""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def get_current_date_string() -> str:
    """Get current date as string"""
    return datetime.date.today().strftime("%Y-%m-%d")

def get_current_time_string() -> str:
    """Get current time as string"""
    return datetime.datetime.now().strftime("%H:%M:%S")

def calculate_face_area(face_location: Tuple[int, int, int, int]) -> int:
    """
    Calculate the area of a face bounding box
    
    Args:
        face_location: Face location as (top, right, bottom, left)
        
    Returns:
        Face area in pixels
    """
    top, right, bottom, left = face_location
    width = right - left
    height = bottom - top
    return width * height

def filter_large_faces(face_locations: List[Tuple[int, int, int, int]], 
                      min_area: int = 2500) -> List[Tuple[int, int, int, int]]:
    """
    Filter out faces that are too small
    
    Args:
        face_locations: List of face locations
        min_area: Minimum face area in pixels
        
    Returns:
        Filtered list of face locations
    """
    return [
        face for face in face_locations 
        if calculate_face_area(face) >= min_area
    ]

def draw_rounded_rectangle(image: np.ndarray, 
                          pt1: Tuple[int, int], 
                          pt2: Tuple[int, int],
                          color: Tuple[int, int, int],
                          thickness: int = 2,
                          radius: int = 10):
    """
    Draw a rounded rectangle on an image
    
    Args:
        image: Input image
        pt1: Top-left corner
        pt2: Bottom-right corner  
        color: Rectangle color (B, G, R)
        thickness: Line thickness
        radius: Corner radius
    """
    x1, y1 = pt1
    x2, y2 = pt2
    
    # Draw the main rectangle
    cv2.rectangle(image, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
    cv2.rectangle(image, (x1, y1 + radius), (x2, y2 - radius), color, thickness)
    
    # Draw the corners
    cv2.ellipse(image, (x1 + radius, y1 + radius), (radius, radius), 180, 0, 90, color, thickness)
    cv2.ellipse(image, (x2 - radius, y1 + radius), (radius, radius), 270, 0, 90, color, thickness)
    cv2.ellipse(image, (x1 + radius, y2 - radius), (radius, radius), 90, 0, 90, color, thickness)
    cv2.ellipse(image, (x2 - radius, y2 - radius), (radius, radius), 0, 0, 90, color, thickness)

def display_success_message(message: str):
    """Display success message in Streamlit"""
    st.success(f"✅ {message}")

def display_error_message(message: str):
    """Display error message in Streamlit"""
    st.error(f"❌ {message}")

def display_warning_message(message: str):
    """Display warning message in Streamlit"""
    st.warning(f"⚠️ {message}")

def display_info_message(message: str):
    """Display info message in Streamlit"""
    st.info(f"ℹ️ {message}")

def create_progress_bar(text: str = "Processing..."):
    """Create a progress bar for Streamlit"""
    return st.progress(0, text=text)

def update_progress_bar(progress_bar, value: float, text: str = ""):
    """Update progress bar value"""
    progress_bar.progress(value, text=text)

def safe_division(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Perform safe division with default value for zero denominator"""
    if denominator == 0:
        return default
    return numerator / denominator

def get_system_info() -> Dict[str, str]:
    """Get basic system information"""
    import platform
    import psutil
    
    try:
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'cpu_count': str(psutil.cpu_count()),
            'memory_gb': f"{psutil.virtual_memory().total / (1024**3):.1f} GB"
        }
    except:
        return {'error': 'Unable to retrieve system information'}

def cleanup_old_files(directory: str, days_old: int = 30, file_pattern: str = "*"):
    """
    Clean up old files from a directory
    
    Args:
        directory: Directory to clean
        days_old: Files older than this many days will be deleted
        file_pattern: File pattern to match (e.g., "*.csv")
    """
    try:
        directory_path = Path(directory)
        if not directory_path.exists():
            return
        
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_old)
        
        for file_path in directory_path.glob(file_pattern):
            if file_path.is_file():
                file_modified_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_modified_time < cutoff_date:
                    file_path.unlink()
                    logging.info(f"Deleted old file: {file_path}")
                    
    except Exception as e:
        logging.error(f"Error cleaning up old files: {str(e)}")
