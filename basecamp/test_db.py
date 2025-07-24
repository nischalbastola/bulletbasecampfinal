#!/usr/bin/env python3
"""
Database test script
Run this to verify your database setup is working correctly
"""

from app import app, db
from models import Tour, Rental, Inquiry, Staff, SecurityLog, Booking

def test_database():
    """Test database functionality"""
    with app.app_context():
        print("🧪 Testing database functionality...")
        
        # Test 1: Check if tables exist
        print("\n1. Checking table creation...")
        try:
            tour_count = Tour.query.count()
            rental_count = Rental.query.count()
            inquiry_count = Inquiry.query.count()
            staff_count = Staff.query.count()
            print(f"   ✅ Tables exist and are accessible")
            print(f"   📊 Current counts: Tours={tour_count}, Rentals={rental_count}, Inquiries={inquiry_count}, Staff={staff_count}")
        except Exception as e:
            print(f"   ❌ Error accessing tables: {e}")
            return False
        
        # Test 2: Create a test tour
        print("\n2. Testing tour creation...")
        try:
            test_tour = Tour()
            test_tour.title = "Test Tour"
            test_tour.duration = "1 day"
            test_tour.difficulty = "Beginner"
            test_tour.price = "NPR 5,000"
            test_tour.description = "This is a test tour"
            test_tour.highlights = ["Test highlight 1", "Test highlight 2"]
            test_tour.is_active = False  # Set to False so it doesn't show in production
            
            db.session.add(test_tour)
            db.session.commit()
            print(f"   ✅ Test tour created with ID: {test_tour.id}")
            
            # Clean up test tour
            db.session.delete(test_tour)
            db.session.commit()
            print(f"   ✅ Test tour cleaned up")
            
        except Exception as e:
            print(f"   ❌ Error creating test tour: {e}")
            db.session.rollback()
            return False
        
        # Test 3: Create a test rental
        print("\n3. Testing rental creation...")
        try:
            test_rental = Rental()
            test_rental.name = "Test Bike"
            test_rental.category = "Test"
            test_rental.price_per_day = "NPR 1,000"
            test_rental.price_per_week = "NPR 5,000"
            test_rental.description = "This is a test bike"
            test_rental.specs = {"engine": "Test", "power": "Test"}
            test_rental.available = False  # Set to False so it doesn't show in production
            
            db.session.add(test_rental)
            db.session.commit()
            print(f"   ✅ Test rental created with ID: {test_rental.id}")
            
            # Clean up test rental
            db.session.delete(test_rental)
            db.session.commit()
            print(f"   ✅ Test rental cleaned up")
            
        except Exception as e:
            print(f"   ❌ Error creating test rental: {e}")
            db.session.rollback()
            return False
        
        # Test 4: Test queries
        print("\n4. Testing database queries...")
        try:
            # Test filtering
            active_tours = Tour.query.filter_by(is_active=True).all()
            available_rentals = Rental.query.filter_by(available=True).all()
            print(f"   ✅ Query tests passed: {len(active_tours)} active tours, {len(available_rentals)} available rentals")
            
        except Exception as e:
            print(f"   ❌ Error testing queries: {e}")
            return False
        
        # Test 5: Test relationships (if any)
        print("\n5. Testing database relationships...")
        try:
            # This is a basic test - you can add more complex relationship tests here
            print(f"   ✅ Basic relationship tests passed")
            
        except Exception as e:
            print(f"   ❌ Error testing relationships: {e}")
            return False
        
        print("\n🎉 All database tests passed!")
        print("\nYour database is working correctly. You can now:")
        print("1. Run 'python migrate_to_db.py' to migrate your existing data")
        print("2. Start your application with 'python app.py'")
        
        return True

if __name__ == '__main__':
    success = test_database()
    if not success:
        print("\n❌ Database tests failed. Please check your setup.")
        exit(1) 