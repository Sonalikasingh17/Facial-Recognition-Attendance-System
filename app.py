"""
Facial Recognition Attendance System - Main Streamlit Application
Built with OpenCV, dlib, and CNN-based architecture for automated attendance tracking 
"""

import streamlit as st 
import cv2
import numpy as np
import pandas as pd
import pickle
import os
import datetime
from pathlib import Path
import face_recognition
import logging
from PIL import Image
import time

# Import custom modules
from models.face_detector import FaceDetector
from models.face_recognizer import FaceRecognizer
from models.attendance_manager import AttendanceManager
from utils.config import Config
from utils.database import Database
from utils.helpers import setup_directories, log_activity

# Page configuration
st.set_page_config(
    page_title="Facial Recognition Attendance System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1e3a8a;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f1f5f9;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
    }
    .success-message {
        color: #059669;
        font-weight: bold;
    }
    .error-message {
        color: #dc2626;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class AttendanceApp:
    def __init__(self):
        self.config = Config()
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer()
        self.attendance_manager = AttendanceManager()
        self.database = Database()
        
        # Setup directories
        setup_directories()
        
        # Initialize session state
        if 'attendance_marked' not in st.session_state:
            st.session_state.attendance_marked = []
    
    def run(self):
        """Main application runner"""
        st.markdown('<h1 class="main-header">🎯 Facial Recognition Attendance System</h1>', 
                   unsafe_allow_html=True)
        
        # Sidebar navigation
        page = st.sidebar.selectbox(
            "Select Mode",
            ["📸 Live Attendance", "👥 Person Management", "📊 Reports", "⚙️ Settings"]
        )
        
        if page == "📸 Live Attendance":
            self.live_attendance_page()
        elif page == "👥 Person Management":
            self.person_management_page()
        elif page == "📊 Reports":
            self.reports_page()
        elif page == "⚙️ Settings":
            self.settings_page()
    
    def live_attendance_page(self):
        """Live attendance tracking page"""
        st.subheader("📸 Live Attendance Tracking")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Camera Feed")
            
            # Camera options
            camera_source = st.selectbox("Select Camera Source", [0, 1, 2])
            confidence_threshold = st.slider("Recognition Confidence", 0.3, 0.7, 0.4)
            
            if st.button("Start Attendance Tracking", type="primary"):
                self.run_live_tracking(camera_source, confidence_threshold)
        
        with col2:
            self.display_today_stats()
    
    def run_live_tracking(self, camera_source, confidence_threshold):
        """Run live face detection and attendance tracking"""
        cap = cv2.VideoCapture(camera_source)
        
        # Create placeholders
        frame_placeholder = st.empty()
        status_placeholder = st.empty()
        
        stop_button = st.button("Stop Tracking")
        
        while cap.isOpened() and not stop_button:
            ret, frame = cap.read()
            if not ret:
                st.error("Failed to access camera")
                break
            
            # Detect and recognize faces
            faces = self.face_detector.detect_faces(frame)
            recognized_persons = []
            
            for face_location in faces:
                # Extract face encoding
                face_encoding = face_recognition.face_encodings(frame, [face_location])
                
                if face_encoding:
                    # Recognize person
                    person_name, confidence = self.face_recognizer.recognize_face(
                        face_encoding[0], confidence_threshold
                    )
                    
                    if person_name != "Unknown":
                        recognized_persons.append(person_name)
                        
                        # Mark attendance
                        attendance_status = self.attendance_manager.mark_attendance(person_name)
                        
                        # Draw bounding box and label
                        top, right, bottom, left = face_location
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        cv2.putText(frame, f"{person_name} ({confidence:.2f})", 
                                  (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    else:
                        # Unknown person - red box
                        top, right, bottom, left = face_location
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                        cv2.putText(frame, "Unknown", (left, top - 10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            
            # Display frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame_rgb, channels="RGB")
            
            # Display status
            if recognized_persons:
                status_placeholder.success(f"Recognized: {', '.join(recognized_persons)}")
            else:
                status_placeholder.info("Looking for faces...")
            
            time.sleep(0.1)
        
        cap.release()
    
    def person_management_page(self):
        """Person management page for adding/removing people"""
        st.subheader("👥 Person Management")
        
        tab1, tab2, tab3 = st.tabs(["Add Person", "View People", "Remove Person"])
        
        with tab1:
            self.add_person_form()
        
        with tab2:
            self.view_people()
        
        with tab3:
            self.remove_person_form()
    
    def add_person_form(self):
        """Form to add new person"""
        st.markdown("### Add New Person")
        
        person_name = st.text_input("Person Name")
        person_id = st.text_input("Person ID (Optional)")
        
        uploaded_images = st.file_uploader(
            "Upload Person Images",
            accept_multiple_files=True,
            type=['jpg', 'jpeg', 'png']
        )
        
        if st.button("Add Person") and person_name and uploaded_images:
            try:
                # Save images and create face encodings
                person_dir = Path(f"data/faces/{person_name}")
                person_dir.mkdir(parents=True, exist_ok=True)
                
                face_encodings = []
                for i, uploaded_file in enumerate(uploaded_images):
                    # Save image
                    image_path = person_dir / f"{person_name}_{i}.jpg"
                    with open(image_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Extract face encoding
                    image = face_recognition.load_image_file(image_path)
                    encodings = face_recognition.face_encodings(image)
                    
                    if encodings:
                        face_encodings.extend(encodings)
                
                if face_encodings:
                    # Save encodings
                    self.face_recognizer.add_person(person_name, face_encodings)
                    
                    # Add to database
                    self.database.add_person(person_name, person_id)
                    
                    st.success(f"Successfully added {person_name} with {len(face_encodings)} face encodings!")
                else:
                    st.error("No faces detected in uploaded images")
                    
            except Exception as e:
                st.error(f"Error adding person: {str(e)}")
    
    def view_people(self):
        """Display registered people"""
        st.markdown("### Registered People")
        
        people = self.database.get_all_people()
        if people:
            df = pd.DataFrame(people, columns=['Name', 'ID', 'Date Added'])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No people registered yet.")
    
    def remove_person_form(self):
        """Form to remove person"""
        st.markdown("### Remove Person")
        
        people = self.database.get_all_people()
        if people:
            person_names = [person[0] for person in people]
            selected_person = st.selectbox("Select Person to Remove", person_names)
            
            if st.button("Remove Person", type="secondary"):
                try:
                    # Remove from face recognizer
                    self.face_recognizer.remove_person(selected_person)
                    
                    # Remove from database
                    self.database.remove_person(selected_person)
                    
                    # Remove image directory
                    import shutil
                    person_dir = Path(f"data/faces/{selected_person}")
                    if person_dir.exists():
                        shutil.rmtree(person_dir)
                    
                    st.success(f"Successfully removed {selected_person}")
                    
                except Exception as e:
                    st.error(f"Error removing person: {str(e)}")
        else:
            st.info("No people registered to remove.")
    
    def reports_page(self):
        """Attendance reports page"""
        st.subheader("📊 Attendance Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=7))
            
        with col2:
            end_date = st.date_input("End Date", datetime.date.today())
        
        if st.button("Generate Report"):
            attendance_data = self.attendance_manager.get_attendance_report(start_date, end_date)
            
            if attendance_data:
                df = pd.DataFrame(attendance_data)
                st.dataframe(df, use_container_width=True)
                
                # Download CSV
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"attendance_report_{start_date}_to_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No attendance data found for the selected period.")
    
    def settings_page(self):
        """Settings configuration page"""
        st.subheader("⚙️ System Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Detection Settings")
            detection_method = st.selectbox(
                "Face Detection Method",
                ["HOG", "CNN"],
                help="HOG is faster, CNN is more accurate"
            )
            
            recognition_tolerance = st.slider(
                "Recognition Tolerance",
                0.3, 0.7, 0.4,
                help="Lower values are more strict"
            )
        
        with col2:
            st.markdown("### System Info")
            st.info(f"OpenCV Version: {cv2.__version__}")
            st.info(f"Face Recognition Library: Available")
            st.info(f"Total Registered People: {len(self.database.get_all_people())}")
    
    def display_today_stats(self):
        """Display today's attendance statistics"""
        st.markdown("### Today's Statistics")
        
        today_attendance = self.attendance_manager.get_today_attendance()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Present Today", len(today_attendance))
        with col2:
            total_people = len(self.database.get_all_people())
            st.metric("Total Registered", total_people)
        
        if today_attendance:
            st.markdown("### Recent Check-ins")
            for record in today_attendance[-5:]:  # Last 5 records
                st.text(f"{record['name']} - {record['time']}")

# Run the application
if __name__ == "__main__":
    app = AttendanceApp()
    app.run()
