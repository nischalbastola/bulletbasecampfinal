import os
import json
import secrets
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, abort, send_from_directory
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import bleach

# Import our secure modules
from forms import LoginForm, ContactForm, TourForm, RentalForm, StaffForm
from security import (
    SecurityManager, PasswordManager, FileSecurityManager, 
    SessionManager, security_manager, log_security_event
)
from models import db, Tour, Rental, Inquiry, Staff, SecurityLog, Booking
from admin_functions import (
    admin_add_tour, admin_edit_tour, admin_delete_tour,
    admin_add_rental, admin_edit_rental, admin_delete_rental,
    admin_add_staff, admin_delete_staff, admin_delete_message
)

# Load environment variables
load_dotenv()

app = Flask(__name__)

print(f"DEBUG: FLASK TEMPLATE FOLDER: {app.template_folder}")

# DATABASE CONFIGURATION
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///basecamp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SECURITY CONFIGURATION - MAXIMUM HARDENING
app.config.update(
    SECRET_KEY=os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32)),
    SESSION_COOKIE_SECURE=False,         # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY=True,        # No JavaScript access
    SESSION_COOKIE_SAMESITE='Lax',       # CSRF protection
    WTF_CSRF_TIME_LIMIT=3600,           # 1 hour CSRF token validity
    MAX_CONTENT_LENGTH=int(os.getenv('MAX_FILE_SIZE_MB', 5)) * 1024 * 1024,
    UPLOAD_FOLDER='static/uploads',
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=int(os.getenv('SESSION_TIMEOUT', 30)))
)

# Initialize database
db.init_app(app)

# Initialize security extensions
csrf = CSRFProtect(app)

# Configure Flask-Limiter with memory storage to avoid warnings
# For development, using memory storage is fine. For production, set up Redis.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{os.getenv('RATE_LIMIT_PER_MINUTE', 60)} per minute"],
    app=app,
    storage_uri="memory://"
)
print("Using memory storage for rate limiting (development mode)")

# Security headers with Talisman
Talisman(app, 
    force_https=False,  # Set to True in production
    strict_transport_security=True,
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'",
        'img-src': "'self' data:",
        'font-src': "'self'"
    }
)

# Create required directories
for directory in ['data', 'logs', 'static/uploads']:
    if not os.path.exists(directory):
        os.makedirs(directory)

# ADMIN CREDENTIALS FROM ENVIRONMENT
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = PasswordManager.hash_password(os.getenv('ADMIN_PASSWORD', 'BulletBasecamp2024!@#'))
SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 1800))  # 30 minutes

# Security middleware
@app.before_request
def security_middleware():
    """Enhanced security checks on every request"""
    ip_address = request.remote_addr
    
    # Block malicious IPs
    if security_manager.is_ip_blocked(ip_address):
        log_security_event('blocked_ip_access', f'Blocked IP {ip_address} attempted access', ip_address)
        abort(429)  # Too Many Requests
    
    # Log admin area access attempts
    if request.endpoint and 'admin' in request.endpoint:
        log_security_event('admin_area_access', f'Access to {request.endpoint}', ip_address)
    
    # Validate session for admin routes
    if (request.endpoint and request.endpoint.startswith('admin') and 
        request.endpoint != 'admin_login' and not SessionManager.validate_session()):
        return redirect(url_for('admin_login'))

def require_admin(f):
    """Enhanced admin authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Debug: Print session info
        print(f"=== ADMIN CHECK for {request.endpoint} ===")
        print("Session data:", dict(session))
        print("User role:", session.get('user_role'))
        print("Username:", session.get('username'))
        print("Session valid:", SessionManager.validate_session())
        print("================================")
        
        if not SessionManager.validate_session():
            log_security_event('unauthorized_admin_access', f'Unauthorized access to {request.endpoint}')
            flash('Authentication required. Please log in.', 'error')
            return redirect(url_for('admin_login'))
        
        if session.get('user_role') != 'admin':
            log_security_event('insufficient_privileges', f'User {session.get("username")} tried to access admin function')
            flash('Insufficient privileges.', 'error')
            return redirect(url_for('admin_login'))  # Changed from admin_dashboard to admin_login
        
        return f(*args, **kwargs)
    return decorated_function

# DATABASE DATA MANAGEMENT
def get_all_tours():
    """Get all active tours from database"""
    try:
        return Tour.query.filter_by(is_active=True).order_by(Tour.created_at.desc()).all()
    except Exception as e:
        log_security_event('data_load_error', f'Error loading tours: {str(e)}')
        return []

def get_all_rentals():
    """Get all available rentals from database"""
    try:
        return Rental.query.filter_by(available=True).order_by(Rental.created_at.desc()).all()
    except Exception as e:
        log_security_event('data_load_error', f'Error loading rentals: {str(e)}')
        return []

def get_all_inquiries():
    """Get all inquiries from database"""
    try:
        return Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    except Exception as e:
        log_security_event('data_load_error', f'Error loading inquiries: {str(e)}')
        return []

def get_all_staff():
    """Get all active staff from database"""
    try:
        return Staff.query.filter_by(is_active=True).order_by(Staff.created_at.desc()).all()
    except Exception as e:
        log_security_event('data_load_error', f'Error loading staff: {str(e)}')
        return []

def sanitize_input_data(data):
    """Sanitize input data to prevent XSS and injection attacks"""
    if isinstance(data, dict):
        return {key: sanitize_input_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input_data(item) for item in data]
    elif isinstance(data, str):
        return bleach.clean(data.strip(), strip=True)
    return data

def save_inquiry(inquiry_data):
    """Securely save inquiry with validation"""
    try:
        # Ensure we have a dictionary
        if not isinstance(inquiry_data, dict):
            raise ValueError("Invalid inquiry data format")
        
        # Sanitize input data
        sanitized_data = sanitize_input_data(inquiry_data)
        if not isinstance(sanitized_data, dict):
            raise ValueError("Sanitization failed to return dictionary")
        
        # Create new inquiry in database
        inquiry = Inquiry()
        inquiry.name = sanitized_data.get('name', '')
        inquiry.email = sanitized_data.get('email', '')
        inquiry.phone = sanitized_data.get('phone', '')
        inquiry.service = sanitized_data.get('service', '')
        inquiry.message = sanitized_data.get('message', '')
        inquiry.ip_address = request.remote_addr or 'unknown'
        inquiry.is_read = False
        
        db.session.add(inquiry)
        db.session.commit()
        
        # Log the event
        log_security_event('inquiry_submitted', f'Inquiry from {inquiry.email}')
        
    except Exception as e:
        log_security_event('inquiry_save_error', f'Error saving inquiry: {str(e)}')
        db.session.rollback()
        raise

def format_price(amount):
    """Formats a number into a currency string."""
    try:
        # Handle cases where amount might be a string with commas
        numeric_amount = float(str(amount).replace(',', ''))
        return f"${int(numeric_amount):,}"
    except (ValueError, TypeError):
        return "$0"

@app.route('/checkout', methods=['GET'])
def checkout():
    """Display the checkout page with order details from URL parameters."""
    try:
        # Sanitize and retrieve order details from query parameters
        order_type = bleach.clean(request.args.get('type', 'item'))
        
        if order_type == 'tour':
            # Handle tour bookings
            order_details = {
                'type': order_type,
                'name': bleach.clean(request.args.get('name', 'Unknown Tour')),
                'days': int(bleach.clean(request.args.get('riders', '1'))),  # riders for tours
                'base_price_raw': float(bleach.clean(request.args.get('base_price', '0'))),
                'pickup_time': bleach.clean(request.args.get('start_date', '')),  # start_date for tours
                'riding_type': bleach.clean(request.args.get('pickup_time', '')),  # pickup_time for tours
                'addons_str': bleach.clean(request.args.get('addons', '')),
                'final_price': bleach.clean(request.args.get('final_price', '$0')),
                'final_price_raw': float(bleach.clean(request.args.get('final_price', '$0').replace('$', '').replace(',', '')))
            }
        else:
            # Handle bike bookings (updated logic)
            order_details = {
                'type': order_type,
                'name': bleach.clean(request.args.get('name', 'Unknown Item')),
                'days': int(bleach.clean(request.args.get('days', '1'))),
                'bikes': int(bleach.clean(request.args.get('bikes', '1'))),
                'base_price_raw': float(bleach.clean(request.args.get('base_price', '0'))),
                'pickup_datetime': bleach.clean(request.args.get('pickup_datetime', '')),
                'addons_str': bleach.clean(request.args.get('addons', '')),
                'final_price': bleach.clean(request.args.get('final_price', '$0')),
                'final_price_raw': float(bleach.clean(request.args.get('final_price', '$0').replace('$', '').replace(',', '')))
            }

        # Process addons, storing raw price for calculations
        addons = []
        if order_details['addons_str']:
            for addon_item in order_details['addons_str'].split(','):
                name, price_str = addon_item.split('|')
                price = float(price_str)
                # Store the raw price, not the formatted string
                addons.append({'name': name, 'price': price})
        order_details['addons'] = addons
        
        # Recalculate prices on the server-side for security and consistency
        if order_type == 'tour':
            # For tours: base_price * number_of_riders
            subtotal_raw = order_details['base_price_raw'] * order_details['days']
            
            # Apply group discounts for tours
            discount_percent = 0
            if order_details['days'] >= 14:
                discount_percent = 15
            elif order_details['days'] >= 7:
                discount_percent = 10
            elif order_details['days'] >= 3:
                discount_percent = 5
        else:
            # For bikes: base_price * number_of_days * number_of_bikes
            subtotal_raw = order_details['base_price_raw'] * order_details['days'] * order_details['bikes']
            
            # Apply duration discounts for bikes
            discount_percent = 0
            if order_details['days'] >= 14:
                discount_percent = 15
            elif order_details['days'] >= 7:
                discount_percent = 10
            elif order_details['days'] >= 3:
                discount_percent = 5
        
        discount_amount_raw = subtotal_raw * (discount_percent / 100)
        
        # Format for display
        order_details['base_price'] = format_price(order_details['base_price_raw'])
        order_details['subtotal'] = format_price(subtotal_raw)
        order_details['discount'] = discount_percent
        order_details['discount_amount'] = format_price(discount_amount_raw)
        
        # Format pickup datetime for display
        if order_details.get('pickup_datetime'):
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(order_details['pickup_datetime'].replace('Z', '+00:00'))
                order_details['pickup_datetime_formatted'] = dt.strftime('%B %d, %Y at %I:%M %p')
            except:
                order_details['pickup_datetime_formatted'] = order_details['pickup_datetime']
        else:
            order_details['pickup_datetime_formatted'] = 'Not specified'

        return render_template('checkout.html', order_details=order_details)

    except Exception as e:
        log_security_event('checkout_page_error', f'Error loading checkout page: {str(e)}')
        flash('There was an error preparing your order. Please try again.', 'error')
        return redirect(url_for('rentals'))

@app.route('/process-checkout', methods=['POST'])
@limiter.limit("5 per minute")
def process_checkout():
    """Process the checkout form submission."""
    form_data = request.form
    try:
        # Construct a detailed message for the admin
        message_lines = [
            f"NEW BOOKING: {form_data.get('order_type', 'item').upper()}",
            "---",
            f"Item: {form_data.get('item_name', 'N/A')}",
            f"Total Price: {format_price(float(form_data.get('final_price', '0')))}",
            "---"
        ]
        
        if form_data.get('order_type') == 'bike':
            message_lines.extend([
                "RENTAL DETAILS:",
                f"Duration: {form_data.get('rental_days', 'N/A')} days",
                f"Number of Bikes: {form_data.get('number_of_bikes', 'N/A')}",
                f"Pickup Date & Time: {form_data.get('pickup_datetime', 'N/A')}",
            ])
            
            addons_str = form_data.get('addons', '')
            if addons_str:
                message_lines.append("\nADD-ONS:")
                for addon in addons_str.split(','):
                    name, price = addon.split('|')
                    # Calculate total price for the message
                    days = int(form_data.get('rental_days', 1))
                    bikes = int(form_data.get('number_of_bikes', 1))
                    total_addon_price = float(price) * days * bikes
                    price_per_day_formatted = format_price(float(price))
                    total_price_formatted = format_price(total_addon_price)
                    message_lines.append(f"- {name} ({price_per_day_formatted}/day/bike) - Total: {total_price_formatted}")
            message_lines.append("---")
        elif form_data.get('order_type') == 'tour':
            message_lines.extend([
                "TOUR DETAILS:",
                f"Number of Riders: {form_data.get('rental_days', 'N/A')}",
                f"Start Date: {form_data.get('pickup_time', 'N/A')}",
                f"Pickup Time: {form_data.get('riding_type', 'N/A')}",
            ])
            
            addons_str = form_data.get('addons', '')
            if addons_str:
                message_lines.append("\nADD-ONS:")
                for addon in addons_str.split(','):
                    name, price = addon.split('|')
                    # Calculate total price for the message
                    riders = int(form_data.get('rental_days', 1))
                    total_addon_price = float(price) * riders
                    price_per_rider_formatted = format_price(float(price))
                    total_price_formatted = format_price(total_addon_price)
                    message_lines.append(f"- {name} ({price_per_rider_formatted}/rider) - Total: {total_price_formatted}")
            message_lines.append("---")

        # Customer details
        message_lines.extend([
            "CUSTOMER:",
            f"Name: {form_data.get('full_name', 'N/A')}",
            f"Email: {form_data.get('email', 'N/A')}",
            f"Phone: {form_data.get('phone', 'N/A')}"
        ])

        inquiry_data = {
            'name': form_data.get('full_name'),
            'email': form_data.get('email'),
            'phone': form_data.get('phone'),
            'service': 'Online Booking',
            'message': "\n".join(message_lines)
        }
        
        save_inquiry(inquiry_data)
        
        flash('Your booking request has been sent! We will contact you shortly.', 'success')
        return redirect(url_for('thank_you'))

    except Exception as e:
        log_security_event('checkout_process_error', f'Error processing checkout: {str(e)}')
        flash('Sorry, there was an error processing your booking. Please try again.', 'error')
        return redirect(url_for('checkout'))

def secure_file_upload(file):
    """Ultra-secure file upload handling"""
    if not file or file.filename == '':
        return None
    
    # Validate file security
    if not FileSecurityManager.is_allowed_file(file.filename):
        log_security_event('file_upload_rejected', f'Invalid file extension: {file.filename}')
        return None
    
    if file.content_length and file.content_length > FileSecurityManager.MAX_FILE_SIZE:
        log_security_event('file_upload_rejected', f'File too large: {file.content_length} bytes')
        return None
    
    # Generate secure filename
    secure_name = FileSecurityManager.generate_secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_name)
    
    try:
        file.save(file_path)
        log_security_event('file_upload_success', f'File uploaded: {secure_name}')
        return secure_name
    except Exception as e:
        log_security_event('file_upload_error', f'File upload failed: {str(e)}')
        return None

def get_next_id(data_list):
    """Get next available ID for new items"""
    if not data_list:
        return 1
    return max([item['id'] for item in data_list]) + 1

def save_uploaded_file(file):
    """Save uploaded file securely"""
    return secure_file_upload(file)

def delete_uploaded_file(filename):
    """Delete uploaded file if it exists"""
    if filename:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            log_security_event('file_deleted', f'File deleted: {filename}')

def load_staff_data():
    """Load staff data from database"""
    try:
        return get_all_staff()
    except Exception as e:
        log_security_event('staff_data_error', f'Error loading staff data: {str(e)}')
        return []

def save_staff_data(staff_data):
    """Save staff data to database - this function is deprecated, use direct database operations"""
    pass

# Old functions removed - now using SecurityManager and SessionManager

def get_image_path(image_filename):
    """Get the correct path for an image, checking uploads folder first"""
    if not image_filename:
        return 'images/default-placeholder.svg'
    
    # Check if image exists in uploads folder (for admin uploaded images)
    upload_path = os.path.join('static', 'uploads', image_filename)
    if os.path.exists(upload_path):
        return f'uploads/{image_filename}'
    
    # Check if image exists in images folder (for default images)
    images_path = os.path.join('static', 'images', image_filename)
    if os.path.exists(images_path):
        return f'images/{image_filename}'
    
    # Fallback to placeholder
    return 'images/default-placeholder.svg'

@app.context_processor
def inject_admin_status():
    """Inject admin login status and helper functions into all templates"""
    # Use SessionManager for secure session validation
    admin_status = SessionManager.validate_session()
    
    return dict(
        is_admin=admin_status,
        get_image_path=get_image_path,
        format_price=format_price
    )

@app.route('/')
def home():
    try:
        rendered_html = render_template('index.html')
        print(f"DEBUG: RENDERED HTML LENGTH: {len(rendered_html)}")
        print(f"DEBUG: RENDERED HTML SNIPPET: {rendered_html[:500]}")
        return rendered_html
    except Exception as e:
        print(f"FUCKING TEMPLATE RENDERING ERROR: {e}")
        return f"<h1>ERROR RENDERING TEMPLATE: {e}</h1>"

@app.route('/tours')
def tours():
    tours_data = get_all_tours()
    return render_template('tours.html', tours=tours_data)

@app.route('/rentals')
def rentals():
    rentals_data = get_all_rentals()
    return render_template('rentals.html', rentals=rentals_data)

@app.route('/bike/<bike_name>')
def bike_detail(bike_name):
    # Convert URL-safe bike name back to original format
    bike_name_normalized = bike_name.replace('-', ' ').title()
    
    # Find the bike in the database
    bike = Rental.query.filter(Rental.name.ilike(f'%{bike_name_normalized}%')).first()
    
    if not bike:
        flash('Bike not found!', 'error')
        return redirect(url_for('rentals'))
    
    # Get other bikes for similar recommendations
    other_bikes = Rental.query.filter(
        Rental.id != bike.id,
        Rental.available == True
    ).limit(6).all()
    
    all_bikes = get_all_rentals()
    
    return render_template('bike_detail.html', bike=bike, all_bikes=all_bikes, other_bikes=other_bikes)

@app.route('/tour/<tour_name>')
def tour_detail(tour_name):
    # Convert URL-safe tour name back to original format
    tour_name_normalized = tour_name.replace('-', ' ').title()
    
    # Find the tour in the database
    tour = Tour.query.filter(Tour.title.ilike(f'%{tour_name_normalized}%')).first()
    
    if not tour:
        flash('Tour not found!', 'error')
        return redirect(url_for('tours'))
    
    # Get other tours for similar recommendations
    other_tours = Tour.query.filter(
        Tour.id != tour.id,
        Tour.is_active == True
    ).limit(6).all()
    
    all_tours = get_all_tours()
    
    return render_template('tour_detail.html', tour=tour, all_tours=all_tours, other_tours=other_tours)

@app.route('/repairs')
def repairs():
    return render_template('repairs.html')

@app.route('/contact', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Prevent spam
def contact():
    form = ContactForm()
    
    if form.validate_on_submit():
        try:
            # Sanitize and save inquiry
            form.sanitize_data()
            inquiry_data = {
                'name': form.name.data,
                'email': form.email.data,
                'phone': form.phone.data,
                'service': form.service.data,
                'message': form.message.data
            }
            
            save_inquiry(inquiry_data)
            flash('Thank you for your inquiry! We will get back to you soon.', 'success')
            return redirect(url_for('thank_you'))
            
        except Exception as e:
            log_security_event('contact_form_error', f'Contact form error: {str(e)}')
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('contact.html', form=form)

@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

# SEO Routes
@app.route('/robots.txt')
def robots_txt():
    return send_from_directory('static', 'robots.txt')

@app.route('/sitemap.xml')
def sitemap_xml():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/about/raju')
def raju_profile():
    return render_template('raju_profile.html')

@app.route('/about/rohan')
def rohan_profile():
    return render_template('rohan_profile.html')

@app.route('/about/bobby')
def bobby_profile():
    return render_template('bobby_profile.html')

# ADMIN AUTHENTICATION
@app.route('/admin')
def admin_redirect():
    if SessionManager.validate_session():
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("20 per minute")  # Prevent brute force
def admin_login():
    if SessionManager.validate_session():
        return redirect(url_for('admin_dashboard'))
    
    form = LoginForm()
    ip_address = request.remote_addr
    
    # Check if IP is blocked
    if security_manager.is_ip_blocked(ip_address):
        log_security_event('blocked_login_attempt', f'Blocked IP {ip_address} tried to login')
        flash('Too many failed attempts. Please try again later.', 'error')
        return render_template('admin/login.html', form=form)
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Load staff data and verify credentials
        user = Staff.query.filter_by(username=username).first()
        
        if user and PasswordManager.verify_password(user.password_hash, password):
            # Successful login
            security_manager.clear_failed_attempts(ip_address)
            SessionManager.create_secure_session(username, user.role)
            
            # Update last login
            user.last_login = datetime.now()
            db.session.commit()
            
            log_security_event('successful_login', f'User {username} logged in successfully')
            flash('Welcome, Mr. Chhetri.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            # Failed login
            security_manager.record_failed_login(ip_address, username)
            failed_count = security_manager.get_failed_attempt_count(ip_address)
            
            flash(f'Invalid credentials. {5 - failed_count} attempts remaining.', 'error')
    
    return render_template('admin/login.html', form=form)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Admin session ended successfully. Thank you for managing Bullet Basecamp!', 'info')
    return redirect(url_for('home'))

@app.route('/admin/dashboard')
@require_admin
def admin_dashboard():
    # Debug: Print session info
    print("=== SESSION DEBUG ===")
    print("Session data:", dict(session))
    print("User role:", session.get('user_role'))
    print("Username:", session.get('username'))
    print("===================")
    
    # Get stats for dashboard
    tours_count = Tour.query.filter_by(is_active=True).count()
    rentals_count = Rental.query.filter_by(available=True).count()
    inquiries_count = Inquiry.query.count()
    staff_count = Staff.query.filter_by(is_active=True).count()
    
    stats = {
        'tours': tours_count,
        'rentals': rentals_count,
        'inquiries': inquiries_count,
        'staff': staff_count
    }
    
    return render_template('admin/dashboard.html', stats=stats)

# Tours Management
@app.route('/admin/tours')
@require_admin
def admin_tours():
    tours_data = get_all_tours()
    return render_template('admin/tours.html', tours=tours_data)

@app.route('/admin/tours/add', methods=['POST'])
@require_admin
def admin_add_tour_route():
    return admin_add_tour()

@app.route('/admin/tours/edit/<int:tour_id>', methods=['GET', 'POST'])
@require_admin
def admin_edit_tour_route(tour_id):
    return admin_edit_tour(tour_id)

@app.route('/admin/tours/delete/<int:tour_id>', methods=['POST'])
@require_admin
def admin_delete_tour_route(tour_id):
    return admin_delete_tour(tour_id)

# Rentals Management
@app.route('/admin/rentals')
@require_admin
def admin_rentals():
    rentals_data = get_all_rentals()
    return render_template('admin/rentals.html', rentals=rentals_data)

@app.route('/admin/rentals/add', methods=['POST'])
@require_admin
def admin_add_rental_route():
    return admin_add_rental()

@app.route('/admin/rentals/edit/<int:rental_id>', methods=['GET', 'POST'])
@require_admin
def admin_edit_rental_route(rental_id):
    return admin_edit_rental(rental_id)

@app.route('/admin/rentals/delete/<int:rental_id>', methods=['POST'])
@require_admin
def admin_delete_rental_route(rental_id):
    return admin_delete_rental(rental_id)

# Staff Management
@app.route('/admin/staff')
@require_admin
def admin_staff():
    staff_data = get_all_staff()
    return render_template('admin/staff.html', staff_list=staff_data)

@app.route('/admin/staff/add', methods=['POST'])
@require_admin
def admin_add_staff_route():
    return admin_add_staff()

@app.route('/admin/staff/delete/<int:staff_id>', methods=['POST'])
@require_admin
def admin_delete_staff_route(staff_id):
    return admin_delete_staff(staff_id)

# Messages Management
@app.route('/admin/messages')
@require_admin
def admin_messages():
    inquiries_data = get_all_inquiries()
    return render_template('admin/messages.html', messages=inquiries_data)

@app.route('/admin/messages/<int:message_id>')
@require_admin
def admin_message_detail(message_id):
    message = Inquiry.query.get(message_id)
    if not message:
        flash('Message not found!', 'error')
        return redirect(url_for('admin_messages'))
    return render_template('admin/message_detail.html', message=message)

@app.route('/admin/messages/delete/<int:message_id>', methods=['POST'])
@require_admin
def admin_delete_message_route(message_id):
    return admin_delete_message(message_id)

# Session check endpoint
@app.route('/admin/session-check')
@require_admin
def admin_session_check():
    """Check if admin session is still valid"""
    last_activity_timestamp = session.get('last_activity_timestamp', 0)
    current_timestamp = datetime.now().timestamp()
    time_remaining = SESSION_TIMEOUT - (current_timestamp - last_activity_timestamp)
    return jsonify({'status': 'valid', 'time_remaining': max(0, time_remaining)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=True, host='0.0.0.0', port=port) 