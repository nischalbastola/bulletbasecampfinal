#!/usr/bin/env python3
"""
Migration script to add keyinfo fields to existing tours
Run this script to add the new keyinfo fields to the database
"""

from app import app, db
from models import Tour
from sqlalchemy import text

def add_keyinfo_fields():
    """Add keyinfo fields to existing tours table"""
    print("Adding keyinfo fields to tours table...")
    
    with app.app_context():
        try:
            # Check if columns already exist
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(tours)"))
                existing_columns = [row[1] for row in result.fetchall()]
                print(f"Existing columns: {existing_columns}")
                
                # Add columns only if they don't exist
                columns_to_add = [
                    'keyinfo_duration',
                    'keyinfo_per_day', 
                    'keyinfo_difficulty',
                    'keyinfo_altitude',
                    'keyinfo_group_size',
                    'keyinfo_trip_cost'
                ]
                
                for column in columns_to_add:
                    if column not in existing_columns:
                        try:
                            conn.execute(text(f"ALTER TABLE tours ADD COLUMN {column} VARCHAR(100)"))
                            print(f"Added {column} column")
                        except Exception as e:
                            print(f"Error adding {column}: {str(e)}")
                    else:
                        print(f"Column {column} already exists")
                
                conn.commit()
            
            print("Successfully processed all keyinfo fields!")
            
        except Exception as e:
            print(f"Error in add_keyinfo_fields: {str(e)}")

def update_existing_tours():
    """Update existing tours with default keyinfo values"""
    print("Updating existing tours with default keyinfo values...")
    
    with app.app_context():
        try:
            tours = Tour.query.all()
            print(f"Found {len(tours)} tours to update")
            
            for tour in tours:
                # Set default values based on existing tour data
                if not tour.keyinfo_duration:
                    tour.keyinfo_duration = tour.duration
                if not tour.keyinfo_difficulty:
                    tour.keyinfo_difficulty = tour.difficulty
                if not tour.keyinfo_trip_cost:
                    tour.keyinfo_trip_cost = tour.price
                if not tour.keyinfo_per_day:
                    tour.keyinfo_per_day = "150-200 km"
                if not tour.keyinfo_altitude:
                    tour.keyinfo_altitude = "3,200m"
                if not tour.keyinfo_group_size:
                    tour.keyinfo_group_size = "2-12 riders"
            
            db.session.commit()
            print(f"Updated {len(tours)} tours with default keyinfo values")
            
        except Exception as e:
            print(f"Error updating tours: {str(e)}")
            db.session.rollback()

def main():
    """Main migration function"""
    print("Starting keyinfo fields migration...")
    
    add_keyinfo_fields()
    update_existing_tours()
    
    print("Migration completed!")

if __name__ == "__main__":
    main() 