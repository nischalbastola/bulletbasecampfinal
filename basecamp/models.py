from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
from sqlalchemy.ext.mutable import MutableDict

db = SQLAlchemy()

class Tour(db.Model):
    """Tour model for motorcycle tours"""
    __tablename__ = 'tours'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, unique=True)
    duration = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    price = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255), default='default-tour.jpg')
    highlights = db.Column(JSON, default=list)

    # New key info fields for the info bar
    keyinfo_duration = db.Column(db.String(100), nullable=True)
    keyinfo_per_day = db.Column(db.String(100), nullable=True)
    keyinfo_difficulty = db.Column(db.String(100), nullable=True)
    keyinfo_altitude = db.Column(db.String(100), nullable=True)
    keyinfo_group_size = db.Column(db.String(100), nullable=True)
    keyinfo_trip_cost = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Tour {self.title}>'
    
    def to_dict(self):
        """Convert tour to dictionary for JSON response"""
        return {
            'id': self.id,
            'title': self.title,
            'duration': self.duration,
            'difficulty': self.difficulty,
            'price': self.price,
            'description': self.description,
            'image': self.image,
            'highlights': self.highlights or [],

            'keyinfo_duration': self.keyinfo_duration,
            'keyinfo_per_day': self.keyinfo_per_day,
            'keyinfo_difficulty': self.keyinfo_difficulty,
            'keyinfo_altitude': self.keyinfo_altitude,
            'keyinfo_group_size': self.keyinfo_group_size,
            'keyinfo_trip_cost': self.keyinfo_trip_cost,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }

class Rental(db.Model):
    """Rental model for motorcycle rentals"""
    __tablename__ = 'rentals'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    category = db.Column(db.String(100), nullable=False)
    price_per_day = db.Column(db.String(50), nullable=False)
    price_per_week = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255), default='default-bike.jpg')
    specs = db.Column(JSON, default=dict)
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Rental {self.name}>'
    
    def to_dict(self):
        """Convert rental to dictionary for JSON response"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'price_per_day': self.price_per_day,
            'price_per_week': self.price_per_week,
            'description': self.description,
            'image': self.image,
            'specs': self.specs or {},
            'available': self.available,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Inquiry(db.Model):
    """Inquiry model for customer inquiries and messages"""
    __tablename__ = 'inquiries'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    service = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Inquiry {self.name} - {self.service}>'
    
    def to_dict(self):
        """Convert inquiry to dictionary for JSON response"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'service': self.service,
            'message': self.message,
            'ip_address': self.ip_address,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Staff(db.Model):
    """Staff model for admin users"""
    __tablename__ = 'staff'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='staff')  # admin, staff
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Staff {self.username}>'
    
    def to_dict(self):
        """Convert staff to dictionary for JSON response"""
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'role': self.role,
            'email': self.email,
            'phone': self.phone,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SecurityLog(db.Model):
    """Security log model for tracking security events"""
    __tablename__ = 'security_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    severity = db.Column(db.String(20), default='info')  # info, warning, error, critical
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SecurityLog {self.event_type} - {self.created_at}>'
    
    def to_dict(self):
        """Convert security log to dictionary for JSON response"""
        return {
            'id': self.id,
            'event_type': self.event_type,
            'description': self.description,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'severity': self.severity,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Booking(db.Model):
    """Booking model for tour and rental bookings"""
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    booking_type = db.Column(db.String(50), nullable=False)  # tour, rental
    item_id = db.Column(db.Integer, nullable=False)  # tour_id or rental_id
    item_name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, cancelled, completed
    special_requests = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Booking {self.customer_name} - {self.booking_type}>'
    
    def to_dict(self):
        """Convert booking to dictionary for JSON response"""
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'booking_type': self.booking_type,
            'item_id': self.item_id,
            'item_name': self.item_name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'total_price': float(self.total_price) if self.total_price else 0,
            'status': self.status,
            'special_requests': self.special_requests,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 