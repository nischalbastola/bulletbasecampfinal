#!/usr/bin/env python3
"""
Database initialization script
Run this to set up the database and migrate existing JSON data
"""

import os
from app import app, db
from models import Tour, Rental, Inquiry, Staff, SecurityLog
from security import PasswordManager

def init_database():
    """Initialize the database and create tables"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Check if we have any data
        tour_count = Tour.query.count()
        rental_count = Rental.query.count()
        inquiry_count = Inquiry.query.count()
        staff_count = Staff.query.count()
        
        print(f"\n📊 Current database status:")
        print(f"   Tours: {tour_count}")
        print(f"   Rentals: {rental_count}")
        print(f"   Inquiries: {inquiry_count}")
        print(f"   Staff: {staff_count}")
        
        # Create default admin if no staff exists
        if staff_count == 0:
            print("\n👤 Creating default admin user...")
            admin = Staff()
            admin.username = 'admin'
            admin.name = 'Administrator'
            admin.password_hash = PasswordManager.hash_password('BulletBasecamp2024!@#')
            admin.role = 'admin'
            admin.email = 'admin@bulletbasecamp.com'
            admin.is_active = True
            
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin created: admin / BulletBasecamp2024!@#")
        
        print("\n🎉 Database initialization complete!")
        print("\nNext steps:")
        print("1. Run 'python migrate_to_db.py' to migrate existing JSON data")
        print("2. Start your application with 'python app.py'")

if __name__ == '__main__':
    init_database() 