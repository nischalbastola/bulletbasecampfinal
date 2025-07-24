#!/usr/bin/env python3
"""
Migration script to transfer data from JSON files to SQL database
Run this script after setting up the database to migrate existing data
"""

import json
import os
from datetime import datetime
from app import app, db
from models import Tour, Rental, Inquiry, Staff, SecurityLog
from security import PasswordManager

def load_json_data(filename):
    """Load JSON data from file"""
    try:
        file_path = os.path.join('data', filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading {filename}: {str(e)}")
        return []

def migrate_tours():
    """Migrate tours from JSON to database"""
    print("Migrating tours...")
    tours_data = load_json_data('tours.json')
    
    for tour_data in tours_data:
        # Check if tour already exists
        existing_tour = Tour.query.filter_by(title=tour_data.get('title')).first()
        if existing_tour:
            print(f"Tour '{tour_data.get('title')}' already exists, skipping...")
            continue
        # Create new tour
        tour = Tour()
        tour.title = tour_data.get('title', '')
        tour.duration = tour_data.get('duration', '')
        tour.difficulty = tour_data.get('difficulty', '')
        tour.price = tour_data.get('price', '')
        tour.description = tour_data.get('description', '')
        tour.image = tour_data.get('image', 'default-tour.jpg')
        tour.highlights = tour_data.get('highlights', [])
        tour.is_active = True
        db.session.add(tour)
        print(f"Added tour: {tour.title}")
    db.session.commit()
    print(f"Migrated {len(tours_data)} tours")

def migrate_rentals():
    """Migrate rentals from JSON to database"""
    print("Migrating rentals...")
    rentals_data = load_json_data('rentals.json')
    
    for rental_data in rentals_data:
        # Check if rental already exists
        existing_rental = Rental.query.filter_by(name=rental_data.get('name')).first()
        if existing_rental:
            print(f"Rental '{rental_data.get('name')}' already exists, skipping...")
            continue
        # Create new rental
        rental = Rental()
        rental.name = rental_data.get('name', '')
        rental.category = rental_data.get('category', '')
        rental.price_per_day = rental_data.get('price_per_day', '')
        rental.price_per_week = rental_data.get('price_per_week', '')
        rental.description = rental_data.get('description', '')
        rental.image = rental_data.get('image', 'default-bike.jpg')
        rental.specs = rental_data.get('specs', {})
        rental.available = rental_data.get('available', True)
        db.session.add(rental)
        print(f"Added rental: {rental.name}")
    db.session.commit()
    print(f"Migrated {len(rentals_data)} rentals")

def migrate_inquiries():
    """Migrate inquiries from JSON to database"""
    print("Migrating inquiries...")
    inquiries_data = load_json_data('inquiries.json')
    
    for inquiry_data in inquiries_data:
        # Check if inquiry already exists (by email and timestamp)
        existing_inquiry = Inquiry.query.filter_by(
            email=inquiry_data.get('email'),
            created_at=datetime.fromisoformat(inquiry_data.get('timestamp', datetime.now().isoformat()))
        ).first()
        if existing_inquiry:
            print(f"Inquiry from {inquiry_data.get('email')} already exists, skipping...")
            continue
        # Create new inquiry
        inquiry = Inquiry()
        inquiry.name = inquiry_data.get('name', '')
        inquiry.email = inquiry_data.get('email', '')
        inquiry.phone = inquiry_data.get('phone', '')
        inquiry.service = inquiry_data.get('service', '')
        inquiry.message = inquiry_data.get('message', '')
        inquiry.ip_address = inquiry_data.get('ip_address', '')
        inquiry.is_read = False
        inquiry.created_at = datetime.fromisoformat(inquiry_data.get('timestamp', datetime.now().isoformat()))
        db.session.add(inquiry)
        print(f"Added inquiry from: {inquiry.name}")
    db.session.commit()
    print(f"Migrated {len(inquiries_data)} inquiries")

def migrate_staff():
    """Migrate staff from JSON to database"""
    print("Migrating staff...")
    staff_data = load_json_data('staff.json')
    
    for staff_member_data in staff_data:
        # Check if staff already exists
        existing_staff = Staff.query.filter_by(username=staff_member_data.get('username')).first()
        if existing_staff:
            print(f"Staff '{staff_member_data.get('username')}' already exists, skipping...")
            continue
        # Create new staff member
        staff = Staff()
        staff.username = staff_member_data.get('username', '')
        staff.name = staff_member_data.get('name', '')
        staff.password_hash = staff_member_data.get('password_hash', '')
        staff.role = staff_member_data.get('role', 'staff')
        staff.email = staff_member_data.get('email', '')
        staff.phone = staff_member_data.get('phone', '')
        staff.is_active = staff_member_data.get('is_active', True)
        staff.last_login = datetime.fromisoformat(staff_member_data.get('last_login')) if staff_member_data.get('last_login') else None
        db.session.add(staff)
        print(f"Added staff: {staff.username}")
    db.session.commit()
    print(f"Migrated {len(staff_data)} staff members")

def create_default_admin():
    """Create default admin user if no admin exists"""
    admin = Staff.query.filter_by(role='admin').first()
    if not admin:
        print("Creating default admin user...")
        admin = Staff()
        admin.username = 'admin'
        admin.name = 'Administrator'
        admin.password_hash = PasswordManager.hash_password('BulletBasecamp2024!@#')
        admin.role = 'admin'
        admin.email = 'admin@bulletbasecamp.com'
        admin.is_active = True
        db.session.add(admin)
        db.session.commit()
        print("Default admin user created: admin / BulletBasecamp2024!@#")

def migrate_security_logs():
    """Migrate security logs from JSON to database"""
    print("Migrating security logs...")
    log_file = os.path.join('data', 'security.log')
    if not os.path.exists(log_file):
        print("No security.log file found, skipping...")
        return
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            if line.strip():
                parts = line.strip().split(' - ', 2)
                if len(parts) >= 3:
                    timestamp_str, event_type, description = parts
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                    except:
                        timestamp = datetime.now()
                    existing_log = SecurityLog.query.filter_by(
                        event_type=event_type,
                        description=description,
                        created_at=timestamp
                    ).first()
                    if not existing_log:
                        log = SecurityLog()
                        log.event_type = event_type
                        log.description = description
                        log.created_at = timestamp
                        log.severity = 'info'
                        db.session.add(log)
        db.session.commit()
        print(f"Migrated security logs")
    except Exception as e:
        print(f"Error migrating security logs: {str(e)}")

def main():
    """Main migration function"""
    print("Starting database migration...")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created")
        
        # Migrate data
        migrate_tours()
        migrate_rentals()
        migrate_inquiries()
        migrate_staff()
        migrate_security_logs()
        
        # Create default admin
        create_default_admin()
        
        print("Migration completed successfully!")
        print("\nSummary:")
        print(f"- Tours: {Tour.query.count()}")
        print(f"- Rentals: {Rental.query.count()}")
        print(f"- Inquiries: {Inquiry.query.count()}")
        print(f"- Staff: {Staff.query.count()}")
        print(f"- Security Logs: {SecurityLog.query.count()}")

if __name__ == '__main__':
    main() 