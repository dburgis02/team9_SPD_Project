from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from datetime import datetime
import traceback
from werkzeug.utils import secure_filename
import os
from PIL import Image

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# UPLOAD_FOLDER = 'static/uploads/resources'
# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


CATEGORIES = [
    'Tools',
    'Garden Equipment',
    'Electronics',
    'Sports Equipment',
    'Books',
    'Kitchen Appliances',
    'DIY Equipment',
    'Other'
]

SPACE_TYPES = [
    'Meeting Room',
    'Garden Plot',
    'Event Hall',
    'Workshop Space',
    'Storage Space',
    'Parking Space'
]


# Helper functions
def get_db_connection():
    db_path = 'neighborhood_exchange.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with our tables"""
    conn = get_db_connection()
    cur = conn.cursor()

    # Create Users table
    # cur.execute('''
    # CREATE TABLE IF NOT EXISTS users (
    # user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    # name TEXT NOT NULL,
    # email TEXT UNIQUE NOT NULL,
    # password TEXT NOT NULL,
    # location TEXT
    # )
    # ''')

    # Create Resources table
    # cur.execute('''
    # CREATE TABLE IF NOT EXISTS resources (
    # resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
    # user_id INTEGER,
    # title TEXT NOT NULL,
    # description TEXT,
    # category TEXT,
    # image_path TEXT,
    # available_from DATE NOT NULL,
    # available_until DATE NOT NULL,
    # max_borrow_days INTEGER NOT NULL,
    # is_available BOOLEAN DEFAULT 1,
    # date_posted TEXT NOT NULL,
    # FOREIGN KEY (user_id) REFERENCES users (user_id)
    # )
    # ''')

    # Create Reviews table
    # cur.execute('''
    # CREATE TABLE IF NOT EXISTS reviews (
    # review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    # user_id INTEGER,
    # reviewer_id INTEGER,
    # rating INTEGER NOT NULL,
    # comment TEXT,
    # timestamp TEXT NOT NULL,
    # FOREIGN KEY (user_id) REFERENCES users (user_id),
    # FOREIGN KEY (reviewer_id) REFERENCES users (user_id)
    # )
    # ''')

    # Create Reservations table
    # cur.execute('''
    # CREATE TABLE IF NOT EXISTS reservations (
    # reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    # resource_id INTEGER,
    # user_id INTEGER,
    # start_date DATE NOT NULL,
    # end_date DATE NOT NULL,
    # status TEXT DEFAULT 'approved',  -- pending, approved, completed, cancelled
    # created_at DATETIME NOT NULL,
    # FOREIGN KEY (resource_id) REFERENCES resources (resource_id),
    # FOREIGN KEY (user_id) REFERENCES users (user_id)
    # )
    # ''')

    # cur.execute('''
    # CREATE TABLE IF NOT EXISTS messages (
    # message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    # sender_id INTEGER NOT NULL,
    # receiver_id INTEGER NOT NULL,
    # message_text TEXT NOT NULL,
    # timestamp DATETIME NOT NULL,
    # is_read BOOLEAN DEFAULT 0,
    # FOREIGN KEY (sender_id) REFERENCES users (user_id),
    # FOREIGN KEY (receiver_id) REFERENCES users (user_id)
    # )
    # ''')

    # cur.execute('''
    # CREATE TABLE IF NOT EXISTS spaces (
    # space_id INTEGER PRIMARY KEY AUTOINCREMENT,
    # name TEXT NOT NULL,
    # type TEXT NOT NULL,
    # description TEXT,
    # capacity INTEGER NOT NULL,
    # hourly_rate DECIMAL(10,2) NOT NULL,
    # amenities TEXT,
    # image_path TEXT,
    # owner_id INTEGER,
    # FOREIGN KEY (owner_id) REFERENCES users (user_id)
    # )
    # ''')

    # Create Space Bookings table
    # cur.execute('''
    # CREATE TABLE IF NOT EXISTS space_bookings (
    # booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    # space_id INTEGER NOT NULL,
    # user_id INTEGER NOT NULL,
    # date DATE NOT NULL,
    # start_time TIME NOT NULL,
    # end_time TIME NOT NULL,
    # event_name TEXT NOT NULL,
    # event_description TEXT,
    # attendees INTEGER NOT NULL,
    # status TEXT DEFAULT 'pending',
    # created_at DATETIME NOT NULL,
    # FOREIGN KEY (space_id) REFERENCES spaces (space_id),
    # FOREIGN KEY (user_id) REFERENCES users (user_id)
    # )
    # ''')
    # conn.commit()
    # conn.close()


# Initialize database when app starts
with app.app_context():
    init_db()


def reset_resources_table():
    conn = get_db_connection()
    cur = conn.cursor()
    # Drop the existing resources table if it exists
    cur.execute("DROP TABLE IF EXISTS resources")
    # Recreate the resources table with all required columns
    cur.execute('''
        CREATE TABLE resources (
            resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            image_front TEXT,
            image_back TEXT,
            available_from DATE NOT NULL,
            available_until DATE NOT NULL,
            max_borrow_days INTEGER NOT NULL,
            is_available BOOLEAN DEFAULT 1,
            date_posted TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# Routes
@app.route('/')
def home():
    conn = get_db_connection()
    try:
        featured_items = conn.execute('''
            SELECT * FROM resources 
            WHERE is_available = 1 
            ORDER BY date_posted DESC 
            LIMIT 6
        ''').fetchall()
        return render_template('home.html', featured_items=featured_items)
    finally:
        conn.close()


@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        # Fetch item details
        item = conn.execute('''
            SELECT * FROM resources WHERE resource_id = ? AND user_id = ?
        ''', (item_id, session['user_id'])).fetchone()

        if not item:
            flash('Item not found or access denied.', 'danger')
            return redirect(url_for('profile'))

        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            category = request.form['category']
            max_borrow_days = request.form['max_borrow_days']
            available_from = request.form['available_from']
            available_until = request.form['available_until']

            # Update the item in the database
            conn.execute('''
                UPDATE resources
                SET title = ?, description = ?, category = ?, max_borrow_days = ?, available_from = ?, available_until = ?
                WHERE resource_id = ? AND user_id = ?
            ''', (title, description, category, max_borrow_days, available_from, available_until, item_id,
                  session['user_id']))
            conn.commit()

            flash('Item updated successfully.', 'success')
            return redirect(url_for('profile'))

        return render_template('edit_item.html', item=item)
    finally:
        conn.close()


@app.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        # Delete the item from the database
        conn.execute('''
            DELETE FROM resources
            WHERE resource_id = ? AND user_id = ?
        ''', (item_id, session['user_id']))
        conn.commit()

        flash('Item deleted successfully.', 'success')
        return redirect(url_for('profile'))
    finally:
        conn.close()


@app.route('/edit_reservation/<int:reservation_id>', methods=['GET', 'POST'])
def edit_reservation(reservation_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        # Fetch reservation details
        reservation = conn.execute('''
            SELECT r.*, res.title
            FROM reservations r
            JOIN resources res ON r.resource_id = res.resource_id
            WHERE r.reservation_id = ? AND r.user_id = ?
        ''', (reservation_id, session['user_id'])).fetchone()

        if not reservation:
            flash('Reservation not found or access denied.', 'danger')
            return redirect(url_for('profile'))

        if request.method == 'POST':
            start_date = request.form['start_date']
            end_date = request.form['end_date']

            # Update the reservation in the database
            conn.execute('''
                UPDATE reservations
                SET start_date = ?, end_date = ?
                WHERE reservation_id = ? AND user_id = ?
            ''', (start_date, end_date, reservation_id, session['user_id']))
            conn.commit()

            flash('Reservation updated successfully.', 'success')
            return redirect(url_for('profile'))

        return render_template('edit_reservation.html', reservation=reservation)
    finally:
        conn.close()

@app.route('/messages')
def messages():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        # Get all users for new conversations - removed profile_image from SELECT
        all_users = conn.execute('''
            SELECT user_id, name 
            FROM users 
            ORDER BY name
        ''').fetchall()

        # Get existing conversations - removed profile_image from query
        conversations = conn.execute('''
            SELECT DISTINCT 
                u.user_id,
                u.name,
                (SELECT message_text 
                 FROM messages 
                 WHERE (sender_id = ? AND receiver_id = u.user_id) 
                    OR (sender_id = u.user_id AND receiver_id = ?)
                 ORDER BY timestamp DESC 
                 LIMIT 1) as last_message,
                (SELECT timestamp 
                 FROM messages 
                 WHERE (sender_id = ? AND receiver_id = u.user_id) 
                    OR (sender_id = u.user_id AND receiver_id = ?)
                 ORDER BY timestamp DESC 
                 LIMIT 1) as last_timestamp,
                (SELECT COUNT(*) 
                 FROM messages 
                 WHERE sender_id = u.user_id 
                    AND receiver_id = ? 
                    AND is_read = 0) as unread_count
            FROM users u
            WHERE u.user_id IN (
                SELECT sender_id FROM messages WHERE receiver_id = ?
                UNION
                SELECT receiver_id FROM messages WHERE sender_id = ?
            )
            ORDER BY last_timestamp DESC
        ''', [session['user_id']] * 7).fetchall()

        return render_template('messages.html',
                               conversations=conversations,
                               all_users=all_users)
    finally:
        conn.close()


@app.route('/conversation/<int:user_id>', methods=['GET', 'POST'])
def conversation(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        # Get the other user's info
        other_user = conn.execute('''
            SELECT * FROM users WHERE user_id = ?
        ''', [user_id]).fetchone()

        if not other_user:
            flash('User not found')
            return redirect(url_for('messages'))

        if request.method == 'POST':
            message_text = request.form.get('message')
            if message_text:
                # Insert the message
                conn.execute('''
                    INSERT INTO messages 
                    (sender_id, receiver_id, message_text, timestamp, is_read)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    session['user_id'],
                    user_id,
                    message_text,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    0
                ))
                conn.commit()

                # After inserting, get all messages again
                messages = conn.execute('''
                    SELECT * FROM messages
                    WHERE (sender_id = ? AND receiver_id = ?)
                    OR (sender_id = ? AND receiver_id = ?)
                    ORDER BY timestamp ASC
                ''', [session['user_id'], user_id, user_id, session['user_id']]).fetchall()

                # Return success response
                return ('', 204)

            return 'Message cannot be empty', 400

        # Get all messages between users
        messages = conn.execute('''
            SELECT m.*, u.name as sender_name
            FROM messages m
            JOIN users u ON m.sender_id = u.user_id
            WHERE (m.sender_id = ? AND m.receiver_id = ?) 
            OR (m.sender_id = ? AND m.receiver_id = ?)
            ORDER BY m.timestamp ASC
        ''', [session['user_id'], user_id, user_id, session['user_id']]).fetchall()

        # Mark received messages as read
        conn.execute('''
            UPDATE messages 
            SET is_read = 1 
            WHERE sender_id = ? AND receiver_id = ? AND is_read = 0
        ''', [user_id, session['user_id']])
        conn.commit()

        return render_template('conversation.html',
                               messages=messages,
                               other_user=other_user)

    except Exception as e:
        print(f"Error in conversation: {e}")
        flash('An error occurred')
        return redirect(url_for('messages'))
    finally:
        conn.close()


@app.route('/browse')
def browse():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    current_user_id = session['user_id']
    selected_category = request.args.get('category')
    search_query = request.args.get('search', '').strip()

    conn = get_db_connection()
    try:
        # Updated query to include total reviews and averages
        query = '''
            SELECT r.*, 
                   u.name as owner_name,
                   COUNT(DISTINCT pr.preview_id) as review_count,
                   AVG(pr.rating) as avg_rating,
                   (SELECT COUNT(*) 
                    FROM borrower_reviews br 
                    WHERE br.user_id = r.user_id) as owner_review_count,
                   (SELECT AVG(rating) 
                    FROM borrower_reviews br 
                    WHERE br.user_id = r.user_id) as owner_rating
            FROM resources r
            JOIN users u ON r.user_id = u.user_id 
            LEFT JOIN product_reviews pr ON r.resource_id = pr.resource_id
        '''
        params = []

        where_clauses = []

        if selected_category and selected_category != "All Items":
            where_clauses.append("r.category = ?")
            params.append(selected_category)

        if search_query:
            where_clauses.append('''(
                r.title LIKE ? 
                OR r.description LIKE ? 
                OR r.category LIKE ?
                OR u.name LIKE ?
            )''')
            search_param = f'%{search_query}%'
            params.extend([search_param] * 4)

        if where_clauses:
            query += ' WHERE ' + ' AND '.join(where_clauses)

        query += ''' 
            GROUP BY r.resource_id
            ORDER BY r.date_posted DESC
        '''

        resources = conn.execute(query, params).fetchall()

        return render_template('browse.html',
                               resources=resources,
                               categories=CATEGORIES,
                               selected_category=selected_category,
                               search_query=search_query)

    finally:
        conn.close()


@app.route('/book-space/<int:space_id>', methods=['GET', 'POST'])
def book_space(space_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()

    try:
        # Get space details
        space = conn.execute('''
            SELECT s.*, u.name as owner_name 
            FROM spaces s
            JOIN users u ON s.owner_id = u.user_id
            WHERE s.space_id = ?
        ''', [space_id]).fetchone()

        if not space:
            flash('Space not found')
            return redirect(url_for('spaces'))

        if request.method == 'POST':
            date = request.form.get('date')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            event_name = request.form.get('event_name')
            event_description = request.form.get('event_description')
            attendees = request.form.get('attendees')

            # Check for time conflicts
            existing = conn.execute('''
                SELECT * FROM space_bookings
                WHERE space_id = ? AND date = ?
                AND ((start_time <= ? AND end_time > ?)
                OR (start_time < ? AND end_time >= ?)
                OR (start_time >= ? AND end_time <= ?))
            ''', [space_id, date, end_time, start_time,
                  end_time, start_time, start_time, end_time]).fetchone()

            if existing:
                flash("This time slot is already booked")
                return render_template('book_space.html',
                                       space=space,
                                       today=datetime.now().strftime('%Y-%m-%d'))

            # Create booking
            conn.execute('''
                INSERT INTO space_bookings 
                (space_id, user_id, date, start_time, end_time,
                 event_name, event_description, attendees, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                space_id,
                session['user_id'],
                date,
                start_time,
                end_time,
                event_name,
                event_description,
                attendees,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])

            conn.commit()
            flash('Space booked successfully!')
            return redirect(url_for('profile'))

        # Get existing bookings for this space
        existing_bookings = conn.execute('''
            SELECT * FROM space_bookings
            WHERE space_id = ? AND date >= ?
            ORDER BY date, start_time
        ''', [space_id, datetime.now().strftime('%Y-%m-%d')]).fetchall()

        return render_template('book_space.html',
                               space=space,
                               existing_bookings=existing_bookings,
                               today=datetime.now().strftime('%Y-%m-%d'))

    except Exception as e:
        print(f"Error booking space: {e}")
        flash('An error occurred while booking the space')
        return redirect(url_for('spaces'))
    finally:
        conn.close()


@app.route('/add-neighborhood-spaces')
def add_neighborhood_spaces():
    conn = get_db_connection()
    try:
        # Clear existing spaces first (optional)
        conn.execute('DELETE FROM spaces')

        # Add specific spaces
        neighborhood_spaces = [
            (
                'Community Garden Plot A',
                'Garden Plot',
                'A 10x10 garden plot with rich soil, perfect for growing vegetables and flowers. Includes access to water and shared tools.',
                4,
                15.00,
                'Water Access, Shared Tool Shed, Composting Area, Fenced Area',
                '/static/uploads/spaces/garden_plot.jpg',
                1
            ),
            (
                'Main Event Hall',
                'Event Hall',
                'Spacious 2000 sq ft hall perfect for neighborhood gatherings, parties, and meetings. Features a full kitchen and modern amenities.',
                150,
                75.00,
                'Full Kitchen, PA System, Tables & Chairs, WiFi, Projector Screen',
                '/static/uploads/spaces/event_hall.jpg',
                1
            ),
            (
                'Workshop Space',
                'Workshop Space',
                'Fully equipped workshop perfect for DIY projects, woodworking, or craft sessions. Includes basic tools and workbenches.',
                10,
                35.00,
                'Power Tools, Workbenches, Safety Equipment, Storage Space',
                '/static/uploads/spaces/workshop.jpg',
                1
            ),
            (
                'Conference Room',
                'Meeting Room',
                'Professional meeting room with modern amenities, ideal for business meetings or study groups.',
                12,
                25.00,
                'Smart TV, Whiteboard, Conference Phone, High-Speed Internet',
                '/static/uploads/spaces/conference.jpg',
                1
            ),
            (
                'Outdoor Pavilion',
                'Event Hall',
                'Covered outdoor space perfect for picnics, BBQs, or outdoor gatherings. Features built-in grills and picnic tables.',
                50,
                40.00,
                'BBQ Grills, Picnic Tables, Lighting, Electrical Outlets',
                '/static/uploads/spaces/pavilion.jpg',
                1
            ),
            (
                'Study Room',
                'Meeting Room',
                'Quiet study space perfect for small groups or individual work. Equipped with charging stations and whiteboards.',
                6,
                15.00,
                'Whiteboards, Charging Stations, WiFi, Desk & Chairs',
                '/static/uploads/spaces/study_room.jpg',
                1
            )
        ]

        for space in neighborhood_spaces:
            conn.execute('''
                INSERT INTO spaces 
                (name, type, description, capacity, hourly_rate, amenities, image_path, owner_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', space)

        conn.commit()
        return "Neighborhood spaces added successfully!"
    except Exception as e:
        return f"Error adding spaces: {e}"
    finally:
        conn.close()


@app.route('/submit-review', methods=['POST'])
def submit_review():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        reviewer_id = session['user_id']
        resource_id = request.form.get('resource_id')
        user_id = request.form.get('user_id')
        rating = int(request.form.get('rating'))
        comment = request.form.get('comment')
        review_type = request.form.get('review_type')

        if not rating or rating < 1 or rating > 5:
            flash('Please provide a valid rating (1-5 stars)')
            return redirect(url_for('profile'))

        conn = get_db_connection()
        try:
            # Always create a new review instead of updating
            if review_type == 'item':
                conn.execute('''
                    INSERT INTO product_reviews 
                    (reviewer_id, resource_id, rating, comment, timestamp)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (reviewer_id, resource_id, rating, comment))

            elif review_type == 'user':
                conn.execute('''
                    INSERT INTO borrower_reviews 
                    (reviewer_id, user_id, rating, comment, timestamp)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (reviewer_id, user_id, rating, comment))

            conn.commit()
            flash('Review submitted successfully!')

        finally:
            conn.close()

    except Exception as e:
        print(f"Error processing review: {e}")
        flash('Error processing your review')

    return redirect(url_for('profile'))

UPLOADS_PROFILES = 'static/uploads/Profiles'
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        user = conn.execute('SELECT * FROM users WHERE user_id = ?',
                            [session['user_id']]).fetchone()

        user_dict = dict(user)

        # No need to modify the path - template will handle it
        print(f"Profile image path: {user_dict.get('profile_image')}")  # For debugging

        resources = conn.execute('''
            SELECT * FROM resources 
            WHERE user_id = ? 
            ORDER BY date_posted DESC
        ''', [session['user_id']]).fetchall()

        # Fix profile image path if it exists
        if user_dict['profile_image']:
            # Make sure the path is relative to static folder
            if user_dict['profile_image'].startswith('static/'):
                user_dict['profile_image'] = user_dict['profile_image']
            else:
                user_dict['profile_image'] = f"static/{user_dict['profile_image']}"

        # Get user's posted resources
        resources = conn.execute('''
            SELECT * FROM resources 
            WHERE user_id = ? 
            ORDER BY date_posted DESC
        ''', [session['user_id']]).fetchall()
        resources = [dict(resource) for resource in resources]  # Convert rows to dictionaries

        # Get user's reservations
        reservations = conn.execute('''
            SELECT r.*, res.title, res.description, 
                   res.category, u.name as owner_name,
                   res.available_from, res.available_until,
                   r.start_date, r.end_date, r.status
            FROM reservations r
            JOIN resources res ON r.resource_id = res.resource_id
            JOIN users u ON res.user_id = u.user_id
            WHERE r.user_id = ?
            ORDER BY r.timestamp DESC
        ''', [session['user_id']]).fetchall()
        reservations = [dict(reservation) for reservation in reservations]  # Convert rows to dictionaries
        # Get reviews for the user's items
        product_reviews = conn.execute('''
            SELECT pr.*, u.name as reviewer_name, res.title as resource_title
            FROM product_reviews pr
            JOIN users u ON pr.reviewer_id = u.user_id
            LEFT JOIN resources res ON pr.resource_id = res.resource_id
            WHERE pr.resource_id IN (SELECT resource_id FROM resources WHERE user_id = ?)
            ORDER BY pr.timestamp DESC
        ''', [session['user_id']]).fetchall()

        # Get reviews about the user
        borrower_reviews = conn.execute('''
            SELECT br.*, u.name as reviewer_name
            FROM borrower_reviews br
            JOIN users u ON br.reviewer_id = u.user_id
            WHERE br.user_id = ?
            ORDER BY br.timestamp DESC
        ''', [session['user_id']]).fetchall()

        # Calculate average ratings
        avg_user_rating = conn.execute('''
            SELECT AVG(rating) as avg_rating
            FROM borrower_reviews
            WHERE user_id = ?
        ''', [session['user_id']]).fetchone()['avg_rating'] or 0

        return render_template('profile.html',
                               user=user_dict,
                               resources=resources,
                               reservations=reservations,
                               product_reviews=product_reviews,
                               borrower_reviews=borrower_reviews,
                               avg_rating=round(avg_user_rating, 1))
    finally:
        conn.close()


@app.route('/reserve/<int:item_id>', methods=['GET', 'POST'])
def reserve_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()

    try:
        # Get item details with owner info and ratings
        item = conn.execute('''
            SELECT r.*, u.name as owner_name, u.user_id as owner_id,
                   COUNT(DISTINCT pr.preview_id) as review_count,
                   AVG(pr.rating) as avg_rating
            FROM resources r
            JOIN users u ON r.user_id = u.user_id
            LEFT JOIN product_reviews pr ON r.resource_id = pr.resource_id
            WHERE r.resource_id = ?
            GROUP BY r.resource_id
        ''', [item_id]).fetchone()

        if not item:
            flash('Item not found.', 'danger')
            return redirect(url_for('browse'))

        # Get all reviews for this item
        item_reviews = conn.execute('''
            SELECT pr.*, u.name as reviewer_name
            FROM product_reviews pr
            JOIN users u ON pr.reviewer_id = u.user_id
            WHERE pr.resource_id = ?
            ORDER BY pr.timestamp DESC
        ''', [item_id]).fetchall()

        # Get owner's overall rating
        owner_rating = conn.execute('''
            SELECT COUNT(*) as total_reviews,
                   AVG(rating) as avg_rating
            FROM borrower_reviews
            WHERE user_id = ?
        ''', [item['owner_id']]).fetchone()

        if request.method == 'POST':
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')

            # Validate reservation dates
            if start_date >= end_date:
                return render_template('reserve_item.html',
                                       item=item,
                                       item_reviews=item_reviews,
                                       owner_rating=owner_rating,
                                       error="Start date must be before end date.")

            # Calculate reservation duration
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            reservation_duration = (end_date_obj - start_date_obj).days + 1

            # Check against max_borrow_days
            if reservation_duration > item['max_borrow_days']:
                return render_template('reserve_item.html',
                                       item=item,
                                       item_reviews=item_reviews,
                                       owner_rating=owner_rating,
                                       error=f"Reservation exceeds maximum allowed duration of {item['max_borrow_days']} days.")

            # Check for overlapping reservations
            existing_reservations = conn.execute('''
                SELECT start_date, end_date 
                FROM reservations 
                WHERE resource_id = ? 
                AND status = 'approved'
                AND (start_date <= ? AND end_date >= ?)
            ''', [item_id, end_date, start_date]).fetchall()

            if existing_reservations:
                return render_template('reserve_item.html',
                                       item=item,
                                       item_reviews=item_reviews,
                                       owner_rating=owner_rating,
                                       error="These dates are not available. Please select different dates.")

            # Create the reservation
            try:
                conn.execute('''
                                   INSERT INTO reservations 
                                   (resource_id, user_id, start_date, end_date, status, created_at)
                                   VALUES (?, ?, ?, ?, 'approved', ?)
                               ''', (
                    item_id,
                    session['user_id'],
                    start_date,
                    end_date,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                conn.commit()
                flash('Reservation successful!', 'success')
                return redirect(url_for('profile'))

            except Exception as e:
                print(f"Error processing reservation: {e}")
                return render_template('reserve_item.html',
                                       item=item,
                                       item_reviews=item_reviews,
                                       owner_rating=owner_rating,
                                       error="Error processing reservation. Please try again.")

        # Get existing reservations for display
        existing_reservations = conn.execute('''
                           SELECT start_date, end_date 
                           FROM reservations 
                           WHERE resource_id = ? 
                           AND status = 'approved'
                           ORDER BY start_date
                       ''', [item_id]).fetchall()

        formatted_reservations = [
            {'start_date': res['start_date'], 'end_date': res['end_date']}
            for res in existing_reservations
        ]

        return render_template('reserve_item.html',
                               item=item,
                               item_reviews=item_reviews,
                               owner_rating=owner_rating,
                               existing_reservations=formatted_reservations)

    except Exception as e:
        print(f"Error in reserve_item: {e}")
        flash('An error occurred', 'error')
        return redirect(url_for('browse'))
    finally:
        conn.close()


UPLOADS_RESOURCES = 'static/uploads/Resource_Images'
@app.route('/add-item', methods=['GET', 'POST'])
def add_item():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == "GET":
        return render_template('add_item.html', form_data={})

    elif request.method == "POST":
        # Get form data
        title = request.form.get("title")
        description = request.form.get("description")
        category = request.form.get("category", "")
        front_image = request.files["front_image"]
        second_image = request.files["second_image"]
        third_image = request.files["third_image"]
        available_from = request.form.get("available_from", "")
        available_until = request.form.get("available_until", "")
        max_borrow_days = request.form.get("max_borrow_days", "")

        # Store form data for re-rendering in case of error
        form_data = {
            'title': title,
            'description': description,
            'category': category,
            'available_from': available_from,
            'available_until': available_until,
            'max_borrow_days': max_borrow_days
        }

        # Convert to datetime objects for comparison
        available_from_obj = datetime.strptime(available_from, "%Y-%m-%d")
        available_until_obj = datetime.strptime(available_until, "%Y-%m-%d")

        # Validate that the availability period is long enough for the max borrow days
        if (available_until_obj - available_from_obj).days < int(max_borrow_days):
            return render_template('add_item.html',
                                   error="Availability period must be at least as long as the maximum borrow days.",
                                   form_data=form_data)

        # Validate inputs
        if not all([title, description, category, front_image, available_from, available_until, max_borrow_days]):
            return render_template('add_item.html',
                                   error="Please fill all required fields.",
                                   form_data=form_data)

        #Setting Date and Time
        Datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ImageTimestamp = datetime.now().strftime("%Y%m%d")

        # Save images
        if front_image:
            formatted_title = title.replace(" ", "_")
            new_frontimagename = f'{formatted_title}_{ImageTimestamp}_frontimage.png'
            front_file_path = f'{UPLOADS_RESOURCES}/{new_frontimagename}'
            image = Image.open(front_image)
            image.save(front_file_path, format='PNG')

        if second_image:
            formatted_title = title.replace(" ", "_")
            new_secondimagename = f'{formatted_title}_{ImageTimestamp}_secondimage.png'
            second_file_path = f'{UPLOADS_RESOURCES}/{new_secondimagename}'
            image = Image.open(second_image)
            image.save(second_file_path, format="PNG")
        else:
            second_file_path = None

        if third_image:
            formatted_title = title.replace(" ", "_")
            new_thirdimage = f'{formatted_title}_{ImageTimestamp}_thirdimage.png'
            third_file_path = f'{UPLOADS_RESOURCES}/{new_thirdimage}'
            image = Image.open(third_image)
            image.save(third_file_path, format="PNG")
        else:
            third_file_path = None

        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO resources 
                (user_id, title, description, category, front_image, second_image, third_image,
                 available_from, available_until, max_borrow_days, is_available, date_posted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session['user_id'],
                title,
                description,
                category,
                front_file_path,
                second_file_path,
                third_file_path,
                available_from,
                available_until,
                max_borrow_days,
                True,
                Datetime,
            ))
            conn.commit()
            conn.close()
            return redirect(url_for('profile'))
        except Exception as e:
            print(f"Database error: {e}")
            return render_template('add_item.html',
                                   error="Failed to save item to database. Please try again.",
                                   form_data=form_data)

        except Exception as e:
            print(f"Error in add_item: {e}")
            return render_template('add_item.html',
                                   error="An error occurred while processing your request",
                                   form_data=form_data if 'form_data' in locals() else {})


@app.route('/reset-db')
def reset_db():
    reset_resources_table()
    return "Resources table reset successfully."


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validate input
        if not username or not password:
            return render_template('login.html',
                                   error="Please fill in all fields")

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?',
                            (username,)).fetchone()
        conn.close()

        if user and user['password'] == password:  # In real app, use password hashing
            # Store user info in session
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            return redirect(url_for('home'))
        else:
            return render_template('login.html',
                                   error="Invalid username or password")

    # If GET request, just show the login form
    return render_template('login.html')


UPLOADS_PROFILES = 'static/uploads/Profiles'
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get("Name", "")
            email = request.form.get("Email", "")
            username = request.form.get("Username", "")
            password = request.form.get("Password", "")
            confirm_password = request.form['confirmPassword']
            profileimg = request.files.get("Profile_Image")
            location = request.form.get("Location", "")

            # Validate input
            if not name or not email or not username or not password or not confirm_password:
                return render_template('register.html', error="Please fill in all the required fields")

            if len(password) < 8:
                return render_template('register.html', error="Password must be at least 8 characters long!")

            if password != confirm_password:
                return render_template('register.html', error="Passwords do not match!")

            # Handle profile image
            if profileimg:
                try:
                    # Create filename using username (similar to add_item)
                    formatted_username = username.replace(" ", "_")
                    new_filename = f'{formatted_username}_{datetime.now().strftime("%Y%m%d")}_profile.png'

                    # Save path (similar to how add_item saves paths)
                    file_path = f"{UPLOADS_PROFILES}/{new_filename}"

                    print(f"Saving profile image to: {file_path}")

                    # Save image using PIL (same as add_item)
                    image = Image.open(profileimg)
                    image.save(file_path, format="PNG")

                except Exception as e:
                    print(f"Error saving profile image: {e}")
                    return render_template('register.html', error="Error uploading profile image")
            else:
                file_path = f"{UPLOADS_PROFILES}/default.png"
                image = Image.open(profileimg)
                image.save(file_path, format="PNG")

            # Connect to database
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute('''
                    INSERT INTO users (name, email, username, password, profile_image, location) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, email, username, password, file_path, location))
                conn.commit()
                print(f"User created with profile image path: {file_path}")
                return redirect(url_for('login'))

            except sqlite3.IntegrityError:
                return render_template('register.html', error="Username or email already registered")
            finally:
                conn.close()

        except Exception as e:
            print(f"Registration error: {e}")
            return render_template('register.html', error="An error occurred during registration")

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# Add this after your imports in app.py
def verify_database():
    print("Verifying database structure...")
    conn = get_db_connection()
    cur = conn.cursor()

    # Check if resources table exists and its structure
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='resources'")
    table_info = cur.fetchone()
    print(f"Resources table definition: {table_info if table_info else 'Table not found'}")

    # Add a test resource if none exist
    cur.execute('SELECT COUNT(*) FROM resources')
    count = cur.fetchone()[0]
    print(f"Number of resources in database: {count}")

    if count == 0:
        print("Adding test resource...")
        try:
            cur.execute('''
                INSERT INTO resources 
                (user_id, title, description, category, available_from,
                 available_until, max_borrow_days, date_posted, is_available)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                1,  # user_id for 'Daphne'
                'Test Garden Tool',
                'This is a test garden tool',
                'Garden Equipment',
                '2024-11-15',
                '2024-12-15',
                7,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                True
            ))
            conn.commit()
            print("Test resource added successfully")
        except Exception as e:
            print(f"Error adding test resource: {e}")

    # Display all resources
    cur.execute('SELECT * FROM resources')
    resources = cur.fetchall()
    print("\nAll resources after verification:")
    for resource in resources:
        print(resource)

    conn.close()


# Add this route to trigger the verification
@app.route('/verify-db')
def verify_db():
    verify_database()
    return "Database verified - check console output"


@app.route('/test-data')
def test_data():
    if 'user_id' not in session:
        return {"error": "Not logged in"}

    conn = get_db_connection()
    output = {}

    try:
        # Get current user info
        output["current_user"] = dict(conn.execute(
            'SELECT * FROM users WHERE user_id = ?',
            [session['user_id']]
        ).fetchone())

        # Get all users
        output["all_users"] = [dict(row) for row in conn.execute(
            'SELECT * FROM users'
        ).fetchall()]

        # Get all resources
        output["all_resources"] = [dict(row) for row in conn.execute(
            'SELECT * FROM resources'
        ).fetchall()]

        # Get resources visible to current user
        output["visible_resources"] = [dict(row) for row in conn.execute('''
            SELECT r.*, u.name as owner_name 
            FROM resources r 
            JOIN users u ON r.user_id = u.user_id 
            WHERE r.user_id != ?
        ''', [session['user_id']]).fetchall()]

    except Exception as e:
        output["error"] = str(e)
    finally:
        conn.close()

    return output

@app.route('/notifications')
def fetch_notifications():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    notifications = conn.execute(
        'SELECT * FROM notifications WHERE user_id = ? ORDER BY date_created DESC',
        (user_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(n) for n in notifications])

@app.route('/notifications/mark-read', methods=['POST'])
def mark_notifications_read():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    user_id = session['user_id']
    conn = get_db_connection()
    conn.execute(
        'UPDATE notifications SET is_read = 1 WHERE user_id = ?',
        (user_id,)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Notifications marked as read.'})

@app.route('/notifications/add', methods=['POST'])
def add_notification():
    """ Add a notification for a user (e.g., triggered by another event). """
    user_id = request.form.get('user_id')
    content = request.form.get('content')

    if not user_id or not content:
        return jsonify({'error': 'Invalid data'}), 400

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO notifications (user_id, content) VALUES (?, ?)',
        (user_id, content)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Notification added.'})

@app.route('/delete_profile', methods=['POST'])
def delete_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        # Delete the user and all their data (e.g., items, reservations)
        conn.execute('DELETE FROM users WHERE user_id = ?', (session['user_id'],))
        conn.commit()

        # Log the user out
        session.pop('user_id', None)
        flash('Profile deleted successfully.', 'success')
        return redirect(url_for('register'))
    finally:
        conn.close()

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        user = conn.execute('SELECT * FROM users WHERE user_id = ?', (session['user_id'],)).fetchone()

        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            location = request.form['location']
            profile_image = request.files.get('profile_image')

            # Save the profile image if provided
            profile_image_path = user['profile_image']
            if profile_image:
                profile_image_path = f"uploads/Profiles/{profile_image.filename}"
                profile_image.save(os.path.join('static', profile_image_path))

            # Update user details in the database
            conn.execute('''
                UPDATE users
                SET name = ?, email = ?, location = ?, profile_image = ?
                WHERE user_id = ?
            ''', (name, email, location, profile_image_path, session['user_id']))
            conn.commit()

            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))

        return render_template('edit_profile.html', user=user)
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)