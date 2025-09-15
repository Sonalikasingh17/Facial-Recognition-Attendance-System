"""
Attendance Management Module
Handles attendance tracking, CSV generation, and reporting
"""

import csv
import os
import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd
import logging
from pathlib import Path
import json

class AttendanceManager:
    """
    Comprehensive attendance management system
    Features:
    - Daily attendance tracking
    - CSV report generation
    - Attendance analytics
    - Multi-format export
    - Duplicate prevention
    """
    
    def __init__(self, attendance_dir: str = "data/attendance"):
        """
        Initialize attendance manager
        
        Args:
            attendance_dir: Directory to store attendance files
        """
        self.attendance_dir = Path(attendance_dir)
        self.attendance_dir.mkdir(parents=True, exist_ok=True)
        
        # Current session tracking
        self.today_attendees = set()
        self.session_stats = {
            'session_start': datetime.datetime.now(),
            'total_check_ins': 0,
            'unique_attendees': 0,
            'duplicate_attempts': 0
        }
        
        # Load today's existing attendees
        self._load_todays_attendees()
    
    def mark_attendance(self, person_name: str, 
                       timestamp: Optional[datetime.datetime] = None,
                       additional_info: Optional[Dict] = None) -> Dict:
        """
        Mark attendance for a person
        
        Args:
            person_name: Name of the person
            timestamp: Attendance timestamp (default: current time)
            additional_info: Additional information to store
            
        Returns:
            Dictionary with attendance status and details
        """
        if timestamp is None:
            timestamp = datetime.datetime.now()
        
        # Check if already marked today
        if person_name in self.today_attendees:
            self.session_stats['duplicate_attempts'] += 1
            return {
                'status': 'already_marked',
                'message': f'{person_name} already marked present today',
                'first_check_in': self._get_first_checkin_time(person_name),
                'current_time': timestamp
            }
        
        try:
            # Create attendance record
            attendance_record = {
                'name': person_name,
                'date': timestamp.strftime('%Y-%m-%d'),
                'time': timestamp.strftime('%H:%M:%S'),
                'timestamp': timestamp.isoformat(),
                'day_of_week': timestamp.strftime('%A'),
                'status': 'Present'
            }
            
            # Add additional information if provided
            if additional_info:
                attendance_record.update(additional_info)
            
            # Save to CSV
            self._save_to_csv(attendance_record, timestamp.date())
            
            # Update session tracking
            self.today_attendees.add(person_name)
            self.session_stats['total_check_ins'] += 1
            self.session_stats['unique_attendees'] = len(self.today_attendees)
            
            logging.info(f"Attendance marked for {person_name} at {timestamp}")
            
            return {
                'status': 'success',
                'message': f'Attendance marked for {person_name}',
                'timestamp': timestamp,
                'total_today': len(self.today_attendees)
            }
            
        except Exception as e:
            logging.error(f"Error marking attendance for {person_name}: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to mark attendance: {str(e)}'
            }
    
    def _save_to_csv(self, record: Dict, date: datetime.date):
        """Save attendance record to CSV file"""
        csv_file = self.attendance_dir / f"attendance_{date.strftime('%Y-%m-%d')}.csv"
        
        # Check if file exists to determine if we need headers
        file_exists = csv_file.exists()
        
        # Field names for CSV
        fieldnames = ['name', 'date', 'time', 'timestamp', 'day_of_week', 'status']
        
        # Add any additional fields from the record
        additional_fields = [key for key in record.keys() if key not in fieldnames]
        fieldnames.extend(additional_fields)
        
        # Write to CSV
        with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
            
            # Write the record
            writer.writerow(record)
    
    def get_today_attendance(self) -> List[Dict]:
        """Get today's attendance records"""
        today = datetime.date.today()
        csv_file = self.attendance_dir / f"attendance_{today.strftime('%Y-%m-%d')}.csv"
        
        attendance_records = []
        
        if csv_file.exists():
            try:
                with open(csv_file, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    attendance_records = list(reader)
            except Exception as e:
                logging.error(f"Error reading today's attendance: {str(e)}")
        
        return attendance_records
    
    def get_attendance_report(self, start_date: datetime.date, 
                            end_date: datetime.date) -> List[Dict]:
        """
        Get attendance report for a date range
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            
        Returns:
            List of attendance records
        """
        all_records = []
        
        current_date = start_date
        while current_date <= end_date:
            csv_file = self.attendance_dir / f"attendance_{current_date.strftime('%Y-%m-%d')}.csv"
            
            if csv_file.exists():
                try:
                    with open(csv_file, 'r', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        daily_records = list(reader)
                        all_records.extend(daily_records)
                except Exception as e:
                    logging.error(f"Error reading attendance for {current_date}: {str(e)}")
            
            current_date += datetime.timedelta(days=1)
        
        return all_records
    
    def get_person_attendance_history(self, person_name: str, 
                                    days_back: int = 30) -> List[Dict]:
        """
        Get attendance history for a specific person
        
        Args:
            person_name: Name of the person
            days_back: Number of days to look back
            
        Returns:
            List of attendance records for the person
        """
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days_back)
        
        all_records = self.get_attendance_report(start_date, end_date)
        
        # Filter records for the specific person
        person_records = [
            record for record in all_records 
            if record.get('name', '').lower() == person_name.lower()
        ]
        
        return person_records
    
    def generate_attendance_statistics(self, start_date: datetime.date, 
                                     end_date: datetime.date) -> Dict:
        """
        Generate comprehensive attendance statistics
        
        Args:
            start_date: Start date for statistics
            end_date: End date for statistics
            
        Returns:
            Dictionary containing various statistics
        """
        records = self.get_attendance_report(start_date, end_date)
        
        if not records:
            return {
                'total_records': 0,
                'unique_attendees': 0,
                'date_range': f"{start_date} to {end_date}",
                'daily_averages': {},
                'top_attendees': [],
                'attendance_trends': {}
            }
        
        # Basic statistics
        total_records = len(records)
        unique_attendees = len(set(record['name'] for record in records))
        
        # Daily statistics
        daily_counts = {}
        person_counts = {}
        
        for record in records:
            date = record['date']
            name = record['name']
            
            daily_counts[date] = daily_counts.get(date, 0) + 1
            person_counts[name] = person_counts.get(name, 0) + 1
        
        # Calculate averages
        num_days = len(daily_counts)
        avg_daily_attendance = total_records / num_days if num_days > 0 else 0
        
        # Top attendees
        top_attendees = sorted(person_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Day of week analysis
        dow_counts = {}
        for record in records:
            dow = record.get('day_of_week', 'Unknown')
            dow_counts[dow] = dow_counts.get(dow, 0) + 1
        
        return {
            'total_records': total_records,
            'unique_attendees': unique_attendees,
            'date_range': f"{start_date} to {end_date}",
            'number_of_days': num_days,
            'average_daily_attendance': round(avg_daily_attendance, 2),
            'daily_counts': daily_counts,
            'person_attendance_counts': person_counts,
            'top_attendees': top_attendees,
            'day_of_week_analysis': dow_counts
        }
    
    def export_to_excel(self, start_date: datetime.date, 
                       end_date: datetime.date, 
                       output_file: Optional[str] = None) -> str:
        """
        Export attendance data to Excel format
        
        Args:
            start_date: Start date for export
            end_date: End date for export
            output_file: Output file path (optional)
            
        Returns:
            Path to the created Excel file
        """
        records = self.get_attendance_report(start_date, end_date)
        
        if not records:
            raise ValueError("No attendance records found for the specified date range")
        
        # Create DataFrame
        df = pd.DataFrame(records)
        
        # Generate output filename if not provided
        if output_file is None:
            output_file = self.attendance_dir / f"attendance_report_{start_date}_to_{end_date}.xlsx"
        
        try:
            # Create Excel writer with multiple sheets
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Raw data sheet
                df.to_excel(writer, sheet_name='Raw Data', index=False)
                
                # Summary statistics
                stats = self.generate_attendance_statistics(start_date, end_date)
                
                # Daily summary
                daily_summary = df.groupby('date').agg({
                    'name': 'count',
                    'name': 'nunique'
                }).rename(columns={'name': 'Total_Attendance', 'name': 'Unique_People'})
                
                daily_summary.to_excel(writer, sheet_name='Daily Summary')
                
                # Person summary
                person_summary = df.groupby('name').agg({
                    'date': 'count',
                    'date': 'nunique'
                }).rename(columns={'date': 'Total_Days', 'date': 'Unique_Dates'})
                
                person_summary.to_excel(writer, sheet_name='Person Summary')
            
            logging.info(f"Attendance data exported to {output_file}")
            return str(output_file)
            
        except Exception as e:
            logging.error(f"Error exporting to Excel: {str(e)}")
            raise
    
    def backup_attendance_data(self, backup_dir: Optional[str] = None) -> str:
        """
        Create a backup of all attendance data
        
        Args:
            backup_dir: Backup directory (optional)
            
        Returns:
            Path to the backup directory
        """
        if backup_dir is None:
            backup_dir = self.attendance_dir.parent / f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        try:
            import shutil
            
            # Copy all CSV files
            for csv_file in self.attendance_dir.glob("*.csv"):
                shutil.copy2(csv_file, backup_path)
            
            # Create backup metadata
            metadata = {
                'backup_date': datetime.datetime.now().isoformat(),
                'source_directory': str(self.attendance_dir),
                'files_backed_up': len(list(self.attendance_dir.glob("*.csv"))),
                'session_stats': self.session_stats
            }
            
            with open(backup_path / "backup_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logging.info(f"Attendance data backed up to {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logging.error(f"Error creating backup: {str(e)}")
            raise
    
    def _load_todays_attendees(self):
        """Load today's attendees to prevent duplicates"""
        today_records = self.get_today_attendance()
        self.today_attendees = set(record['name'] for record in today_records)
    
    def _get_first_checkin_time(self, person_name: str) -> Optional[str]:
        """Get the first check-in time for a person today"""
        today_records = self.get_today_attendance()
        
        person_records = [
            record for record in today_records 
            if record['name'] == person_name
        ]
        
        if person_records:
            # Records should be in chronological order
            return person_records[0].get('time')
        
        return None
    
    def get_session_statistics(self) -> Dict:
        """Get current session statistics"""
        session_duration = datetime.datetime.now() - self.session_stats['session_start']
        
        return {
            'session_start': self.session_stats['session_start'].isoformat(),
            'session_duration_minutes': round(session_duration.total_seconds() / 60, 2),
            'total_check_ins': self.session_stats['total_check_ins'],
            'unique_attendees': self.session_stats['unique_attendees'],
            'duplicate_attempts': self.session_stats['duplicate_attempts'],
            'today_total_attendees': len(self.today_attendees)
        }
    
    def manual_attendance_entry(self, person_name: str, 
                              date: datetime.date, 
                              time: datetime.time,
                              status: str = "Present") -> Dict:
        """
        Manually enter attendance (for corrections or missed entries)
        
        Args:
            person_name: Name of the person
            date: Date of attendance
            time: Time of attendance
            status: Attendance status
            
        Returns:
            Dictionary with operation status
        """
        try:
            # Create timestamp
            timestamp = datetime.datetime.combine(date, time)
            
            # Create attendance record
            attendance_record = {
                'name': person_name,
                'date': date.strftime('%Y-%m-%d'),
                'time': time.strftime('%H:%M:%S'),
                'timestamp': timestamp.isoformat(),
                'day_of_week': date.strftime('%A'),
                'status': status,
                'entry_type': 'manual'
            }
            
            # Save to CSV
            self._save_to_csv(attendance_record, date)
            
            logging.info(f"Manual attendance entry for {person_name} on {date}")
            
            return {
                'status': 'success',
                'message': f'Manual attendance recorded for {person_name}'
            }
            
        except Exception as e:
            logging.error(f"Error in manual attendance entry: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to record manual attendance: {str(e)}'
            }
