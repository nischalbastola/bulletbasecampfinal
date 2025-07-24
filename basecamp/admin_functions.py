"""
Updated admin functions that use database instead of JSON files
These functions replace the old JSON-based admin functions in app.py
"""

from flask import request, flash, redirect, url_for, render_template
from models import db, Tour, Rental, Inquiry, Staff
from security import log_security_event
from datetime import datetime

def get_next_id(model_class):
    """Get next available ID for new items"""
    last_item = model_class.query.order_by(model_class.id.desc()).first()
    return (last_item.id + 1) if last_item else 1

def admin_add_tour():
    """Add new tour to database"""
    try:
        # Handle image upload
        image_filename = 'default-tour.jpg'
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                from app import save_uploaded_file
                uploaded_filename = save_uploaded_file(file)
                if uploaded_filename:
                    image_filename = uploaded_filename
                else:
                    flash('Invalid image file. Please upload PNG, JPG, JPEG, GIF, or WEBP files only.', 'error')
                    return redirect(url_for('admin_tours'))
        
        # Create new tour
        tour = Tour()
        tour.title = request.form.get('title')
        tour.duration = request.form.get('duration')
        tour.difficulty = request.form.get('difficulty')
        tour.price = request.form.get('price')
        tour.description = request.form.get('description')
        tour.image = image_filename
        tour.highlights = [h.strip() for h in request.form.get('highlights', '').split('\n') if h.strip()]
        # Add new key info fields
        tour.keyinfo_duration = request.form.get('keyinfo_duration')
        tour.keyinfo_per_day = request.form.get('keyinfo_per_day')
        tour.keyinfo_difficulty = request.form.get('keyinfo_difficulty')
        tour.keyinfo_altitude = request.form.get('keyinfo_altitude')
        tour.keyinfo_group_size = request.form.get('keyinfo_group_size')
        tour.keyinfo_trip_cost = request.form.get('keyinfo_trip_cost')
        tour.is_active = True
        
        db.session.add(tour)
        db.session.commit()
        
        log_security_event('tour_added', f'New tour added: {tour.title}')
        flash('Tour added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        log_security_event('tour_add_error', f'Error adding tour: {str(e)}')
        flash('Error adding tour. Please try again.', 'error')
    
    return redirect(url_for('admin_tours'))

def admin_edit_tour(tour_id):
    """Edit existing tour in database"""
    tour = Tour.query.get(tour_id)
    
    if not tour:
        flash('Tour not found!', 'error')
        return redirect(url_for('admin_tours'))
    
    if request.method == 'POST':
        try:
            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '':
                    from app import save_uploaded_file, delete_uploaded_file
                    uploaded_filename = save_uploaded_file(file)
                    if uploaded_filename:
                        # Delete old image if it's not default
                        if tour.image != 'default-tour.jpg':
                            delete_uploaded_file(tour.image)
                        tour.image = uploaded_filename
                    else:
                        flash('Invalid image file. Please upload PNG, JPG, JPEG, GIF, or WEBP files only.', 'error')
                        return render_template('admin/edit_tour.html', tour=tour)
            
            # Update tour data
            tour.title = request.form.get('title')
            tour.duration = request.form.get('duration')
            tour.difficulty = request.form.get('difficulty')
            tour.price = request.form.get('price')
            tour.description = request.form.get('description')
            tour.highlights = [h.strip() for h in request.form.get('highlights', '').split('\n') if h.strip()]
            # Update new key info fields
            tour.keyinfo_duration = request.form.get('keyinfo_duration')
            tour.keyinfo_per_day = request.form.get('keyinfo_per_day')
            tour.keyinfo_difficulty = request.form.get('keyinfo_difficulty')
            tour.keyinfo_altitude = request.form.get('keyinfo_altitude')
            tour.keyinfo_group_size = request.form.get('keyinfo_group_size')
            tour.keyinfo_trip_cost = request.form.get('keyinfo_trip_cost')
            
            db.session.commit()
            log_security_event('tour_updated', f'Tour updated: {tour.title}')
            flash('Tour updated successfully!', 'success')
            return redirect(url_for('admin_tours'))
            
        except Exception as e:
            db.session.rollback()
            log_security_event('tour_update_error', f'Error updating tour: {str(e)}')
            flash('Error updating tour. Please try again.', 'error')
    
    return render_template('admin/edit_tour.html', tour=tour)

def admin_delete_tour(tour_id):
    """Delete tour from database"""
    try:
        tour = Tour.query.get(tour_id)
        if not tour:
            flash('Tour not found!', 'error')
            return redirect(url_for('admin_tours'))
        
        # Delete associated image
        if tour.image and tour.image != 'default-tour.jpg':
            from app import delete_uploaded_file
            delete_uploaded_file(tour.image)
        
        tour_title = tour.title
        db.session.delete(tour)
        db.session.commit()
        
        log_security_event('tour_deleted', f'Tour deleted: {tour_title}')
        flash('Tour deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        log_security_event('tour_delete_error', f'Error deleting tour: {str(e)}')
        flash('Error deleting tour. Please try again.', 'error')
    
    return redirect(url_for('admin_tours'))

def admin_add_rental():
    """Add new rental to database"""
    try:
        # Handle image upload
        image_filename = 'default-bike.jpg'
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                from app import save_uploaded_file
                uploaded_filename = save_uploaded_file(file)
                if uploaded_filename:
                    image_filename = uploaded_filename
                else:
                    flash('Invalid image file. Please upload PNG, JPG, JPEG, GIF, or WEBP files only.', 'error')
                    return redirect(url_for('admin_rentals'))
        
        # Create new rental
        rental = Rental()
        rental.name = request.form.get('name')
        rental.category = request.form.get('category')
        rental.price_per_day = request.form.get('price_per_day')
        rental.price_per_week = request.form.get('price_per_week')
        rental.description = request.form.get('description')
        rental.image = image_filename
        rental.specs = {
            'engine': request.form.get('engine'),
            'power': request.form.get('power'),
            'torque': request.form.get('torque'),
            'fuel_capacity': request.form.get('fuel_capacity'),
            'start_mode': request.form.get('start_mode'),
            'weight': request.form.get('weight'),
            'ground_clearance': request.form.get('ground_clearance')
        }
        rental.available = request.form.get('available') == 'on'
        
        db.session.add(rental)
        db.session.commit()
        
        log_security_event('rental_added', f'New rental added: {rental.name}')
        flash('Rental bike added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        log_security_event('rental_add_error', f'Error adding rental: {str(e)}')
        flash('Error adding rental. Please try again.', 'error')
    
    return redirect(url_for('admin_rentals'))

def admin_edit_rental(rental_id):
    """Edit existing rental in database"""
    rental = Rental.query.get(rental_id)
    
    if not rental:
        flash('Rental bike not found!', 'error')
        return redirect(url_for('admin_rentals'))
    
    if request.method == 'POST':
        try:
            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '':
                    from app import save_uploaded_file, delete_uploaded_file
                    uploaded_filename = save_uploaded_file(file)
                    if uploaded_filename:
                        # Delete old image if it's not default
                        if rental.image != 'default-bike.jpg':
                            delete_uploaded_file(rental.image)
                        rental.image = uploaded_filename
                    else:
                        flash('Invalid image file. Please upload PNG, JPG, JPEG, GIF, or WEBP files only.', 'error')
                        return render_template('admin/edit_rental.html', rental=rental)
            
            # Update rental data
            rental.name = request.form.get('name')
            rental.category = request.form.get('category')
            rental.price_per_day = request.form.get('price_per_day')
            rental.price_per_week = request.form.get('price_per_week')
            rental.description = request.form.get('description')
            rental.specs = {
                'engine': request.form.get('engine'),
                'power': request.form.get('power'),
                'torque': request.form.get('torque'),
                'fuel_capacity': request.form.get('fuel_capacity'),
                'start_mode': request.form.get('start_mode'),
                'weight': request.form.get('weight'),
                'ground_clearance': request.form.get('ground_clearance')
            }
            rental.available = request.form.get('available') == 'on'
            
            db.session.commit()
            log_security_event('rental_updated', f'Rental updated: {rental.name}')
            flash('Rental bike updated successfully!', 'success')
            return redirect(url_for('admin_rentals'))
            
        except Exception as e:
            db.session.rollback()
            log_security_event('rental_update_error', f'Error updating rental: {str(e)}')
            flash('Error updating rental. Please try again.', 'error')
    
    return render_template('admin/edit_rental.html', rental=rental)

def admin_delete_rental(rental_id):
    """Delete rental from database"""
    try:
        rental = Rental.query.get(rental_id)
        if not rental:
            flash('Rental bike not found!', 'error')
            return redirect(url_for('admin_rentals'))
        
        # Delete associated image
        if rental.image and rental.image != 'default-bike.jpg':
            from app import delete_uploaded_file
            delete_uploaded_file(rental.image)
        
        rental_name = rental.name
        db.session.delete(rental)
        db.session.commit()
        
        log_security_event('rental_deleted', f'Rental deleted: {rental_name}')
        flash('Rental bike deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        log_security_event('rental_delete_error', f'Error deleting rental: {str(e)}')
        flash('Error deleting rental. Please try again.', 'error')
    
    return redirect(url_for('admin_rentals'))

def admin_add_staff():
    """Add new staff member to database"""
    try:
        from security import PasswordManager
        
        # Create new staff member
        staff = Staff()
        staff.username = request.form.get('username')
        staff.name = request.form.get('name')
        staff.password_hash = PasswordManager.hash_password(request.form.get('password'))
        staff.role = 'staff'
        staff.is_active = True
        
        db.session.add(staff)
        db.session.commit()
        
        log_security_event('staff_added', f'New staff added: {staff.username}')
        flash('Staff member added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        log_security_event('staff_add_error', f'Error adding staff: {str(e)}')
        flash('Error adding staff. Please try again.', 'error')
    
    return redirect(url_for('admin_staff'))

def admin_delete_staff(staff_id):
    """Delete staff member from database"""
    try:
        staff = Staff.query.get(staff_id)
        if not staff:
            flash('Staff member not found!', 'error')
            return redirect(url_for('admin_staff'))
        
        # Don't allow deleting admin users
        if staff.role == 'admin':
            flash('Cannot delete admin users!', 'error')
            return redirect(url_for('admin_staff'))
        
        staff_username = staff.username
        db.session.delete(staff)
        db.session.commit()
        
        log_security_event('staff_deleted', f'Staff deleted: {staff_username}')
        flash('Staff member deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        log_security_event('staff_delete_error', f'Error deleting staff: {str(e)}')
        flash('Error deleting staff. Please try again.', 'error')
    
    return redirect(url_for('admin_staff'))

def admin_delete_message(message_id):
    """Delete inquiry/message from database"""
    try:
        inquiry = Inquiry.query.get(message_id)
        if not inquiry:
            flash('Message not found!', 'error')
            return redirect(url_for('admin_messages'))
        
        inquiry_email = inquiry.email
        db.session.delete(inquiry)
        db.session.commit()
        
        log_security_event('message_deleted', f'Message deleted from: {inquiry_email}')
        flash('Message deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        log_security_event('message_delete_error', f'Error deleting message: {str(e)}')
        flash('Error deleting message. Please try again.', 'error')
    
    return redirect(url_for('admin_messages')) 