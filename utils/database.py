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
