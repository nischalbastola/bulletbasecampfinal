#!/usr/bin/env python3
"""
Migration script to add bikes field to tours table
Run this script to add the bikes column to existing tours
"""

from app import app, db
from models import Tour

def add_bikes_column():
    """Add bikes column to tours table"""
    print("Adding bikes column to tours table...")
    
    with app.app_context():
        # Add the bikes column using raw SQL
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE tours ADD COLUMN bikes JSON DEFAULT "[]"'))
                conn.commit()
            print("Successfully added bikes column to tours table")
        except Exception as e:
            print(f"Error adding bikes column: {str(e)}")
            print("Column might already exist, continuing...")

def update_existing_tours():
    """Update existing tours with empty bikes list"""
    print("Updating existing tours with empty bikes list...")
    
    with app.app_context():
        tours = Tour.query.all()
        for tour in tours:
            if tour.bikes is None:
                tour.bikes = []
                print(f"Updated tour: {tour.title}")
        db.session.commit()
        print(f"Updated {len(tours)} tours")

def main():
    """Main migration function"""
    print("Starting bikes field migration...")
    
    add_bikes_column()
    update_existing_tours()
    
    print("Migration completed successfully!")

if __name__ == '__main__':
    main() 