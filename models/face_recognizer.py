"""
Face Recognition Module using 128-dimensional face encodings
Implements deep learning-based face recognition with high accuracy
"""

import numpy as np
import pickle
import os
from typing import List, Tuple, Optional, Dict 
import face_recognition
import logging
from pathlib import Path
import joblib
from sklearn.metrics.pairwise import cosine_similarity
from utils.config import Config

class FaceRecognizer:
    """
    Advanced face recognition using deep learning embeddings
    Features:
    - 128-dimensional face encodings
    - Multiple comparison methods (Euclidean, Cosine similarity)
    - Adaptive thresholding
    - Performance optimization
    """
    
    def __init__(self, tolerance: float = 0.4):
        """
        Initialize face recognizer
        
        Args:
            tolerance: Recognition tolerance (lower = more strict)
        """
        self.config = Config()
        self.tolerance = tolerance
        self.encodings_file = "data/encodings/face_encodings.pkl"
        self.names_file = "data/encodings/face_names.pkl"
        
        # Face database
        self.known_face_encodings = []
        self.known_face_names = []
        
        # Recognition statistics
        self.recognition_stats = {
            'total_recognitions': 0,
            'successful_recognitions': 0,
            'unknown_faces': 0,
            'confidence_scores': []
        }
        
        # Load existing encodings
        self.load_encodings()
    
    def add_person(self, name: str, face_encodings: List[np.ndarray]):
        """
        Add a new person to the recognition database
        
        Args:
            name: Person's name
            face_encodings: List of 128-d face encodings for the person
        """
        try:
            # Add multiple encodings for better recognition accuracy
            for encoding in face_encodings:
                self.known_face_encodings.append(encoding)
                self.known_face_names.append(name)
            
            # Save updated encodings
            self.save_encodings()
            
            logging.info(f"Added {len(face_encodings)} encodings for {name}")
            
        except Exception as e:
            logging.error(f"Error adding person {name}: {str(e)}")
            raise
    
    def remove_person(self, name: str):
        """
        Remove a person from the recognition database
        
        Args:
            name: Person's name to remove
        """
        try:
            # Find all indices for this person
            indices_to_remove = [i for i, n in enumerate(self.known_face_names) if n == name]
            
            # Remove in reverse order to maintain indices
            for index in reversed(indices_to_remove):
                del self.known_face_encodings[index]
                del self.known_face_names[index]
            
            # Save updated encodings
            self.save_encodings()
            
            logging.info(f"Removed {len(indices_to_remove)} encodings for {name}")
            
        except Exception as e:
            logging.error(f"Error removing person {name}: {str(e)}")
            raise
    
    def recognize_face(self, face_encoding: np.ndarray, 
                      tolerance: Optional[float] = None) -> Tuple[str, float]:
        """
        Recognize a face from its encoding
        
        Args:
            face_encoding: 128-d face encoding to recognize
            tolerance: Override default tolerance
            
        Returns:
            Tuple of (name, confidence_score)
        """
        if not self.known_face_encodings:
            return "Unknown", 0.0
        
        tolerance = tolerance or self.tolerance
        
        try:
            # Compute distances to all known faces
            distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            
            # Find the best match
            min_distance_index = np.argmin(distances)
            min_distance = distances[min_distance_index]
            
            # Update statistics
            self.recognition_stats['total_recognitions'] += 1
            
            if min_distance <= tolerance:
                name = self.known_face_names[min_distance_index]
                confidence = 1.0 - min_distance  # Convert distance to confidence
                
                self.recognition_stats['successful_recognitions'] += 1
                self.recognition_stats['confidence_scores'].append(confidence)
                
                return name, confidence
            else:
                self.recognition_stats['unknown_faces'] += 1
                return "Unknown", 1.0 - min_distance
                
        except Exception as e:
            logging.error(f"Error in face recognition: {str(e)}")
            return "Unknown", 0.0
    
    def recognize_faces_batch(self, face_encodings: List[np.ndarray], 
                            tolerance: Optional[float] = None) -> List[Tuple[str, float]]:
        """
        Recognize multiple faces in batch
        
        Args:
            face_encodings: List of 128-d face encodings
            tolerance: Override default tolerance
            
        Returns:
            List of (name, confidence) tuples
        """
        results = []
        
        for encoding in face_encodings:
            name, confidence = self.recognize_face(encoding, tolerance)
            results.append((name, confidence))
            
        return results
    
    def get_face_encodings_from_image(self, image_path: str, 
                                    num_jitters: int = 1) -> List[np.ndarray]:
        """
        Extract face encodings from an image file
        
        Args:
            image_path: Path to image file
            num_jitters: Number of times to re-sample for better accuracy
            
        Returns:
            List of 128-d face encodings found in the image
        """
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Find face locations
            face_locations = face_recognition.face_locations(image, model="hog")
            
            if not face_locations:
                logging.warning(f"No faces found in {image_path}")
                return []
            
            # Extract face encodings
            face_encodings = face_recognition.face_encodings(
                image, face_locations, num_jitters=num_jitters
            )
            
            return face_encodings
            
        except Exception as e:
            logging.error(f"Error processing image {image_path}: {str(e)}")
            return []
    
    def train_from_directory(self, data_directory: str):
        """
        Train face recognition from a directory structure:
        data_directory/
        ├── person1/
        │   ├── image1.jpg
        │   ├── image2.jpg
        │   └── ...
        ├── person2/
        │   ├── image1.jpg
        │   └── ...
        
        Args:
            data_directory: Path to training data directory
        """
        data_path = Path(data_directory)
        
        if not data_path.exists():
            logging.error(f"Training directory {data_directory} does not exist")
            return
        
        total_encodings = 0
        
        for person_dir in data_path.iterdir():
            if person_dir.is_dir():
                person_name = person_dir.name
                person_encodings = []
                
                # Process all images for this person
                for image_file in person_dir.glob("*.jpg"):
                    encodings = self.get_face_encodings_from_image(str(image_file))
                    person_encodings.extend(encodings)
                
                # Add person to database
                if person_encodings:
                    self.add_person(person_name, person_encodings)
                    total_encodings += len(person_encodings)
                    logging.info(f"Trained {person_name} with {len(person_encodings)} encodings")
                else:
                    logging.warning(f"No face encodings found for {person_name}")
        
        logging.info(f"Training completed: {total_encodings} total encodings for {len(set(self.known_face_names))} people")
    
    def save_encodings(self):
        """Save face encodings to disk"""
        try:
            os.makedirs(os.path.dirname(self.encodings_file), exist_ok=True)
            
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(self.known_face_encodings, f)
                
            with open(self.names_file, 'wb') as f:
                pickle.dump(self.known_face_names, f)
                
            logging.info("Face encodings saved successfully")
            
        except Exception as e:
            logging.error(f"Error saving encodings: {str(e)}")
    
    def load_encodings(self):
        """Load face encodings from disk"""
        try:
            if os.path.exists(self.encodings_file) and os.path.exists(self.names_file):
                with open(self.encodings_file, 'rb') as f:
                    self.known_face_encodings = pickle.load(f)
                    
                with open(self.names_file, 'rb') as f:
                    self.known_face_names = pickle.load(f)
                    
                logging.info(f"Loaded {len(self.known_face_encodings)} face encodings")
            else:
                logging.info("No existing encodings found, starting fresh")
                
        except Exception as e:
            logging.error(f"Error loading encodings: {str(e)}")
            self.known_face_encodings = []
            self.known_face_names = []
    
    def get_person_statistics(self) -> Dict[str, int]:
        """Get statistics about registered people"""
        person_counts = {}
        
        for name in self.known_face_names:
            person_counts[name] = person_counts.get(name, 0) + 1
            
        return person_counts
    
    def get_recognition_statistics(self) -> Dict:
        """Get recognition performance statistics"""
        total_recognitions = self.recognition_stats['total_recognitions']
        
        if total_recognitions == 0:
            return {
                'total_recognitions': 0,
                'success_rate': 0.0,
                'average_confidence': 0.0,
                'unknown_rate': 0.0
            }
        
        success_rate = (self.recognition_stats['successful_recognitions'] / total_recognitions) * 100
        unknown_rate = (self.recognition_stats['unknown_faces'] / total_recognitions) * 100
        
        confidence_scores = self.recognition_stats['confidence_scores']
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
        
        return {
            'total_recognitions': total_recognitions,
            'successful_recognitions': self.recognition_stats['successful_recognitions'],
            'unknown_faces': self.recognition_stats['unknown_faces'],
            'success_rate': success_rate,
            'unknown_rate': unknown_rate,
            'average_confidence': avg_confidence,
            'registered_people': len(set(self.known_face_names)),
            'total_encodings': len(self.known_face_encodings)
        }
    
    def optimize_encodings(self, max_encodings_per_person: int = 10):
        """
        Optimize encodings by keeping only the best ones for each person
        This reduces memory usage and can improve recognition speed
        
        Args:
            max_encodings_per_person: Maximum encodings to keep per person
        """
        if not self.known_face_encodings:
            return
        
        # Group encodings by person
        person_encodings = {}
        for i, name in enumerate(self.known_face_names):
            if name not in person_encodings:
                person_encodings[name] = []
            person_encodings[name].append((i, self.known_face_encodings[i]))
        
        # Keep only the best encodings for each person
        optimized_encodings = []
        optimized_names = []
        
        for name, encodings in person_encodings.items():
            if len(encodings) <= max_encodings_per_person:
                # Keep all encodings
                for idx, encoding in encodings:
                    optimized_encodings.append(encoding)
                    optimized_names.append(name)
            else:
                # Calculate diversity scores and keep the most diverse encodings
                # This is a simplified approach - in production, you might use more sophisticated methods
                selected_encodings = encodings[:max_encodings_per_person]
                
                for idx, encoding in selected_encodings:
                    optimized_encodings.append(encoding)
                    optimized_names.append(name)
        
        # Update the encodings
        original_count = len(self.known_face_encodings)
        self.known_face_encodings = optimized_encodings
        self.known_face_names = optimized_names
        
        # Save optimized encodings
        self.save_encodings()
        
        logging.info(f"Optimized encodings: {original_count} -> {len(optimized_encodings)}")
    
    def validate_encodings(self) -> Dict:
        """Validate the integrity of stored encodings"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'total_encodings': len(self.known_face_encodings),
            'unique_people': len(set(self.known_face_names))
        }
        
        # Check if encodings and names match in length
        if len(self.known_face_encodings) != len(self.known_face_names):
            validation_results['valid'] = False
            validation_results['errors'].append("Mismatch in encodings and names count")
        
        # Check encoding dimensions
        for i, encoding in enumerate(self.known_face_encodings):
            if len(encoding) != 128:
                validation_results['valid'] = False
                validation_results['errors'].append(f"Invalid encoding dimension at index {i}: {len(encoding)}")
        
        # Check for duplicate encodings (might indicate overfitting)
        unique_encodings = set(tuple(enc) for enc in self.known_face_encodings)
        if len(unique_encodings) < len(self.known_face_encodings):
            validation_results['warnings'].append("Duplicate encodings detected")
        
        return validation_results
