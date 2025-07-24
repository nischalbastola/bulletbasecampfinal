# Database Setup Guide for Bullet Basecamp

This guide will help you migrate from JSON files to a proper SQL database for better performance, data integrity, and scalability.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
python init_db.py
```

### 3. Migrate Existing Data (Optional)
```bash
python migrate_to_db.py
```

### 4. Start Application
```bash
python app.py
```

## 📊 Database Models

### Tours
- **id**: Primary key
- **title**: Tour name (unique)
- **duration**: Tour duration (e.g., "12 days")
- **difficulty**: Difficulty level (Beginner, Intermediate, Advanced, Expert)
- **price**: Price in NPR
- **description**: Detailed tour description
- **image**: Image filename
- **highlights**: JSON array of tour highlights
- **is_active**: Whether tour is available
- **created_at/updated_at**: Timestamps

### Rentals
- **id**: Primary key
- **name**: Bike name (unique)
- **category**: Bike category (Adventure, Sport, Premium, etc.)
- **price_per_day**: Daily rental price
- **price_per_week**: Weekly rental price
- **description**: Bike description
- **image**: Image filename
- **specs**: JSON object with bike specifications
- **available**: Whether bike is available
- **created_at/updated_at**: Timestamps

### Inquiries
- **id**: Primary key
- **name**: Customer name
- **email**: Customer email
- **phone**: Customer phone
- **service**: Service type (Bike Rental, Tour, etc.)
- **message**: Inquiry message
- **ip_address**: Customer IP address
- **is_read**: Whether inquiry has been read
- **created_at/updated_at**: Timestamps

### Staff
- **id**: Primary key
- **username**: Username (unique)
- **name**: Full name
- **password_hash**: Hashed password
- **role**: Role (admin, staff)
- **email**: Email address
- **phone**: Phone number
- **is_active**: Whether account is active
- **last_login**: Last login timestamp
- **created_at/updated_at**: Timestamps

### Security Logs
- **id**: Primary key
- **event_type**: Type of security event
- **description**: Event description
- **ip_address**: IP address
- **user_agent**: User agent string
- **severity**: Severity level (info, warning, error, critical)
- **created_at**: Timestamp

### Bookings
- **id**: Primary key
- **customer_name**: Customer name
- **customer_email**: Customer email
- **customer_phone**: Customer phone
- **booking_type**: Type (tour, rental)
- **item_id**: Tour or rental ID
- **item_name**: Tour or rental name
- **start_date**: Start date
- **end_date**: End date
- **total_price**: Total price
- **status**: Booking status (pending, confirmed, cancelled, completed)
- **special_requests**: Special requests
- **ip_address**: Customer IP
- **created_at/updated_at**: Timestamps

## 🔧 Configuration

### Development (SQLite)
```env
DATABASE_URL=sqlite:///basecamp.db
```

### Production (PostgreSQL)
```env
DATABASE_URL=postgresql://username:password@localhost:5432/basecamp_db
```

### Production (MySQL)
```env
DATABASE_URL=mysql://username:password@localhost:3306/basecamp_db
```

## 📈 Benefits of Database Migration

### Performance
- **Faster queries**: SQL queries are much faster than JSON file operations
- **Indexing**: Database indexes improve search performance
- **Connection pooling**: Efficient database connections

### Data Integrity
- **ACID compliance**: Transactions ensure data consistency
- **Foreign keys**: Maintain referential integrity
- **Constraints**: Prevent invalid data

### Scalability
- **Concurrent access**: Multiple users can access data simultaneously
- **Large datasets**: Handle thousands of records efficiently
- **Backup/restore**: Easy database backup and recovery

### Security
- **SQL injection protection**: Parameterized queries prevent attacks
- **Access control**: Database-level security
- **Audit trails**: Track all data changes

## 🛠️ Database Operations

### Using SQLAlchemy ORM

```python
# Get all active tours
tours = Tour.query.filter_by(is_active=True).all()

# Get tour by ID
tour = Tour.query.get(1)

# Create new tour
new_tour = Tour()
new_tour.title = "New Tour"
new_tour.duration = "5 days"
# ... set other fields
db.session.add(new_tour)
db.session.commit()

# Update tour
tour = Tour.query.get(1)
tour.price = "NPR 25,000"
db.session.commit()

# Delete tour
tour = Tour.query.get(1)
db.session.delete(tour)
db.session.commit()
```

### Raw SQL Queries

```python
# Execute raw SQL
result = db.session.execute("SELECT * FROM tours WHERE is_active = 1")
tours = result.fetchall()
```

## 🔍 Database Management

### View Database
```bash
# SQLite
sqlite3 basecamp.db
.tables
.schema tours
SELECT * FROM tours;
```

### Backup Database
```bash
# SQLite
cp basecamp.db basecamp_backup.db

# PostgreSQL
pg_dump basecamp_db > backup.sql
```

### Reset Database
```bash
# Remove database file
rm basecamp.db

# Reinitialize
python init_db.py
python migrate_to_db.py
```

## 🚨 Troubleshooting

### Common Issues

1. **Database locked**: Close all connections and restart
2. **Migration errors**: Check JSON file format
3. **Permission errors**: Ensure write permissions to directory

### Debug Mode
```python
# Enable SQLAlchemy logging
app.config['SQLALCHEMY_ECHO'] = True
```

## 📚 Additional Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Flask-SQLAlchemy Documentation](https://flask-sqlalchemy.palletsprojects.com/)
- [Database Design Best Practices](https://www.postgresql.org/docs/current/ddl.html)

## 🎯 Next Steps

1. **Test the application** with the new database
2. **Monitor performance** and optimize queries if needed
3. **Set up regular backups** for production
4. **Consider database migrations** for future schema changes
5. **Implement connection pooling** for production deployments 