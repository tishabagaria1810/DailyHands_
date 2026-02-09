from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
import sqlite3
import re
import os
import io
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dailyhands_secret_key_2024')
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = None  # No time limit for CSRF tokens

# Initialize CSRF Protection
csrf = CSRFProtect(app)

DATABASE = 'dailyhands.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least 1 uppercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least 1 number"
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        return False, "Password must contain at least 1 special character"
    return True, ""

def is_phone_unique(phone, exclude_table=None, exclude_id=None):
    """Check if phone number is unique across users, agencies, and workers tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check users table
    if exclude_table == 'users' and exclude_id:
        cursor.execute("SELECT id FROM users WHERE phone = ? AND id != ?", (phone, exclude_id))
    else:
        cursor.execute("SELECT id FROM users WHERE phone = ?", (phone,))
    if cursor.fetchone():
        conn.close()
        return False, "This phone number is already registered by a contractor"
    
    # Check agencies table
    if exclude_table == 'agencies' and exclude_id:
        cursor.execute("SELECT id FROM agencies WHERE phone = ? AND id != ?", (phone, exclude_id))
    else:
        cursor.execute("SELECT id FROM agencies WHERE phone = ?", (phone,))
    if cursor.fetchone():
        conn.close()
        return False, "This phone number is already registered by an agency"
    
    # Check workers table
    if exclude_table == 'workers' and exclude_id:
        cursor.execute("SELECT id FROM workers WHERE phone = ? AND id != ?", (phone, exclude_id))
    else:
        cursor.execute("SELECT id FROM workers WHERE phone = ?", (phone,))
    if cursor.fetchone():
        conn.close()
        return False, "This phone number is already registered by a worker"
    
    conn.close()
    return True, ""

# ============ PUBLIC ROUTES ============
@app.route('/')
def landing():
    return render_template('landing.html')

# ============ REAL-TIME VALIDATION API ============
@app.route('/api/check-availability', methods=['POST'])
def check_availability():
    field = request.form.get('field')
    value = request.form.get('value')
    role = request.form.get('role', 'contractor')
    
    if not field or not value:
        return jsonify({'available': True})
    
    conn = get_db()
    cursor = conn.cursor()
    
    if field == 'email':
        # Check in both tables
        cursor.execute("SELECT id FROM users WHERE email = ?", (value,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'available': False, 'message': 'Email already registered'})
        cursor.execute("SELECT id FROM agencies WHERE email = ?", (value,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'available': False, 'message': 'Email already registered'})
    
    elif field == 'phone':
        # Check in all three tables
        cursor.execute("SELECT id FROM users WHERE phone = ?", (value,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'available': False, 'message': 'Phone number already registered'})
        cursor.execute("SELECT id FROM agencies WHERE phone = ?", (value,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'available': False, 'message': 'Phone number already registered'})
        cursor.execute("SELECT id FROM workers WHERE phone = ?", (value,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'available': False, 'message': 'Phone number already registered'})
    
    elif field == 'name' and role == 'agency':
        # Only check agency name uniqueness
        cursor.execute("SELECT id FROM agencies WHERE LOWER(name) = LOWER(?)", (value,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'available': False, 'message': 'Agency name already in use'})
    
    conn.close()
    return jsonify({'available': True})

@app.route('/api/request-details/<int:request_id>')
def get_request_details(request_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT wr.*, u.name as contractor_name, u.phone as contractor_phone
        FROM work_requests wr 
        JOIN users u ON wr.contractor_id = u.id 
        WHERE wr.id = ? AND wr.status = 'Pending'
    """, (request_id,))
    req = cursor.fetchone()
    
    if not req:
        conn.close()
        return jsonify({'error': 'Request not found'})
    
    # Get worker types
    cursor.execute("SELECT * FROM request_worker_types WHERE request_id = ?", (request_id,))
    worker_types = cursor.fetchall()
    
    conn.close()
    
    # Convert to dict for JSON response
    request_data = dict(req)
    worker_types_list = [dict(wt) for wt in worker_types]
    
    return jsonify({
        'request': request_data,
        'worker_types': worker_types_list
    })

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        city = request.form.get('city')
        area = request.form.get('area')
        
        valid, msg = validate_password(password)
        if not valid:
            return render_template('register.html', error=msg)
        
        # Check phone uniqueness across all tables
        phone_unique, phone_msg = is_phone_unique(phone)
        if not phone_unique:
            return render_template('register.html', error=phone_msg)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check email uniqueness across both tables
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return render_template('register.html', error="Email already registered")
        
        cursor.execute("SELECT id FROM agencies WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return render_template('register.html', error="Email already registered")
        
        # Hash the password before storing
        hashed_password = generate_password_hash(password)
        
        # Check agency name uniqueness
        if role == 'agency':
            cursor.execute("SELECT id FROM agencies WHERE LOWER(name) = LOWER(?)", (name,))
            if cursor.fetchone():
                conn.close()
                return render_template('register.html', error="This agency name is already in use")
        
        if role == 'contractor':
            cursor.execute("""
                INSERT INTO users (name, email, password, phone, city, area, role)
                VALUES (?, ?, ?, ?, ?, ?, 'contractor')
            """, (name, email, hashed_password, phone, city, area))
        else:
            cursor.execute("""
                INSERT INTO agencies (name, email, password, phone, city, area)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, email, hashed_password, phone, city, area))
        
        conn.commit()
        conn.close()
        return redirect(url_for('login', registered='true'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    registered = request.args.get('registered')
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        conn = get_db()
        cursor = conn.cursor()
        
        if role == 'contractor':
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['role'] = 'contractor'
                session['name'] = user['name']
                conn.close()
                return redirect(url_for('contractor_dashboard'))
        else:
            cursor.execute("SELECT * FROM agencies WHERE email = ?", (email,))
            agency = cursor.fetchone()
            if agency and check_password_hash(agency['password'], password):
                session['user_id'] = agency['id']
                session['role'] = 'agency'
                session['name'] = agency['name']
                conn.close()
                return redirect(url_for('agency_dashboard'))
        
        conn.close()
        return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html', registered=registered)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

# ============ FORGOT PASSWORD ROUTES ============
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        phone = request.form.get('phone')
        role = request.form.get('role')
        
        conn = get_db()
        cursor = conn.cursor()
        
        if role == 'contractor':
            cursor.execute("SELECT id, name FROM users WHERE phone = ?", (phone,))
        else:
            cursor.execute("SELECT id, name FROM agencies WHERE phone = ?", (phone,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            otp = str(random.randint(100000, 999999))
            session['reset_otp'] = otp
            session['reset_user_id'] = user['id']
            session['reset_role'] = role
            session['reset_phone'] = phone
            return jsonify({'success': True, 'otp': otp, 'name': user['name']})
        else:
            return jsonify({'success': False, 'error': 'Phone number not registered'})
    
    return render_template('forgot_password.html')

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    entered_otp = request.form.get('otp')
    stored_otp = session.get('reset_otp')
    
    if entered_otp == stored_otp:
        session['otp_verified'] = True
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Invalid OTP'})

@app.route('/reset-password', methods=['POST'])
def reset_password():
    if not session.get('otp_verified'):
        return jsonify({'success': False, 'error': 'OTP not verified'})
    
    new_password = request.form.get('new_password')
    valid, msg = validate_password(new_password)
    
    if not valid:
        return jsonify({'success': False, 'error': msg})
    
    # Hash the new password
    hashed_password = generate_password_hash(new_password)
    
    conn = get_db()
    cursor = conn.cursor()
    
    role = session.get('reset_role')
    user_id = session.get('reset_user_id')
    
    if role == 'contractor':
        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
    else:
        cursor.execute("UPDATE agencies SET password = ? WHERE id = ?", (hashed_password, user_id))
    
    conn.commit()
    conn.close()
    
    # Clear reset session data
    session.pop('reset_otp', None)
    session.pop('reset_user_id', None)
    session.pop('reset_role', None)
    session.pop('reset_phone', None)
    session.pop('otp_verified', None)
    
    return jsonify({'success': True})


# ============ CONTRACTOR ROUTES ============
@app.route('/contractor/dashboard')
@login_required(role='contractor')
def contractor_dashboard():
    conn = get_db()
    cursor = conn.cursor()
    user_id = session['user_id']
    
    cursor.execute("SELECT COUNT(*) as total FROM work_requests WHERE contractor_id = ?", (user_id,))
    total_requests = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as pending FROM work_requests WHERE contractor_id = ? AND status = 'Pending'", (user_id,))
    pending = cursor.fetchone()['pending']
    
    cursor.execute("SELECT COUNT(*) as completed FROM work_requests WHERE contractor_id = ? AND status = 'Completed'", (user_id,))
    completed = cursor.fetchone()['completed']
    
    cursor.execute("SELECT COUNT(*) as active FROM work_requests WHERE contractor_id = ? AND status IN ('Accepted', 'Assigned')", (user_id,))
    active = cursor.fetchone()['active']
    
    cursor.execute("""
        SELECT wr.*, a.name as agency_name,
               (SELECT COUNT(*) FROM request_workers WHERE request_id = wr.id) as assigned_count
        FROM work_requests wr 
        LEFT JOIN agencies a ON wr.agency_id = a.id 
        WHERE wr.contractor_id = ? 
        ORDER BY wr.created_at DESC LIMIT 5
    """, (user_id,))
    recent_requests = cursor.fetchall()
    
    conn.close()
    return render_template('contractor/dashboard.html', 
                         total=total_requests, pending=pending, 
                         completed=completed, active=active,
                         recent_requests=recent_requests)

@app.route('/contractor/create-request', methods=['GET', 'POST'])
@login_required(role='contractor')
def create_request():
    conn = get_db()
    cursor = conn.cursor()
    user_id = session['user_id']
    
    cursor.execute("SELECT city FROM users WHERE id = ?", (user_id,))
    user_city = cursor.fetchone()['city']
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        expected_duration = request.form.get('expected_duration')
        start_date = request.form.get('start_date')
        
        # Get multiple worker types
        worker_types = request.form.getlist('worker_type[]')
        workers_needed_list = request.form.getlist('workers_needed[]')
        wage_per_day_list = request.form.getlist('wage_per_day[]')
        
        # Calculate totals for main request
        total_workers = sum(int(w) for w in workers_needed_list if w)
        
        # Create summary of worker types for display
        worker_type_summary = ', '.join(worker_types)
        avg_wage = sum(float(w) for w in wage_per_day_list if w) / len(wage_per_day_list) if wage_per_day_list else 0
        
        cursor.execute("""
            INSERT INTO work_requests 
            (contractor_id, title, description, worker_type, workers_needed, 
             expected_duration, wage_per_day, start_date, city, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
        """, (user_id, title, description, worker_type_summary, total_workers, 
              expected_duration, avg_wage, start_date, user_city))
        
        request_id = cursor.lastrowid
        
        # Insert individual worker type requirements
        for i in range(len(worker_types)):
            if worker_types[i] and workers_needed_list[i] and wage_per_day_list[i]:
                cursor.execute("""
                    INSERT INTO request_worker_types (request_id, worker_type, workers_needed, wage_per_day)
                    VALUES (?, ?, ?, ?)
                """, (request_id, worker_types[i], workers_needed_list[i], wage_per_day_list[i]))
        
        conn.commit()
        conn.close()
        return redirect(url_for('contractor_requests'))
    
    conn.close()
    return render_template('contractor/create_request.html', city=user_city)

@app.route('/contractor/requests')
@login_required(role='contractor')
def contractor_requests():
    conn = get_db()
    cursor = conn.cursor()
    user_id = session['user_id']
    
    cursor.execute("""
        SELECT wr.*, a.name as agency_name,
               (SELECT COUNT(*) FROM request_workers WHERE request_id = wr.id) as assigned_count
        FROM work_requests wr 
        LEFT JOIN agencies a ON wr.agency_id = a.id 
        WHERE wr.contractor_id = ? 
        ORDER BY wr.created_at DESC
    """, (user_id,))
    requests = cursor.fetchall()
    
    # Get worker types for each request
    requests_with_types = []
    for req in requests:
        cursor.execute("SELECT * FROM request_worker_types WHERE request_id = ?", (req['id'],))
        worker_types = cursor.fetchall()
        requests_with_types.append({
            'request': req,
            'worker_types': worker_types
        })
    
    conn.close()
    return render_template('contractor/requests.html', requests_with_types=requests_with_types)

@app.route('/contractor/request/<int:request_id>')
@login_required(role='contractor')
def contractor_request_detail(request_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT wr.*, a.name as agency_name, a.phone as agency_phone,
               u.name as contractor_name
        FROM work_requests wr 
        LEFT JOIN agencies a ON wr.agency_id = a.id 
        LEFT JOIN users u ON wr.contractor_id = u.id
        WHERE wr.id = ? AND wr.contractor_id = ?
    """, (request_id, session['user_id']))
    req = cursor.fetchone()
    
    if not req:
        conn.close()
        return redirect(url_for('contractor_requests'))
    
    # Get worker type requirements
    cursor.execute("SELECT * FROM request_worker_types WHERE request_id = ?", (request_id,))
    worker_types = cursor.fetchall()
    
    cursor.execute("""
        SELECT w.*, rw.id as assignment_id
        FROM request_workers rw
        JOIN workers w ON rw.worker_id = w.id
        WHERE rw.request_id = ?
    """, (request_id,))
    workers = cursor.fetchall()
    
    cursor.execute("""
        SELECT a.*, w.name as worker_name
        FROM attendance a
        JOIN workers w ON a.worker_id = w.id
        WHERE a.request_id = ?
    """, (request_id,))
    attendance = cursor.fetchall()
    
    # Calculate total payment
    cursor.execute("""
        SELECT SUM(amount) as total FROM payments WHERE request_id = ?
    """, (request_id,))
    payment_result = cursor.fetchone()
    total_payment = payment_result['total'] if payment_result and payment_result['total'] else 0
    
    conn.close()
    return render_template('contractor/request_detail.html', 
                         req=req, workers=workers, worker_types=worker_types,
                         attendance=attendance, payment={'total': total_payment})

@app.route('/contractor/complete-request/<int:request_id>', methods=['POST'])
@login_required(role='contractor')
def complete_request(request_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM work_requests WHERE id = ? AND contractor_id = ?", 
                  (request_id, session['user_id']))
    req = cursor.fetchone()
    
    if req and req['status'] == 'Assigned':
        start_date = datetime.strptime(req['start_date'], '%Y-%m-%d')
        expected_end = start_date + timedelta(days=req['expected_duration'])
        today = datetime.now()
        
        delay_days = max(0, (today - expected_end).days)
        penalty = delay_days * 100
        
        cursor.execute("""
            UPDATE work_requests 
            SET status = 'Completed', completed_at = ?, delay_days = ?, penalty_amount = ?
            WHERE id = ?
        """, (today.strftime('%Y-%m-%d %H:%M:%S'), delay_days, penalty, request_id))
        
        if penalty > 0 and req['agency_id']:
            cursor.execute("""
                UPDATE agency_earnings 
                SET penalty_earned = penalty_earned + ?
                WHERE agency_id = ? AND request_id = ?
            """, (penalty, req['agency_id'], request_id))
        
        cursor.execute("""
            UPDATE workers SET status = 'Available'
            WHERE id IN (SELECT worker_id FROM request_workers WHERE request_id = ?)
        """, (request_id,))
        
        conn.commit()
    
    conn.close()
    return redirect(url_for('contractor_request_detail', request_id=request_id))

@app.route('/contractor/rate/<int:request_id>', methods=['GET', 'POST'])
@login_required(role='contractor')
def rate_agency(request_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT wr.*, a.name as agency_name 
        FROM work_requests wr 
        JOIN agencies a ON wr.agency_id = a.id
        WHERE wr.id = ? AND wr.contractor_id = ? AND wr.status = 'Completed'
    """, (request_id, session['user_id']))
    req = cursor.fetchone()
    
    if not req:
        conn.close()
        return redirect(url_for('contractor_requests'))
    
    cursor.execute("SELECT * FROM ratings WHERE request_id = ?", (request_id,))
    existing_rating = cursor.fetchone()
    
    if request.method == 'POST' and not existing_rating:
        rating = int(request.form.get('rating'))
        review = request.form.get('review', '')
        
        cursor.execute("""
            INSERT INTO ratings (request_id, agency_id, contractor_id, rating, review)
            VALUES (?, ?, ?, ?, ?)
        """, (request_id, req['agency_id'], session['user_id'], rating, review))
        
        conn.commit()
        conn.close()
        return redirect(url_for('contractor_request_detail', request_id=request_id))
    
    conn.close()
    return render_template('contractor/rate.html', req=req, existing_rating=existing_rating)

@app.route('/contractor/profile', methods=['GET', 'POST'])
@login_required(role='contractor')
def contractor_profile():
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        city = request.form.get('city')
        area = request.form.get('area')
        
        cursor.execute("""
            UPDATE users SET name = ?, phone = ?, city = ?, area = ?
            WHERE id = ?
        """, (name, phone, city, area, session['user_id']))
        session['name'] = name
        conn.commit()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    return render_template('contractor/profile.html', user=user)


# ============ AGENCY ROUTES ============
@app.route('/agency/dashboard')
@login_required(role='agency')
def agency_dashboard():
    conn = get_db()
    cursor = conn.cursor()
    agency_id = session['user_id']
    
    cursor.execute("SELECT city FROM agencies WHERE id = ?", (agency_id,))
    agency_city = cursor.fetchone()['city']
    
    cursor.execute("""
        SELECT COUNT(*) as new FROM work_requests 
        WHERE city = ? AND status = 'Pending'
    """, (agency_city,))
    new_requests = cursor.fetchone()['new']
    
    cursor.execute("""
        SELECT COUNT(*) as active FROM work_requests 
        WHERE agency_id = ? AND status IN ('Accepted', 'Assigned')
    """, (agency_id,))
    active = cursor.fetchone()['active']
    
    cursor.execute("""
        SELECT COUNT(*) as completed FROM work_requests 
        WHERE agency_id = ? AND status = 'Completed'
    """, (agency_id,))
    completed = cursor.fetchone()['completed']
    
    cursor.execute("SELECT COUNT(*) as workers FROM workers WHERE agency_id = ?", (agency_id,))
    total_workers = cursor.fetchone()['workers']
    
    cursor.execute("""
        SELECT COALESCE(SUM(total_earned + penalty_earned), 0) as earnings 
        FROM agency_earnings WHERE agency_id = ?
    """, (agency_id,))
    total_earnings = cursor.fetchone()['earnings']
    
    cursor.execute("""
        SELECT wr.*, u.name as contractor_name 
        FROM work_requests wr 
        JOIN users u ON wr.contractor_id = u.id 
        WHERE wr.agency_id = ? 
        ORDER BY wr.created_at DESC LIMIT 5
    """, (agency_id,))
    recent_requests = cursor.fetchall()
    
    conn.close()
    return render_template('agency/dashboard.html',
                         new_requests=new_requests, active=active,
                         completed=completed, total_workers=total_workers,
                         total_earnings=total_earnings, recent_requests=recent_requests)


@app.route('/agency/new-requests')
@login_required(role='agency')
def agency_new_requests():
    conn = get_db()
    cursor = conn.cursor()
    agency_id = session['user_id']
    
    cursor.execute("SELECT city FROM agencies WHERE id = ?", (agency_id,))
    agency_city = cursor.fetchone()['city']
    
    cursor.execute("""
        SELECT wr.*, u.name as contractor_name, u.phone as contractor_phone
        FROM work_requests wr 
        JOIN users u ON wr.contractor_id = u.id 
        WHERE wr.city = ? AND wr.status = 'Pending'
        ORDER BY wr.created_at DESC
    """, (agency_city,))
    requests = cursor.fetchall()
    
    # Get worker types for each request
    requests_with_types = []
    for req in requests:
        cursor.execute("SELECT * FROM request_worker_types WHERE request_id = ?", (req['id'],))
        worker_types = cursor.fetchall()
        requests_with_types.append({
            'request': req,
            'worker_types': worker_types
        })
    
    conn.close()
    return render_template('agency/new_requests.html', requests_with_types=requests_with_types)

@app.route('/agency/accept-request/<int:request_id>', methods=['POST'])
@login_required(role='agency')
def accept_request(request_id):
    conn = get_db()
    cursor = conn.cursor()
    agency_id = session['user_id']
    
    cursor.execute("SELECT city FROM agencies WHERE id = ?", (agency_id,))
    agency_city = cursor.fetchone()['city']
    
    cursor.execute("""
        SELECT * FROM work_requests 
        WHERE id = ? AND city = ? AND status = 'Pending'
    """, (request_id, agency_city))
    req = cursor.fetchone()
    
    if req:
        cursor.execute("""
            UPDATE work_requests SET agency_id = ?, status = 'Accepted'
            WHERE id = ?
        """, (agency_id, request_id))
        
        cursor.execute("""
            INSERT INTO agency_earnings (agency_id, request_id, total_earned, penalty_earned)
            VALUES (?, ?, 0, 0)
        """, (agency_id, request_id))
        
        conn.commit()
    
    conn.close()
    return redirect(url_for('agency_my_requests'))

@app.route('/agency/my-requests')
@login_required(role='agency')
def agency_my_requests():
    conn = get_db()
    cursor = conn.cursor()
    agency_id = session['user_id']
    
    cursor.execute("""
        SELECT wr.*, u.name as contractor_name 
        FROM work_requests wr 
        JOIN users u ON wr.contractor_id = u.id 
        WHERE wr.agency_id = ?
        ORDER BY wr.created_at DESC
    """, (agency_id,))
    requests = cursor.fetchall()
    
    # Get worker types for each request
    requests_with_types = []
    for req in requests:
        cursor.execute("SELECT * FROM request_worker_types WHERE request_id = ?", (req['id'],))
        worker_types = cursor.fetchall()
        requests_with_types.append({
            'request': req,
            'worker_types': worker_types
        })
    
    conn.close()
    return render_template('agency/my_requests.html', requests_with_types=requests_with_types)

@app.route('/agency/workers')
@login_required(role='agency')
def agency_workers():
    conn = get_db()
    cursor = conn.cursor()
    agency_id = session['user_id']
    
    # Get filter and error parameters
    skill_filter = request.args.get('skill', '')
    error = request.args.get('error', '')
    
    # Get all unique skills for filter dropdown
    cursor.execute("SELECT DISTINCT skill FROM workers WHERE agency_id = ? ORDER BY skill", (agency_id,))
    skills = [row['skill'] for row in cursor.fetchall()]
    
    # Get workers with optional filter
    if skill_filter:
        cursor.execute("""
            SELECT * FROM workers 
            WHERE agency_id = ? AND skill = ?
            ORDER BY name
        """, (agency_id, skill_filter))
    else:
        cursor.execute("SELECT * FROM workers WHERE agency_id = ? ORDER BY name", (agency_id,))
    
    workers = cursor.fetchall()
    conn.close()
    return render_template('agency/workers.html', workers=workers, skills=skills, current_filter=skill_filter, error=error)

@app.route('/agency/add-worker', methods=['POST'])
@login_required(role='agency')
def add_worker():
    agency_id = session['user_id']
    
    name = request.form.get('name')
    phone = request.form.get('phone')
    skill = request.form.get('skill')
    daily_wage = request.form.get('daily_wage')
    
    # Check phone uniqueness across all tables
    phone_unique, phone_msg = is_phone_unique(phone)
    if not phone_unique:
        return redirect(url_for('agency_workers', error=phone_msg))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO workers (agency_id, name, phone, skill, daily_wage, status)
        VALUES (?, ?, ?, ?, ?, 'Available')
    """, (agency_id, name, phone, skill, daily_wage))
    
    conn.commit()
    conn.close()
    return redirect(url_for('agency_workers'))

@app.route('/agency/edit-worker/<int:worker_id>', methods=['GET', 'POST'])
@login_required(role='agency')
def edit_worker(worker_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM workers WHERE id = ? AND agency_id = ?", 
                  (worker_id, session['user_id']))
    worker = cursor.fetchone()
    
    if not worker:
        conn.close()
        return redirect(url_for('agency_workers'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        skill = request.form.get('skill')
        daily_wage = request.form.get('daily_wage')
        
        # Check phone uniqueness (exclude current worker)
        phone_unique, phone_msg = is_phone_unique(phone, exclude_table='workers', exclude_id=worker_id)
        if not phone_unique:
            conn.close()
            return redirect(url_for('agency_workers', error=phone_msg))
        
        cursor.execute("""
            UPDATE workers 
            SET name = ?, phone = ?, skill = ?, daily_wage = ?
            WHERE id = ? AND agency_id = ?
        """, (name, phone, skill, daily_wage, worker_id, session['user_id']))
        
        conn.commit()
        conn.close()
        return redirect(url_for('agency_workers'))
    
    conn.close()
    return jsonify({
        'id': worker['id'],
        'name': worker['name'],
        'phone': worker['phone'],
        'skill': worker['skill'],
        'daily_wage': worker['daily_wage'],
        'status': worker['status']
    })

@app.route('/agency/delete-worker/<int:worker_id>', methods=['POST'])
@login_required(role='agency')
def delete_worker(worker_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM workers WHERE id = ? AND agency_id = ? AND status = 'Available'", 
                  (worker_id, session['user_id']))
    if cursor.fetchone():
        cursor.execute("DELETE FROM workers WHERE id = ?", (worker_id,))
        conn.commit()
    
    conn.close()
    return redirect(url_for('agency_workers'))

@app.route('/agency/assign-workers/<int:request_id>', methods=['GET', 'POST'])
@login_required(role='agency')
def assign_workers(request_id):
    conn = get_db()
    cursor = conn.cursor()
    agency_id = session['user_id']
    
    cursor.execute("""
        SELECT * FROM work_requests 
        WHERE id = ? AND agency_id = ? AND status = 'Accepted'
    """, (request_id, agency_id))
    req = cursor.fetchone()
    
    if not req:
        conn.close()
        return redirect(url_for('agency_my_requests'))
    
    # Get worker type requirements
    cursor.execute("""
        SELECT * FROM request_worker_types WHERE request_id = ?
    """, (request_id,))
    worker_type_reqs = cursor.fetchall()
    
    # If no specific requirements in new table, use legacy single type
    if not worker_type_reqs:
        worker_type_reqs = [{
            'worker_type': req['worker_type'],
            'workers_needed': req['workers_needed'],
            'wage_per_day': req['wage_per_day']
        }]
    
    error = None
    
    if request.method == 'POST':
        all_valid = True
        all_worker_ids = []
        
        # Validate each worker type requirement
        for wt_req in worker_type_reqs:
            worker_type = wt_req['worker_type']
            workers_needed = wt_req['workers_needed']
            required_wage = wt_req['wage_per_day']
            
            # Get selected workers for this type
            field_name = f"workers_{worker_type.replace(' ', '_')}"
            worker_ids = request.form.getlist(field_name)
            
            # Validation 1: Check if correct number of workers selected
            if len(worker_ids) != workers_needed:
                error = f"You must select exactly {workers_needed} {worker_type}(s). You selected {len(worker_ids)}."
                all_valid = False
                break
            
            # Validation 2: Check if all selected workers have matching wage
            for worker_id in worker_ids:
                cursor.execute("SELECT name, daily_wage, skill FROM workers WHERE id = ?", (int(worker_id),))
                worker = cursor.fetchone()
                if worker and worker['daily_wage'] != required_wage:
                    error = f"{worker['name']}'s wage (₹{worker['daily_wage']}) doesn't match required ₹{required_wage}/day for {worker_type}"
                    all_valid = False
                    break
                all_worker_ids.append(int(worker_id))
            
            if not all_valid:
                break
        
        if all_valid:
            # All validations passed - assign workers
            for worker_id in all_worker_ids:
                cursor.execute("""
                    INSERT INTO request_workers (request_id, worker_id)
                    VALUES (?, ?)
                """, (request_id, worker_id))
                
                cursor.execute("UPDATE workers SET status = 'Busy' WHERE id = ?", (worker_id,))
            
            cursor.execute("UPDATE work_requests SET status = 'Assigned' WHERE id = ?", (request_id,))
            conn.commit()
            conn.close()
            return redirect(url_for('agency_request_detail', request_id=request_id))
    
    # Get available workers grouped by skill
    workers_by_type = {}
    for wt_req in worker_type_reqs:
        worker_type = wt_req['worker_type']
        required_wage = wt_req['wage_per_day']
        
        cursor.execute("""
            SELECT *, 
                CASE WHEN daily_wage = ? THEN 1 ELSE 0 END as is_valid
            FROM workers 
            WHERE agency_id = ? AND status = 'Available' AND LOWER(skill) = LOWER(?)
            ORDER BY is_valid DESC, name
        """, (required_wage, agency_id, worker_type))
        workers_by_type[worker_type] = {
            'workers': cursor.fetchall(),
            'needed': wt_req['workers_needed'],
            'wage': required_wage
        }
    
    conn.close()
    return render_template('agency/assign_workers.html', req=req, workers_by_type=workers_by_type, 
                          worker_type_reqs=worker_type_reqs, error=error)

@app.route('/agency/request/<int:request_id>')
@login_required(role='agency')
def agency_request_detail(request_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT wr.*, u.name as contractor_name, u.phone as contractor_phone
        FROM work_requests wr 
        JOIN users u ON wr.contractor_id = u.id 
        WHERE wr.id = ? AND wr.agency_id = ?
    """, (request_id, session['user_id']))
    req = cursor.fetchone()
    
    if not req:
        conn.close()
        return redirect(url_for('agency_my_requests'))
    
    # Get worker type requirements
    cursor.execute("SELECT * FROM request_worker_types WHERE request_id = ?", (request_id,))
    worker_types = cursor.fetchall()
    
    cursor.execute("""
        SELECT w.*, rw.id as assignment_id
        FROM request_workers rw
        JOIN workers w ON rw.worker_id = w.id
        WHERE rw.request_id = ?
    """, (request_id,))
    workers = cursor.fetchall()
    
    cursor.execute("""
        SELECT a.*, w.name as worker_name
        FROM attendance a
        JOIN workers w ON a.worker_id = w.id
        WHERE a.request_id = ?
        ORDER BY a.date DESC
    """, (request_id,))
    attendance = cursor.fetchall()
    
    cursor.execute("""
        SELECT * FROM agency_earnings WHERE request_id = ? AND agency_id = ?
    """, (request_id, session['user_id']))
    earnings = cursor.fetchone()
    
    conn.close()
    return render_template('agency/request_detail.html', 
                         req=req, workers=workers, worker_types=worker_types,
                         attendance=attendance, earnings=earnings)

@app.route('/agency/attendance/<int:request_id>', methods=['GET', 'POST'])
@login_required(role='agency')
def mark_attendance(request_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM work_requests 
        WHERE id = ? AND agency_id = ? AND status = 'Assigned'
    """, (request_id, session['user_id']))
    req = cursor.fetchone()
    
    if not req:
        conn.close()
        return redirect(url_for('agency_my_requests'))
    
    if request.method == 'POST':
        worker_id = request.form.get('worker_id')
        date = request.form.get('date')
        status = request.form.get('status')
        
        cursor.execute("""
            SELECT * FROM attendance 
            WHERE request_id = ? AND worker_id = ? AND date = ?
        """, (request_id, worker_id, date))
        
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO attendance (request_id, worker_id, date, status)
                VALUES (?, ?, ?, ?)
            """, (request_id, worker_id, date, status))
            
            if status == 'Present':
                cursor.execute("SELECT daily_wage FROM workers WHERE id = ?", (worker_id,))
                wage = cursor.fetchone()['daily_wage']
                
                cursor.execute("""
                    INSERT INTO payments (request_id, worker_id, date, amount)
                    VALUES (?, ?, ?, ?)
                """, (request_id, worker_id, date, wage))
                
                cursor.execute("""
                    UPDATE agency_earnings 
                    SET total_earned = total_earned + ?
                    WHERE request_id = ? AND agency_id = ?
                """, (wage, request_id, session['user_id']))
            
            conn.commit()
        
        conn.close()
        return redirect(url_for('agency_request_detail', request_id=request_id))
    
    cursor.execute("""
        SELECT w.* FROM request_workers rw
        JOIN workers w ON rw.worker_id = w.id
        WHERE rw.request_id = ?
    """, (request_id,))
    workers = cursor.fetchall()
    
    conn.close()
    return render_template('agency/attendance.html', req=req, workers=workers)

@app.route('/agency/earnings')
@login_required(role='agency')
def agency_earnings():
    conn = get_db()
    cursor = conn.cursor()
    agency_id = session['user_id']
    
    cursor.execute("""
        SELECT ae.*, wr.title, wr.status as request_status, wr.workers_needed,
               wr.expected_duration, wr.wage_per_day, wr.start_date
        FROM agency_earnings ae
        JOIN work_requests wr ON ae.request_id = wr.id
        WHERE ae.agency_id = ?
        ORDER BY ae.id DESC
    """, (agency_id,))
    earnings = cursor.fetchall()
    
    cursor.execute("""
        SELECT COALESCE(SUM(total_earned), 0) as total,
               COALESCE(SUM(penalty_earned), 0) as penalties
        FROM agency_earnings WHERE agency_id = ?
    """, (agency_id,))
    totals = cursor.fetchone()
    
    conn.close()
    return render_template('agency/earnings.html', earnings=earnings, totals=totals)

@app.route('/agency/earnings/<int:request_id>')
@login_required(role='agency')
def agency_request_earnings(request_id):
    conn = get_db()
    cursor = conn.cursor()
    agency_id = session['user_id']
    
    # Get request details
    cursor.execute("""
        SELECT wr.*, u.name as contractor_name, u.phone as contractor_phone
        FROM work_requests wr
        JOIN users u ON wr.contractor_id = u.id
        WHERE wr.id = ? AND wr.agency_id = ?
    """, (request_id, agency_id))
    req = cursor.fetchone()
    
    if not req:
        conn.close()
        return redirect(url_for('agency_earnings'))
    
    # Get all assigned workers with their attendance summary
    cursor.execute("""
        SELECT w.id, w.name, w.skill, w.daily_wage,
               COUNT(CASE WHEN a.status = 'Present' THEN 1 END) as days_present,
               COUNT(CASE WHEN a.status = 'Absent' THEN 1 END) as days_absent,
               COALESCE(SUM(CASE WHEN a.status = 'Present' THEN w.daily_wage ELSE 0 END), 0) as total_earned
        FROM request_workers rw
        JOIN workers w ON rw.worker_id = w.id
        LEFT JOIN attendance a ON a.worker_id = w.id AND a.request_id = rw.request_id
        WHERE rw.request_id = ?
        GROUP BY w.id, w.name, w.skill, w.daily_wage
    """, (request_id,))
    workers_summary = cursor.fetchall()
    
    # Get detailed attendance records
    cursor.execute("""
        SELECT a.date, a.status, w.name as worker_name, w.daily_wage,
               CASE WHEN a.status = 'Present' THEN w.daily_wage ELSE 0 END as earned
        FROM attendance a
        JOIN workers w ON a.worker_id = w.id
        WHERE a.request_id = ?
        ORDER BY a.date DESC, w.name
    """, (request_id,))
    attendance_records = cursor.fetchall()
    
    # Calculate totals
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) as total_paid
        FROM payments WHERE request_id = ?
    """, (request_id,))
    total_paid = cursor.fetchone()['total_paid']
    
    # Get agency earnings for this request
    cursor.execute("""
        SELECT total_earned, penalty_earned
        FROM agency_earnings
        WHERE request_id = ? AND agency_id = ?
    """, (request_id, agency_id))
    agency_earn = cursor.fetchone()
    
    # Calculate agency commission (10% of total)
    agency_commission = total_paid * 0.10
    worker_payments = total_paid - agency_commission
    
    conn.close()
    return render_template('agency/request_earnings.html',
                         req=req,
                         workers_summary=workers_summary,
                         attendance_records=attendance_records,
                         total_paid=total_paid,
                         agency_commission=agency_commission,
                         worker_payments=worker_payments,
                         agency_earn=agency_earn)

@app.route('/graph/request-earnings/<int:request_id>')
@login_required(role='agency')
def request_earnings_graph(request_id):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get worker-wise earnings
    cursor.execute("""
        SELECT w.name,
               COUNT(CASE WHEN a.status = 'Present' THEN 1 END) as days_present,
               COALESCE(SUM(CASE WHEN a.status = 'Present' THEN w.daily_wage ELSE 0 END), 0) as total_earned
        FROM request_workers rw
        JOIN workers w ON rw.worker_id = w.id
        LEFT JOIN attendance a ON a.worker_id = w.id AND a.request_id = rw.request_id
        WHERE rw.request_id = ?
        GROUP BY w.id, w.name
    """, (request_id,))
    data = cursor.fetchall()
    conn.close()
    
    if not data:
        # Return empty graph
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center', fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    else:
        names = [row['name'] for row in data]
        days = [row['days_present'] for row in data]
        earnings = [row['total_earned'] for row in data]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Days worked bar chart
        colors1 = ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899']
        ax1.bar(names, days, color=colors1[:len(names)])
        ax1.set_xlabel('Workers')
        ax1.set_ylabel('Days Present')
        ax1.set_title('Days Worked by Each Worker')
        ax1.tick_params(axis='x', rotation=45)
        
        # Earnings bar chart
        colors2 = ['#10b981', '#14b8a6', '#06b6d4', '#0ea5e9', '#3b82f6']
        ax2.bar(names, earnings, color=colors2[:len(names)])
        ax2.set_xlabel('Workers')
        ax2.set_ylabel('Earnings (₹)')
        ax2.set_title('Earnings by Each Worker')
        ax2.tick_params(axis='x', rotation=45)
        
        for i, v in enumerate(earnings):
            ax2.text(i, v + 50, f'₹{v}', ha='center', fontsize=9)
    
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=100, facecolor='white')
    img.seek(0)
    plt.close()
    
    return send_file(img, mimetype='image/png')

@app.route('/agency/profile', methods=['GET', 'POST'])
@login_required(role='agency')
def agency_profile():
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        city = request.form.get('city')
        area = request.form.get('area')
        
        cursor.execute("""
            UPDATE agencies SET name = ?, phone = ?, city = ?, area = ?
            WHERE id = ?
        """, (name, phone, city, area, session['user_id']))
        session['name'] = name
        conn.commit()
    
    cursor.execute("SELECT * FROM agencies WHERE id = ?", (session['user_id'],))
    agency = cursor.fetchone()
    
    cursor.execute("""
        SELECT AVG(rating) as avg_rating, COUNT(*) as total_ratings
        FROM ratings WHERE agency_id = ?
    """, (session['user_id'],))
    rating_info = cursor.fetchone()
    
    conn.close()
    return render_template('agency/profile.html', agency=agency, rating_info=rating_info)


# ============ API ROUTES (FETCH API) ============
@app.route('/api/agencies')
@login_required(role='contractor')
def get_agencies():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT city FROM users WHERE id = ?", (session['user_id'],))
    user_city = cursor.fetchone()['city']
    
    sort_by = request.args.get('sort', 'name')
    
    if sort_by == 'rating':
        cursor.execute("""
            SELECT a.*, COALESCE(AVG(r.rating), 0) as avg_rating, COUNT(r.id) as total_ratings
            FROM agencies a
            LEFT JOIN ratings r ON a.id = r.agency_id
            WHERE a.city = ?
            GROUP BY a.id
            ORDER BY avg_rating DESC
        """, (user_city,))
    else:
        cursor.execute("""
            SELECT a.*, COALESCE(AVG(r.rating), 0) as avg_rating, COUNT(r.id) as total_ratings
            FROM agencies a
            LEFT JOIN ratings r ON a.id = r.agency_id
            WHERE a.city = ?
            GROUP BY a.id
            ORDER BY a.name
        """, (user_city,))
    
    agencies = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(agencies)

@app.route('/api/request-status/<int:request_id>')
@login_required()
def get_request_status(request_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT wr.status, wr.created_at, a.name as agency_name,
               (SELECT COUNT(*) FROM request_workers WHERE request_id = wr.id) as workers_assigned
        FROM work_requests wr
        LEFT JOIN agencies a ON wr.agency_id = a.id
        WHERE wr.id = ?
    """, (request_id,))
    req = cursor.fetchone()
    
    if req:
        result = dict(req)
        conn.close()
        return jsonify(result)
    
    conn.close()
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/payment-preview/<int:request_id>')
@login_required(role='agency')
def payment_preview(request_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT SUM(p.amount) as total_payment, COUNT(DISTINCT a.date) as days_worked
        FROM payments p
        JOIN attendance a ON p.request_id = a.request_id AND p.worker_id = a.worker_id AND p.date = a.date
        WHERE p.request_id = ? AND a.status = 'Present'
    """, (request_id,))
    result = cursor.fetchone()
    
    conn.close()
    return jsonify({
        'total_payment': result['total_payment'] or 0,
        'days_worked': result['days_worked'] or 0
    })

# ============ CHART.JS API ENDPOINTS ============
@app.route('/api/contractor/dashboard-data')
@login_required(role='contractor')
def contractor_dashboard_data():
    """JSON endpoint for contractor requests chart"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
        FROM work_requests
        WHERE contractor_id = ?
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6
    """, (session['user_id'],))
    data = cursor.fetchall()
    conn.close()
    
    # Reverse to show oldest to newest
    data = list(reversed(data))
    
    if not data:
        return jsonify({
            'labels': ['No Data'],
            'counts': [0]
        })
    
    return jsonify({
        'labels': [row['month'] for row in data],
        'counts': [row['count'] for row in data]
    })

@app.route('/api/agency/earnings-data')
@login_required(role='agency')
def agency_earnings_data():
    """JSON endpoint for agency earnings chart"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT strftime('%Y-%m', wr.created_at) as month, 
               SUM(ae.total_earned) as earned,
               SUM(ae.penalty_earned) as penalty
        FROM agency_earnings ae
        JOIN work_requests wr ON ae.request_id = wr.id
        WHERE ae.agency_id = ?
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6
    """, (session['user_id'],))
    data = cursor.fetchall()
    conn.close()
    
    # Reverse to show oldest to newest
    data = list(reversed(data))
    
    if not data:
        return jsonify({
            'labels': ['No Data'],
            'earned': [0],
            'penalty': [0]
        })
    
    return jsonify({
        'labels': [row['month'] for row in data],
        'earned': [row['earned'] or 0 for row in data],
        'penalty': [row['penalty'] or 0 for row in data]
    })

@app.route('/api/request/<int:request_id>/worker-earnings')
@login_required(role='agency')
def request_worker_earnings_data(request_id):
    """JSON endpoint for worker earnings breakdown"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify agency owns this request
    cursor.execute("""
        SELECT id FROM work_requests 
        WHERE id = ? AND agency_id = ?
    """, (request_id, session['user_id']))
    
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get worker earnings
    cursor.execute("""
        SELECT w.name,
               COALESCE(SUM(CASE WHEN a.status = 'Present' THEN w.daily_wage ELSE 0 END), 0) as total_earned
        FROM request_workers rw
        JOIN workers w ON rw.worker_id = w.id
        LEFT JOIN attendance a ON a.worker_id = w.id AND a.request_id = rw.request_id
        WHERE rw.request_id = ?
        GROUP BY w.id, w.name
    """, (request_id,))
    data = cursor.fetchall()
    conn.close()
    
    if not data:
        return jsonify({
            'names': ['No Data'],
            'earnings': [0]
        })
    
    return jsonify({
        'names': [row['name'] for row in data],
        'earnings': [row['total_earned'] for row in data]
    })

@app.route('/api/request/<int:request_id>/worker-days')
@login_required(role='agency')
def request_worker_days_data(request_id):
    """JSON endpoint for worker days worked"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify agency owns this request
    cursor.execute("""
        SELECT id FROM work_requests 
        WHERE id = ? AND agency_id = ?
    """, (request_id, session['user_id']))
    
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get worker days
    cursor.execute("""
        SELECT w.name,
               COUNT(CASE WHEN a.status = 'Present' THEN 1 END) as days_present
        FROM request_workers rw
        JOIN workers w ON rw.worker_id = w.id
        LEFT JOIN attendance a ON a.worker_id = w.id AND a.request_id = rw.request_id
        WHERE rw.request_id = ?
        GROUP BY w.id, w.name
    """, (request_id,))
    data = cursor.fetchall()
    conn.close()
    
    if not data:
        return jsonify({
            'names': ['No Data'],
            'days': [0]
        })
    
    return jsonify({
        'names': [row['name'] for row in data],
        'days': [row['days_present'] for row in data]
    })

# ============ GRAPH ROUTES ============
@app.route('/graph/contractor-requests')
@login_required(role='contractor')
def contractor_requests_graph():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
        FROM work_requests
        WHERE contractor_id = ?
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6
    """, (session['user_id'],))
    data = cursor.fetchall()
    conn.close()
    
    months = [row['month'] for row in reversed(data)] or ['No Data']
    counts = [row['count'] for row in reversed(data)] or [0]
    
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(months, counts, color='#6366f1')
    ax.set_xlabel('Month')
    ax.set_ylabel('Requests')
    ax.set_title('Requests Over Time')
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=100, facecolor='white')
    img.seek(0)
    plt.close()
    
    return send_file(img, mimetype='image/png')

@app.route('/graph/agency-earnings')
@login_required(role='agency')
def agency_earnings_graph():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT strftime('%Y-%m', wr.created_at) as month, 
               SUM(ae.total_earned) as earned,
               SUM(ae.penalty_earned) as penalty
        FROM agency_earnings ae
        JOIN work_requests wr ON ae.request_id = wr.id
        WHERE ae.agency_id = ?
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6
    """, (session['user_id'],))
    data = cursor.fetchall()
    conn.close()
    
    months = [row['month'] for row in reversed(data)] or ['No Data']
    earned = [row['earned'] or 0 for row in reversed(data)] or [0]
    penalty = [row['penalty'] or 0 for row in reversed(data)] or [0]
    
    fig, ax = plt.subplots(figsize=(8, 4))
    x = range(len(months))
    width = 0.35
    ax.bar([i - width/2 for i in x], earned, width, label='Earned', color='#10b981')
    ax.bar([i + width/2 for i in x], penalty, width, label='Penalty Bonus', color='#f59e0b')
    ax.set_xlabel('Month')
    ax.set_ylabel('Amount (₹)')
    ax.set_title('Earnings Overview')
    ax.set_xticks(x)
    ax.set_xticklabels(months)
    ax.legend()
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=100, facecolor='white')
    img.seek(0)
    plt.close()
    
    return send_file(img, mimetype='image/png')


# ============ DATABASE INITIALIZATION ============
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            city TEXT NOT NULL,
            area TEXT,
            role TEXT DEFAULT 'contractor',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS agencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            city TEXT NOT NULL,
            area TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agency_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            skill TEXT NOT NULL,
            daily_wage REAL NOT NULL,
            status TEXT DEFAULT 'Available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agency_id) REFERENCES agencies(id)
        );
        
        CREATE TABLE IF NOT EXISTS work_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contractor_id INTEGER NOT NULL,
            agency_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            worker_type TEXT NOT NULL,
            workers_needed INTEGER NOT NULL,
            expected_duration INTEGER NOT NULL,
            wage_per_day REAL NOT NULL,
            start_date DATE NOT NULL,
            city TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            delay_days INTEGER DEFAULT 0,
            penalty_amount REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (contractor_id) REFERENCES users(id),
            FOREIGN KEY (agency_id) REFERENCES agencies(id)
        );
        
        CREATE TABLE IF NOT EXISTS request_workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            worker_id INTEGER NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES work_requests(id),
            FOREIGN KEY (worker_id) REFERENCES workers(id)
        );
        
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            worker_id INTEGER NOT NULL,
            date DATE NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (request_id) REFERENCES work_requests(id),
            FOREIGN KEY (worker_id) REFERENCES workers(id)
        );
        
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            worker_id INTEGER NOT NULL,
            date DATE NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (request_id) REFERENCES work_requests(id),
            FOREIGN KEY (worker_id) REFERENCES workers(id)
        );
        
        CREATE TABLE IF NOT EXISTS agency_earnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agency_id INTEGER NOT NULL,
            request_id INTEGER NOT NULL,
            total_earned REAL DEFAULT 0,
            penalty_earned REAL DEFAULT 0,
            FOREIGN KEY (agency_id) REFERENCES agencies(id),
            FOREIGN KEY (request_id) REFERENCES work_requests(id)
        );
        
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            agency_id INTEGER NOT NULL,
            contractor_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            review TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES work_requests(id),
            FOREIGN KEY (agency_id) REFERENCES agencies(id),
            FOREIGN KEY (contractor_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS request_worker_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            worker_type TEXT NOT NULL,
            workers_needed INTEGER NOT NULL,
            wage_per_day REAL NOT NULL,
            FOREIGN KEY (request_id) REFERENCES work_requests(id)
        );
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("  DailyHands Server Starting...")
    print("=" * 50)
    print("  Open: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True)
