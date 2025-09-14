# Create the face detector model - models/face_detector.py

face_detector_code = '''
"""
Face Detection Module using OpenCV and dlib
Supports multiple detection methods with performance optimization
"""

import cv2
import dlib
import numpy as np
from typing import List, Tuple, Optional
import logging
from utils.config import Config

class FaceDetector:
    """
    Advanced face detection using multiple algorithms:
    - OpenCV Haar Cascade (fast, basic accuracy)
    - dlib HOG (balanced speed and accuracy)
    - dlib CNN (high accuracy, slower)
    - OpenCV DNN (deep learning based)
    """
    
    def __init__(self, method: str = "HOG"):
        """
        Initialize face detector with specified method
        
        Args:
            method: Detection method - "HAAR", "HOG", "CNN", or "DNN"
        """
        self.config = Config()
        self.method = method.upper()
        self.setup_detectors()
        
        # Performance tracking
        self.detection_stats = {
            'total_detections': 0,
            'successful_detections': 0,
            'average_confidence': 0.0
        }
    
    def setup_detectors(self):
        """Initialize detection models based on selected method"""
        try:
            if self.method == "HAAR":
                self.haar_detector = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
                
            elif self.method == "HOG":
                self.hog_detector = dlib.get_frontal_face_detector()
                
            elif self.method == "CNN":
                # Download model if not exists
                model_path = "models/mmod_human_face_detector.dat"
                if not os.path.exists(model_path):
                    self._download_dlib_model(model_path)
                self.cnn_detector = dlib.cnn_face_detection_model_v1(model_path)
                
            elif self.method == "DNN":
                # OpenCV DNN face detector
                net_path = "models/opencv_face_detector.pbtxt"
                weights_path = "models/opencv_face_detector_uint8.pb"
                
                if not os.path.exists(net_path) or not os.path.exists(weights_path):
                    self._download_opencv_models(net_path, weights_path)
                    
                self.dnn_net = cv2.dnn.readNetFromTensorflow(weights_path, net_path)
                
        except Exception as e:
            logging.error(f"Error initializing {self.method} detector: {str(e)}")
            # Fallback to HOG
            self.method = "HOG"
            self.hog_detector = dlib.get_frontal_face_detector()
    
    def detect_faces(self, image: np.ndarray, 
                    min_confidence: float = 0.5) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in image using selected method
        
        Args:
            image: Input image as numpy array
            min_confidence: Minimum confidence threshold (for CNN/DNN methods)
            
        Returns:
            List of face locations as (top, right, bottom, left) tuples
        """
        if image is None:
            return []
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        faces = []
        
        try:
            if self.method == "HAAR":
                faces = self._detect_haar(gray)
            elif self.method == "HOG":
                faces = self._detect_hog(gray)
            elif self.method == "CNN":
                faces = self._detect_cnn(gray, min_confidence)
            elif self.method == "DNN":
                faces = self._detect_dnn(image, min_confidence)
                
            # Update statistics
            self.detection_stats['total_detections'] += 1
            if faces:
                self.detection_stats['successful_detections'] += 1
                
        except Exception as e:
            logging.error(f"Error in face detection: {str(e)}")
            
        return faces
    
    def _detect_haar(self, gray: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Haar Cascade detection"""
        faces = self.haar_detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Convert to face_recognition format (top, right, bottom, left)
        face_locations = []
        for (x, y, w, h) in faces:
            face_locations.append((y, x + w, y + h, x))
            
        return face_locations
    
    def _detect_hog(self, gray: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """HOG detection using dlib"""
        faces = self.hog_detector(gray)
        
        face_locations = []
        for face in faces:
            # Convert dlib rectangle to face_recognition format
            left = face.left()
            top = face.top()
            right = face.right()
            bottom = face.bottom()
            face_locations.append((top, right, bottom, left))
            
        return face_locations
    
    def _detect_cnn(self, gray: np.ndarray, 
                   min_confidence: float) -> List[Tuple[int, int, int, int]]:
        """CNN detection using dlib"""
        faces = self.cnn_detector(gray, 1)  # 1 = upsample once
        
        face_locations = []
        for face in faces:
            if face.confidence > min_confidence:
                rect = face.rect
                left = rect.left()
                top = rect.top()
                right = rect.right()
                bottom = rect.bottom()
                face_locations.append((top, right, bottom, left))
                
        return face_locations
    
    def _detect_dnn(self, image: np.ndarray, 
                   min_confidence: float) -> List[Tuple[int, int, int, int]]:
        """DNN detection using OpenCV"""
        h, w = image.shape[:2]
        
        # Create blob from image
        blob = cv2.dnn.blobFromImage(
            image, 1.0, (300, 300), [104, 117, 123], False, False
        )
        
        # Set input to the network
        self.dnn_net.setInput(blob)
        
        # Run forward pass
        detections = self.dnn_net.forward()
        
        face_locations = []
        
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > min_confidence:
                # Get bounding box coordinates
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x1, y1, x2, y2) = box.astype("int")
                
                # Convert to face_recognition format
                face_locations.append((y1, x2, y2, x1))
                
        return face_locations
    
    def detect_faces_batch(self, images: List[np.ndarray], 
                          min_confidence: float = 0.5) -> List[List[Tuple[int, int, int, int]]]:
        """
        Detect faces in multiple images (batch processing)
        
        Args:
            images: List of input images
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of face location lists for each image
        """
        all_faces = []
        
        for image in images:
            faces = self.detect_faces(image, min_confidence)
            all_faces.append(faces)
            
        return all_faces
    
    def get_largest_face(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Get the largest face in the image (useful for single-person scenarios)
        
        Args:
            image: Input image
            
        Returns:
            Largest face location or None if no faces found
        """
        faces = self.detect_faces(image)
        
        if not faces:
            return None
        
        # Calculate face areas and return the largest
        largest_face = max(faces, key=lambda face: (face[2] - face[0]) * (face[1] - face[3]))
        
        return largest_face
    
    def draw_face_boxes(self, image: np.ndarray, 
                       faces: List[Tuple[int, int, int, int]],
                       color: Tuple[int, int, int] = (0, 255, 0),
                       thickness: int = 2) -> np.ndarray:
        """
        Draw bounding boxes around detected faces
        
        Args:
            image: Input image
            faces: List of face locations
            color: Box color (B, G, R)
            thickness: Box thickness
            
        Returns:
            Image with face boxes drawn
        """
        result_image = image.copy()
        
        for (top, right, bottom, left) in faces:
            cv2.rectangle(result_image, (left, top), (right, bottom), color, thickness)
            
            # Add confidence score if available
            cv2.putText(
                result_image, 
                f"Face", 
                (left, top - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.6, 
                color, 
                thickness
            )
            
        return result_image
    
    def get_face_chips(self, image: np.ndarray, 
                      faces: List[Tuple[int, int, int, int]],
                      size: int = 150) -> List[np.ndarray]:
        """
        Extract face chips (cropped faces) from image
        
        Args:
            image: Input image
            faces: List of face locations
            size: Output size for face chips
            
        Returns:
            List of cropped face images
        """
        face_chips = []
        
        for (top, right, bottom, left) in faces:
            # Extract face region
            face_image = image[top:bottom, left:right]
            
            # Resize to standard size
            if face_image.size > 0:
                face_chip = cv2.resize(face_image, (size, size))
                face_chips.append(face_chip)
                
        return face_chips
    
    def get_detection_stats(self) -> dict:
        """Get detection performance statistics"""
        success_rate = 0.0
        if self.detection_stats['total_detections'] > 0:
            success_rate = (self.detection_stats['successful_detections'] / 
                          self.detection_stats['total_detections']) * 100
                          
        return {
            'method': self.method,
            'total_detections': self.detection_stats['total_detections'],
            'successful_detections': self.detection_stats['successful_detections'],
            'success_rate': success_rate
        }
    
    def _download_dlib_model(self, model_path: str):
        """Download dlib CNN model if not present"""
        import urllib.request
        import os
        
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        url = "http://dlib.net/files/mmod_human_face_detector.dat.bz2"
        compressed_path = model_path + ".bz2"
        
        # Download compressed file
        urllib.request.urlretrieve(url, compressed_path)
        
        # Decompress
        import bz2
        with bz2.BZ2File(compressed_path, 'rb') as f_in:
            with open(model_path, 'wb') as f_out:
                f_out.write(f_in.read())
        
        # Remove compressed file
        os.remove(compressed_path)
    
    def _download_opencv_models(self, net_path: str, weights_path: str):
        """Download OpenCV DNN models if not present"""
        import urllib.request
        import os
        
        os.makedirs(os.path.dirname(net_path), exist_ok=True)
        
        # URLs for OpenCV face detection models
        net_url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/opencv_face_detector.pbtxt"
        weights_url = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/opencv_face_detector_uint8.pb"
        
        urllib.request.urlretrieve(net_url, net_path)
        urllib.request.urlretrieve(weights_url, weights_path)
'''

print("Face Detector Module (models/face_detector.py) created successfully!")
print("File size:", len(face_detector_code), "characters")