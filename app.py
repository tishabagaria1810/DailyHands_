from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash
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
import threading

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dailyhands_secret_key_2024')
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = None  # No time limit for CSRF tokens

# Initialize CSRF Protection
csrf = CSRFProtect(app)

# Global error handler
@app.errorhandler(500)
def internal_error(error):
    import traceback
    error_trace = traceback.format_exc()
    print("="*60)
    print("INTERNAL SERVER ERROR:")
    print(error_trace)
    print("="*60)
    return f"<h1>Internal Server Error</h1><pre>{error_trace}</pre>", 500

DATABASE = 'dailyhands.db'

# OTP will be printed to console only (no SMS/Email)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Simple shift cipher encryption (shift by 3)
def encrypt_password(password):
    encrypted = ''
    for char in password:
        if char.isalpha():
            # Shift letters by 3
            if char.isupper():
                encrypted += chr((ord(char) - ord('A') + 3) % 26 + ord('A'))
            else:
                encrypted += chr((ord(char) - ord('a') + 3) % 26 + ord('a'))
        elif char.isdigit():
            # Shift digits by 3
            encrypted += str((int(char) + 3) % 10)
        else:
            # Keep special characters unchanged
            encrypted += char
    return encrypted

def decrypt_password(encrypted_password):
    decrypted = ''
    for char in encrypted_password:
        if char.isalpha():
            # Shift letters back by 3
            if char.isupper():
                decrypted += chr((ord(char) - ord('A') - 3) % 26 + ord('A'))
            else:
                decrypted += chr((ord(char) - ord('a') - 3) % 26 + ord('a'))
        elif char.isdigit():
            # Shift digits back by 3
            decrypted += str((int(char) - 3) % 10)
        else:
            # Keep special characters unchanged
            decrypted += char
    return decrypted

# Send SMS OTP (prints to console only)
def send_sms_otp(phone, otp):
    print(f"\n{'='*60}")
    print(f"📱 SMS OTP for {phone}: {otp}")
    print(f"{'='*60}\n")
    return True

# Send email (prints to console only)
def send_email(to_email, subject, body):
    print(f"\n{'='*60}")
    print(f"📧 Email to {to_email}")
    print(f"Subject: {subject}")
    print(f"{'='*60}\n")
    return True

# Background task to check and update request statuses
def check_request_statuses():
    try:
        conn = get_db()
        cursor = conn.cursor()
        today = datetime.now().date()
        
        # Auto-cancel unaccepted requests on or after start date
        cursor.execute("""
            UPDATE work_requests 
            SET status = 'Cancelled'
            WHERE status = 'Pending' 
            AND date(start_date) <= date(?)
        """, (today,))
        
        # Auto-reject accepted but unassigned requests at start date
        cursor.execute("""
            UPDATE work_requests 
            SET status = 'Rejected'
            WHERE status = 'Accepted' 
            AND date(start_date) <= date(?)
        """, (today,))
        
        # Auto-complete requests and release workers when duration ends
        cursor.execute("""
            SELECT id, start_date, expected_duration, agency_id
            FROM work_requests 
            WHERE status = 'Assigned'
        """)
        assigned_requests = cursor.fetchall()
        
        for req in assigned_requests:
            start_date = datetime.strptime(req['start_date'], '%Y-%m-%d').date()
            end_date = start_date + timedelta(days=req['expected_duration'])
            
            if today > end_date:
                # Calculate due date and late penalty
                due_date = end_date + timedelta(days=7)  # 7 days to pay
                late_days = max(0, (today - due_date).days)
                late_penalty = late_days * 100
                
                # Update request status
                cursor.execute("""
                    UPDATE work_requests 
                    SET status = 'Completed_Payment_Pending', 
                        completed_at = ?,
                        due_date = ?,
                        delay_days = ?,
                        penalty_amount = ?
                    WHERE id = ?
                """, (today.strftime('%Y-%m-%d'), due_date.strftime('%Y-%m-%d'), 
                      late_days, late_penalty, req['id']))
                
                # Release all assigned workers
                cursor.execute("""
                    UPDATE workers SET status = 'Available'
                    WHERE id IN (SELECT worker_id FROM request_workers WHERE request_id = ?)
                """, (req['id'],))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Background check error: {e}")

# Run background checks periodically
def run_background_checks():
    check_request_statuses()
    # Schedule next check in 1 hour
    threading.Timer(3600, run_background_checks).start()

# Start background checks (commented out to avoid threading issues in debug mode)
# threading.Timer(10, run_background_checks).start()

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                return redirect(url_for('login'))
            
            # Check OTP verification
            if not session.get('otp_verified'):
                return redirect(url_for('verify_login_otp'))
            
            # Execute the protected route
            response = f(*args, **kwargs)
            
            # Add cache prevention headers to prevent back-button access
            # Handle different response types
            if isinstance(response, tuple):
                # If it's a tuple (body, status_code), convert to response object
                response = app.make_response(response)
            elif isinstance(response, str):
                response = app.make_response(response)
            
            # Only add headers if response has headers attribute
            if hasattr(response, 'headers'):
                response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
            
            return response
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

# ============ PREVIEW ROUTE (UI KIT INTEGRATION - PHASE 1) ============
# This route is completely isolated and does NOT affect production code
# NO authentication, NO database, NO session - pure static preview only
@app.route('/preview/dashboard')
def preview_dashboard():
    """
    Static UI preview for third-party dashboard integration.
    This is a DESIGN REFERENCE ONLY - no backend logic connected.
    Safe to access without login for visual inspection.
    """
    return render_template('preview_dashboard.html')

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
        email = request.form.get('email').lower()  # Convert to lowercase
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
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return render_template('register.html', error="Email already registered")
        
        cursor.execute("SELECT id FROM agencies WHERE LOWER(email) = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return render_template('register.html', error="Email already registered")
        
        # Encrypt password using shift cipher
        encrypted_password = encrypt_password(password)
        
        # Check agency name uniqueness
        if role == 'agency':
            cursor.execute("SELECT id FROM agencies WHERE LOWER(name) = LOWER(?)", (name,))
            if cursor.fetchone():
                conn.close()
                return render_template('register.html', error="This agency name is already in use")
            
            # Get commission per worker
            commission_per_worker = request.form.get('commission_per_worker', 0)
            try:
                commission_per_worker = float(commission_per_worker)
            except:
                commission_per_worker = 0
            
            cursor.execute("""
                INSERT INTO agencies (name, email, password, phone, city, area, commission_per_worker)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, email, encrypted_password, phone, city, area, commission_per_worker))
        else:
            cursor.execute("""
                INSERT INTO users (name, email, password, phone, city, area, role)
                VALUES (?, ?, ?, ?, ?, ?, 'contractor')
            """, (name, email, encrypted_password, phone, city, area))
        
        conn.commit()
        conn.close()
        return redirect(url_for('login', registered='true'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    registered = request.args.get('registered')
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role')
            
            if not email or not password or not role:
                return render_template('login.html', error="Please fill in all fields")
            
            email = email.lower()  # Convert to lowercase
            
            conn = get_db()
            cursor = conn.cursor()
            
            if role == 'contractor':
                cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
                user = cursor.fetchone()
                if user:
                    # Decrypt stored password and compare
                    decrypted_password = decrypt_password(user['password'])
                    if decrypted_password == password:
                        # Generate OTP
                        otp = str(random.randint(100000, 999999))
                        otp_expiry = datetime.now() + timedelta(minutes=5)
                        
                        # Store OTP in database
                        cursor.execute("""
                            UPDATE users 
                            SET otp_code = ?, otp_expiry = ?, otp_verified = 0
                            WHERE id = ?
                        """, (otp, otp_expiry.strftime('%Y-%m-%d %H:%M:%S'), user['id']))
                        conn.commit()
                        
                        # Send OTP via SMS
                        send_sms_otp(user['phone'], otp)
                        
                        # Store user info in session temporarily
                        session['temp_user_id'] = user['id']
                        session['temp_role'] = 'contractor'
                        session['temp_name'] = user['name']
                        session['temp_phone'] = user['phone']
                        session['otp_attempts'] = 0
                        session['debug_otp'] = otp  # For debugging in browser console
                        
                        conn.close()
                        return redirect(url_for('verify_login_otp'))
            else:
                cursor.execute("SELECT * FROM agencies WHERE LOWER(email) = ?", (email,))
                agency = cursor.fetchone()
                if agency:
                    # Decrypt stored password and compare
                    decrypted_password = decrypt_password(agency['password'])
                    if decrypted_password == password:
                        # Generate OTP
                        otp = str(random.randint(100000, 999999))
                        otp_expiry = datetime.now() + timedelta(minutes=5)
                        
                        # Store OTP in database
                        cursor.execute("""
                            UPDATE agencies 
                            SET otp_code = ?, otp_expiry = ?, otp_verified = 0
                            WHERE id = ?
                        """, (otp, otp_expiry.strftime('%Y-%m-%d %H:%M:%S'), agency['id']))
                        conn.commit()
                        
                        # Send OTP via SMS
                        send_sms_otp(agency['phone'], otp)
                        
                        # Store user info in session temporarily
                        session['temp_user_id'] = agency['id']
                        session['temp_role'] = 'agency'
                        session['temp_name'] = agency['name']
                        session['temp_phone'] = agency['phone']
                        session['otp_attempts'] = 0
                        session['debug_otp'] = otp  # For debugging in browser console
                        
                        conn.close()
                        return redirect(url_for('verify_login_otp'))
            
            conn.close()
            return render_template('login.html', error="Invalid credentials")
        except Exception as e:
            print(f"ERROR in login: {str(e)}")
            import traceback
            traceback.print_exc()
            return render_template('login.html', error="An error occurred during login. Please try again.")
    
    return render_template('login.html', registered=registered)

@app.route('/logout')
def logout():
    session.clear()
    response = redirect(url_for('login'))
    # Add cache prevention headers to logout response
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/verify-login-otp', methods=['GET', 'POST'])
def verify_login_otp():
    if 'temp_user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        
        # Check retry limit
        if session.get('otp_attempts', 0) >= 3:
            session.clear()
            return render_template('verify_otp.html', error="Too many failed attempts. Please login again.", 
                                 phone=session.get('temp_phone', ''))
        
        conn = get_db()
        cursor = conn.cursor()
        
        role = session.get('temp_role')
        user_id = session.get('temp_user_id')
        
        if role == 'contractor':
            cursor.execute("SELECT otp_code, otp_expiry FROM users WHERE id = ?", (user_id,))
        else:
            cursor.execute("SELECT otp_code, otp_expiry FROM agencies WHERE id = ?", (user_id,))
        
        user = cursor.fetchone()
        
        if user:
            # Check if OTP expired
            otp_expiry = datetime.strptime(user['otp_expiry'], '%Y-%m-%d %H:%M:%S')
            if datetime.now() > otp_expiry:
                conn.close()
                session.clear()
                return render_template('verify_otp.html', error="OTP expired. Please login again.",
                                     phone=session.get('temp_phone', ''))
            
            # Verify OTP
            if user['otp_code'] == entered_otp:
                # Mark OTP as verified
                if role == 'contractor':
                    cursor.execute("UPDATE users SET otp_verified = 1 WHERE id = ?", (user_id,))
                else:
                    cursor.execute("UPDATE agencies SET otp_verified = 1 WHERE id = ?", (user_id,))
                conn.commit()
                conn.close()
                
                # Set session variables
                session['user_id'] = session.pop('temp_user_id')
                session['role'] = session.pop('temp_role')
                session['name'] = session.pop('temp_name')
                session['otp_verified'] = True
                session.pop('temp_phone', None)
                session.pop('otp_attempts', None)
                session.pop('debug_otp', None)  # Clear debug OTP after verification
                
                # Redirect to dashboard
                if role == 'contractor':
                    return redirect(url_for('contractor_dashboard'))
                else:
                    return redirect(url_for('agency_dashboard'))
            else:
                session['otp_attempts'] = session.get('otp_attempts', 0) + 1
                conn.close()
                return render_template('verify_otp.html', error="Invalid OTP. Please try again.",
                                     phone=session.get('temp_phone', ''),
                                     attempts_left=3 - session.get('otp_attempts', 0))
        
        conn.close()
        return render_template('verify_otp.html', error="Invalid session. Please login again.",
                             phone=session.get('temp_phone', ''))
    
    return render_template('verify_otp.html', phone=session.get('temp_phone', ''))

# ============ FORGOT PASSWORD ROUTES ============
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = request.form.get('identifier')  # email or phone
        role = request.form.get('role')
        delivery_method = request.form.get('delivery_method')  # 'email' or 'phone'
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if identifier is email or phone
        is_email = '@' in identifier
        
        if role == 'contractor':
            if is_email:
                cursor.execute("SELECT id, name, email, phone FROM users WHERE LOWER(email) = ?", (identifier.lower(),))
            else:
                cursor.execute("SELECT id, name, email, phone FROM users WHERE phone = ?", (identifier,))
        else:
            if is_email:
                cursor.execute("SELECT id, name, email, phone FROM agencies WHERE LOWER(email) = ?", (identifier.lower(),))
            else:
                cursor.execute("SELECT id, name, email, phone FROM agencies WHERE phone = ?", (identifier,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            otp = str(random.randint(100000, 999999))
            otp_expiry = datetime.now() + timedelta(minutes=5)
            
            session['reset_otp'] = otp
            session['reset_otp_expiry'] = otp_expiry.strftime('%Y-%m-%d %H:%M:%S')
            session['reset_user_id'] = user['id']
            session['reset_role'] = role
            session['reset_attempts'] = 0
            session['debug_otp'] = otp  # For debugging in browser console
            
            # Send OTP based on delivery method
            if delivery_method == 'email':
                subject = "DailyHands Password Reset OTP"
                body = f"""
                <html>
                <body>
                    <h2>Password Reset Request</h2>
                    <p>Hello {user['name']},</p>
                    <p>Your OTP for password reset is: <strong>{otp}</strong></p>
                    <p>This OTP is valid for 5 minutes.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                </body>
                </html>
                """
                send_email(user['email'], subject, body)
                return jsonify({'success': True, 'message': 'OTP sent to your email', 'name': user['name'], 'debug_otp': otp})
            else:
                send_sms_otp(user['phone'], otp)
                return jsonify({'success': True, 'message': 'OTP sent to your phone', 'name': user['name'], 'debug_otp': otp})
        else:
            return jsonify({'success': False, 'error': 'Email/Phone not registered'})
    
    return render_template('forgot_password.html')

@app.route('/verify-reset-otp', methods=['POST'])
def verify_reset_otp():
    entered_otp = request.form.get('otp')
    stored_otp = session.get('reset_otp')
    otp_expiry_str = session.get('reset_otp_expiry')
    
    # Check retry limit
    if session.get('reset_attempts', 0) >= 3:
        session.pop('reset_otp', None)
        session.pop('reset_otp_expiry', None)
        session.pop('reset_user_id', None)
        session.pop('reset_role', None)
        session.pop('reset_attempts', None)
        return jsonify({'success': False, 'error': 'Too many failed attempts. Please start over.'})
    
    # Check if OTP expired
    if otp_expiry_str:
        otp_expiry = datetime.strptime(otp_expiry_str, '%Y-%m-%d %H:%M:%S')
        if datetime.now() > otp_expiry:
            session.clear()
            return jsonify({'success': False, 'error': 'OTP expired. Please request a new one.'})
    
    if entered_otp == stored_otp:
        session['otp_verified'] = True
        session.pop('reset_attempts', None)
        return jsonify({'success': True})
    else:
        session['reset_attempts'] = session.get('reset_attempts', 0) + 1
        attempts_left = 3 - session.get('reset_attempts', 0)
        return jsonify({'success': False, 'error': f'Invalid OTP. {attempts_left} attempts left.'})

@app.route('/reset-password', methods=['POST'])
def reset_password():
    if not session.get('otp_verified'):
        return jsonify({'success': False, 'error': 'OTP not verified'})
    
    new_password = request.form.get('new_password')
    valid, msg = validate_password(new_password)
    
    if not valid:
        return jsonify({'success': False, 'error': msg})
    
    # Encrypt the new password using shift cipher
    encrypted_password = encrypt_password(new_password)
    
    conn = get_db()
    cursor = conn.cursor()
    
    role = session.get('reset_role')
    user_id = session.get('reset_user_id')
    
    if role == 'contractor':
        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (encrypted_password, user_id))
    else:
        cursor.execute("UPDATE agencies SET password = ? WHERE id = ?", (encrypted_password, user_id))
    
    conn.commit()
    conn.close()
    
    # Clear reset session data
    session.pop('reset_otp', None)
    session.pop('reset_otp_expiry', None)
    session.pop('reset_user_id', None)
    session.pop('reset_role', None)
    session.pop('otp_verified', None)
    session.pop('reset_attempts', None)
    session.pop('debug_otp', None)  # Clear debug OTP after password reset
    
    return jsonify({'success': True})


# ============ CONTRACTOR ROUTES ============
@app.route('/contractor/dashboard')
@login_required(role='contractor')
def contractor_dashboard():
    # Check and update request statuses
    check_request_statuses()
    
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
        start_date = datetime.strptime(req['start_date'], '%Y-%m-%d').date()
        today = datetime.now().date()
        
        # Check if today is before start date
        if today < start_date:
            conn.close()
            flash('Cannot mark project as completed before the start date', 'error')
            return redirect(url_for('contractor_request_detail', request_id=request_id))
        
        # Calculate actual days worked from attendance records
        cursor.execute("""
            SELECT COUNT(DISTINCT date) as days_worked
            FROM attendance
            WHERE request_id = ? AND status = 'Present'
        """, (request_id,))
        attendance_result = cursor.fetchone()
        days_worked = attendance_result['days_worked'] if attendance_result else 0
        
        # If no attendance records, use days from start date to today
        if days_worked == 0:
            days_worked = (today - start_date).days + 1
        
        # Calculate expected end date based on duration
        expected_end = start_date + timedelta(days=req['expected_duration'])
        
        # Calculate due date (7 days after expected end)
        due_date = expected_end + timedelta(days=7)
        
        # Calculate penalty if completed late
        delay_days = max(0, (today - expected_end).days)
        penalty = delay_days * 100
        
        # Update request status to Completed_Payment_Pending
        cursor.execute("""
            UPDATE work_requests 
            SET status = 'Completed_Payment_Pending', 
                completed_at = ?, 
                delay_days = ?, 
                penalty_amount = ?,
                due_date = ?
            WHERE id = ?
        """, (today.strftime('%Y-%m-%d %H:%M:%S'), delay_days, penalty, 
              due_date.strftime('%Y-%m-%d'), request_id))
        
        # Release all assigned workers
        cursor.execute("""
            UPDATE workers SET status = 'Available'
            WHERE id IN (SELECT worker_id FROM request_workers WHERE request_id = ?)
        """, (request_id,))
        
        conn.commit()
        flash('Project marked as completed successfully', 'success')
    
    conn.close()
    return redirect(url_for('contractor_request_detail', request_id=request_id))

@app.route('/contractor/cancel-request/<int:request_id>', methods=['POST'])
@login_required(role='contractor')
def contractor_cancel_request(request_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM work_requests WHERE id = ? AND contractor_id = ?", 
                  (request_id, session['user_id']))
    req = cursor.fetchone()
    
    if req and req['status'] in ['Pending', 'Accepted']:
        # Check if before start date
        start_date = datetime.strptime(req['start_date'], '%Y-%m-%d').date()
        today = datetime.now().date()
        
        if today < start_date:
            cursor.execute("UPDATE work_requests SET status = 'Cancelled' WHERE id = ?", (request_id,))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Request cancelled successfully'})
        else:
            conn.close()
            return jsonify({'success': False, 'error': 'Cannot cancel request after start date'})
    
    conn.close()
    return jsonify({'success': False, 'error': 'Request cannot be cancelled'})

@app.route('/contractor/payment/<int:request_id>', methods=['GET', 'POST'])
@login_required(role='contractor')
def contractor_payment(request_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT wr.*, a.name as agency_name, a.commission_per_worker
        FROM work_requests wr
        JOIN agencies a ON wr.agency_id = a.id
        WHERE wr.id = ? AND wr.contractor_id = ? AND wr.status = 'Completed_Payment_Pending'
    """, (request_id, session['user_id']))
    req = cursor.fetchone()
    
    if not req:
        conn.close()
        return redirect(url_for('contractor_requests'))
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')  # 'upi' or 'card'
        payment_details = request.form.get('payment_details')  # UPI ID or Card Number
        
        # Simple format validation (mock)
        if payment_method == 'upi':
            if not re.match(r'^[\w.-]+@[\w.-]+$', payment_details):
                # Calculate values for error display
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0) as worker_wages
                    FROM payments WHERE request_id = ?
                """, (request_id,))
                worker_wages = cursor.fetchone()['worker_wages']
                commission = req['workers_needed'] * req['commission_per_worker']
                start_date = datetime.strptime(req['start_date'], '%Y-%m-%d').date()
                end_date = start_date + timedelta(days=req['expected_duration'])
                due_date = end_date + timedelta(days=7)
                today = datetime.now().date()
                late_days = max(0, (today - due_date).days)
                late_penalty = late_days * 100
                total_amount = worker_wages + commission + late_penalty
                conn.close()
                return render_template('contractor/payment.html', req=req, 
                                     worker_wages=worker_wages, commission=commission,
                                     late_penalty=late_penalty, total_amount=total_amount,
                                     error='Invalid UPI ID format')
        elif payment_method == 'card':
            card_clean = payment_details.replace(' ', '').replace('-', '')
            if not re.match(r'^\d{16}$', card_clean):
                # Calculate values for error display
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0) as worker_wages
                    FROM payments WHERE request_id = ?
                """, (request_id,))
                worker_wages = cursor.fetchone()['worker_wages']
                commission = req['workers_needed'] * req['commission_per_worker']
                start_date = datetime.strptime(req['start_date'], '%Y-%m-%d').date()
                end_date = start_date + timedelta(days=req['expected_duration'])
                due_date = end_date + timedelta(days=7)
                today = datetime.now().date()
                late_days = max(0, (today - due_date).days)
                late_penalty = late_days * 100
                total_amount = worker_wages + commission + late_penalty
                conn.close()
                return render_template('contractor/payment.html', req=req,
                                     worker_wages=worker_wages, commission=commission,
                                     late_penalty=late_penalty, total_amount=total_amount,
                                     error='Invalid card number format')
        
        # Calculate total payment with DYNAMIC penalty
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as worker_wages
            FROM payments WHERE request_id = ?
        """, (request_id,))
        worker_wages = cursor.fetchone()['worker_wages']
        
        # Add agency commission
        commission = req['workers_needed'] * req['commission_per_worker']
        
        # Calculate late penalty dynamically
        start_date = datetime.strptime(req['start_date'], '%Y-%m-%d').date()
        end_date = start_date + timedelta(days=req['expected_duration'])
        due_date = end_date + timedelta(days=7)
        today = datetime.now().date()
        
        late_days = max(0, (today - due_date).days)
        late_penalty = late_days * 100
        
        total_amount = worker_wages + commission + late_penalty
        
        # Update request status
        cursor.execute("""
            UPDATE work_requests 
            SET status = 'Completed_Paid', payment_status = 'Paid'
            WHERE id = ?
        """, (request_id,))
        
        # Store payment details
        cursor.execute("""
            INSERT INTO payments (request_id, worker_id, date, amount, payment_method, payment_details)
            VALUES (?, 0, ?, ?, ?, ?)
        """, (request_id, datetime.now().strftime('%Y-%m-%d'), total_amount, payment_method, payment_details))
        
        # Update or create agency_earnings record
        cursor.execute("""
            SELECT id FROM agency_earnings WHERE request_id = ? AND agency_id = ?
        """, (request_id, req['agency_id']))
        existing_earning = cursor.fetchone()
        
        if existing_earning:
            # Update existing record
            cursor.execute("""
                UPDATE agency_earnings 
                SET total_earned = ?, penalty_earned = ?
                WHERE request_id = ? AND agency_id = ?
            """, (commission, late_penalty, request_id, req['agency_id']))
        else:
            # Create new record
            cursor.execute("""
                INSERT INTO agency_earnings (agency_id, request_id, total_earned, penalty_earned)
                VALUES (?, ?, ?, ?)
            """, (req['agency_id'], request_id, commission, late_penalty))
        
        conn.commit()
        
        # Send email to agency with payment confirmation
        try:
            cursor.execute("SELECT email FROM agencies WHERE id = ?", (req['agency_id'],))
            agency_email = cursor.fetchone()['email']
            
            cursor.execute("""
                SELECT COUNT(CASE WHEN status = 'Present' THEN 1 END) as present_count,
                       COUNT(CASE WHEN status = 'Absent' THEN 1 END) as absent_count
                FROM attendance WHERE request_id = ?
            """, (request_id,))
            attendance_summary = cursor.fetchone()
            
            subject = f"Payment Received - {req['title']}"
            body = f"""
            <html>
            <body>
                <h2>Payment Received</h2>
                <p>Hello {req['agency_name']},</p>
                <p>Payment has been received for the request: <strong>{req['title']}</strong></p>
                <hr>
                <p><strong>Workers Present:</strong> {attendance_summary['present_count']}</p>
                <p><strong>Workers Absent:</strong> {attendance_summary['absent_count']}</p>
                <p><strong>Worker Wages:</strong> ₹{worker_wages}</p>
                <p><strong>Agency Commission:</strong> ₹{commission}</p>
                <p><strong>Late Penalty:</strong> ₹{late_penalty}</p>
                <p><strong>Total Amount Paid:</strong> ₹{total_amount}</p>
                <hr>
                <p>Thank you for your service!</p>
            </body>
            </html>
            """
            send_email(agency_email, subject, body)
        except Exception as e:
            print(f"Email notification error: {e}")
        
        conn.close()
        flash('Payment successful! Your payment has been processed.', 'success')
        return redirect(url_for('contractor_request_detail', request_id=request_id))
    
    # Calculate payment preview with DYNAMIC penalty calculation
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) as worker_wages
        FROM payments WHERE request_id = ?
    """, (request_id,))
    worker_wages = cursor.fetchone()['worker_wages']
    
    commission = req['workers_needed'] * req['commission_per_worker']
    
    # Calculate late penalty dynamically based on current date
    start_date = datetime.strptime(req['start_date'], '%Y-%m-%d').date()
    end_date = start_date + timedelta(days=req['expected_duration'])
    due_date = end_date + timedelta(days=7)  # 7 days to pay after work ends
    today = datetime.now().date()
    
    late_days = max(0, (today - due_date).days)
    late_penalty = late_days * 100  # ₹100 per day penalty
    
    # Update the penalty in database if it changed
    if late_penalty != (req['penalty_amount'] or 0):
        cursor.execute("""
            UPDATE work_requests 
            SET penalty_amount = ?, delay_days = ?, due_date = ?
            WHERE id = ?
        """, (late_penalty, late_days, due_date.strftime('%Y-%m-%d'), request_id))
        conn.commit()
    
    total_amount = worker_wages + commission + late_penalty
    
    conn.close()
    return render_template('contractor/payment.html', req=req, 
                         worker_wages=worker_wages, commission=commission,
                         late_penalty=late_penalty, total_amount=total_amount)

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
    # Check and update request statuses
    check_request_statuses()
    
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
    # Check and update request statuses before displaying
    check_request_statuses()
    
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
    # Check and update request statuses before accepting
    check_request_statuses()
    
    conn = get_db()
    cursor = conn.cursor()
    agency_id = session['user_id']
    
    cursor.execute("SELECT city, name, email, commission_per_worker FROM agencies WHERE id = ?", (agency_id,))
    agency_info = cursor.fetchone()
    agency_city = agency_info['city']
    
    cursor.execute("""
        SELECT wr.*, u.name as contractor_name, u.email as contractor_email, u.city as contractor_city, u.area as contractor_area
        FROM work_requests wr
        JOIN users u ON wr.contractor_id = u.id
        WHERE wr.id = ? AND wr.city = ? AND wr.status = 'Pending'
    """, (request_id, agency_city))
    req = cursor.fetchone()
    
    if req:
        # Validate acceptance deadline (must accept BEFORE start date, not on start date)
        start_date = datetime.strptime(req['start_date'], '%Y-%m-%d').date()
        today = datetime.now().date()
        
        if today >= start_date:
            conn.close()
            flash('Acceptance deadline has passed. Cannot accept this request after start date.', 'error')
            return redirect(url_for('agency_new_requests'))
        
        cursor.execute("""
            UPDATE work_requests SET agency_id = ?, status = 'Accepted'
            WHERE id = ?
        """, (agency_id, request_id))
        
        cursor.execute("""
            INSERT INTO agency_earnings (agency_id, request_id, total_earned, penalty_earned)
            VALUES (?, ?, 0, 0)
        """, (agency_id, request_id))
        
        conn.commit()
        
        # Send email to agency with request details
        try:
            subject = f"Request Accepted - {req['title']}"
            body = f"""
            <html>
            <body>
                <h2>Request Accepted Successfully</h2>
                <p>Hello {agency_info['name']},</p>
                <p>You have successfully accepted the following work request:</p>
                <hr>
                <p><strong>Request Title:</strong> {req['title']}</p>
                <p><strong>Contractor:</strong> {req['contractor_name']}</p>
                <p><strong>Location:</strong> {req['contractor_city']}, {req['contractor_area'] or ''}</p>
                <p><strong>Start Date:</strong> {req['start_date']}</p>
                <p><strong>Duration:</strong> {req['expected_duration']} days</p>
                <p><strong>Workers Needed:</strong> {req['workers_needed']}</p>
                <p><strong>Worker Type:</strong> {req['worker_type']}</p>
                <p><strong>Wage per Day:</strong> ₹{req['wage_per_day']}</p>
                <p><strong>Your Commission:</strong> ₹{agency_info['commission_per_worker']} per worker</p>
                <hr>
                <p>Please assign workers before the start date.</p>
                <p>Thank you for using DailyHands!</p>
            </body>
            </html>
            """
            send_email(agency_info['email'], subject, body)
        except Exception as e:
            print(f"Email notification error: {e}")
        
        conn.close()
        flash('Request accepted successfully!', 'success')
        return redirect(url_for('agency_my_requests'))
    
    conn.close()
    flash('Request not found or already accepted.', 'error')
    return redirect(url_for('agency_new_requests'))

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

@app.route('/agency/cancel-request/<int:request_id>', methods=['POST'])
@login_required(role='agency')
def agency_cancel_request(request_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM work_requests WHERE id = ? AND agency_id = ?", 
                  (request_id, session['user_id']))
    req = cursor.fetchone()
    
    if req and req['status'] == 'Accepted':
        # Check if before start date
        start_date = datetime.strptime(req['start_date'], '%Y-%m-%d').date()
        today = datetime.now().date()
        
        if today < start_date:
            cursor.execute("UPDATE work_requests SET status = 'Cancelled' WHERE id = ?", (request_id,))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Request cancelled successfully'})
        else:
            conn.close()
            return jsonify({'success': False, 'error': 'Cannot cancel request after start date'})
    
    conn.close()
    return jsonify({'success': False, 'error': 'Request cannot be cancelled'})
    
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
    
    # Validate assignment deadline (must assign before start date)
    start_date = datetime.strptime(req['start_date'], '%Y-%m-%d').date()
    today = datetime.now().date()
    
    if today >= start_date:
        conn.close()
        return render_template('agency/assign_workers.html', req=req, workers_by_type={},
                             worker_type_reqs=[], 
                             error='Assignment deadline has passed. Cannot assign workers after start date.')
    
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
            
            # Validation 2: Check if all selected workers have wage <= required wage
            for worker_id in worker_ids:
                cursor.execute("SELECT name, daily_wage, skill FROM workers WHERE id = ?", (int(worker_id),))
                worker = cursor.fetchone()
                if worker and worker['daily_wage'] > required_wage:
                    error = f"{worker['name']}'s wage (₹{worker['daily_wage']}) exceeds the maximum ₹{required_wage}/day for {worker_type}"
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
                CASE WHEN daily_wage <= ? THEN 1 ELSE 0 END as is_valid
            FROM workers 
            WHERE agency_id = ? AND status = 'Available' AND LOWER(skill) = LOWER(?)
            ORDER BY is_valid DESC, daily_wage DESC, name
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
    
    # Calculate payment status for Completed_Payment_Pending requests
    payment_status = None
    if req['status'] == 'Completed_Payment_Pending':
        # First, try to calculate based on actual attendance records
        cursor.execute("""
            SELECT COALESCE(SUM(CASE WHEN a.status = 'Present' THEN w.daily_wage ELSE 0 END), 0) as worker_wages,
                   COUNT(DISTINCT a.date) as days_with_attendance
            FROM attendance a
            JOIN workers w ON a.worker_id = w.id
            WHERE a.request_id = ?
        """, (request_id,))
        attendance_data = cursor.fetchone()
        worker_wages = attendance_data['worker_wages']
        days_with_attendance = attendance_data['days_with_attendance']
        
        # If no attendance records exist, calculate based on expected duration and assigned workers
        if days_with_attendance == 0:
            cursor.execute("""
                SELECT w.daily_wage
                FROM request_workers rw
                JOIN workers w ON rw.worker_id = w.id
                WHERE rw.request_id = ?
            """, (request_id,))
            assigned_workers = cursor.fetchall()
            
            # Calculate total wages: sum of (each worker's daily wage × duration)
            worker_wages = sum(worker['daily_wage'] * req['expected_duration'] for worker in assigned_workers)
        
        # Calculate commission
        cursor.execute("""
            SELECT commission_per_worker FROM agencies WHERE id = ?
        """, (session['user_id'],))
        commission_per_worker = cursor.fetchone()['commission_per_worker']
        
        # Get actual number of workers assigned
        cursor.execute("""
            SELECT COUNT(DISTINCT worker_id) as worker_count
            FROM request_workers WHERE request_id = ?
        """, (request_id,))
        worker_count = cursor.fetchone()['worker_count']
        commission = worker_count * commission_per_worker
        
        # Calculate penalty
        start_date = datetime.strptime(req['start_date'], '%Y-%m-%d').date()
        end_date = start_date + timedelta(days=req['expected_duration'])
        due_date = end_date + timedelta(days=7)
        today = datetime.now().date()
        late_days = max(0, (today - due_date).days)
        late_penalty = late_days * 100
        
        total_expected = worker_wages + commission + late_penalty
        
        payment_status = {
            'due_date': due_date.strftime('%Y-%m-%d'),
            'days_overdue': late_days,
            'penalty': late_penalty,
            'expected_payment': total_expected,
            'is_overdue': late_days > 0
        }
    
    conn.close()
    return render_template('agency/request_detail.html', 
                         req=req, workers=workers, worker_types=worker_types,
                         attendance=attendance, earnings=earnings, payment_status=payment_status)

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
        WHERE ae.agency_id = ? AND wr.status = 'Completed_Paid'
        ORDER BY ae.id DESC
    """, (agency_id,))
    earnings = cursor.fetchall()
    
    cursor.execute("""
        SELECT COALESCE(SUM(ae.total_earned), 0) as total,
               COALESCE(SUM(ae.penalty_earned), 0) as penalties
        FROM agency_earnings ae
        JOIN work_requests wr ON ae.request_id = wr.id
        WHERE ae.agency_id = ? AND wr.status = 'Completed_Paid'
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
            otp_code TEXT,
            otp_expiry TIMESTAMP,
            otp_verified INTEGER DEFAULT 0,
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
            commission_per_worker REAL DEFAULT 0,
            otp_code TEXT,
            otp_expiry TIMESTAMP,
            otp_verified INTEGER DEFAULT 0,
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
            due_date DATE,
            payment_status TEXT DEFAULT 'Pending',
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
            payment_method TEXT,
            payment_details TEXT,
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

# ============ ADMIN ROUTE - PASSWORD FIX ============
@app.route('/admin/fix-passwords-now')
def admin_fix_passwords():
    """Emergency route to convert hashed passwords to shift cipher"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Set temporary password for all users
        temp_password = "TempPass123!"
        encrypted_temp = encrypt_password(temp_password)
        
        # Update users table
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor.execute("UPDATE users SET password = ?", (encrypted_temp,))
        
        # Update agencies table
        cursor.execute("SELECT COUNT(*) FROM agencies")
        agency_count = cursor.fetchone()[0]
        cursor.execute("UPDATE agencies SET password = ?", (encrypted_temp,))
        
        conn.commit()
        conn.close()
        
        return f"""
        <html>
        <head><title>Passwords Fixed</title></head>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1 style="color: green;">✓ Passwords Fixed Successfully!</h1>
            <p>Updated {user_count} contractors and {agency_count} agencies</p>
            <hr>
            <h2>Temporary Password: {temp_password}</h2>
            <p>Encrypted in DB as: {encrypted_temp}</p>
            <p>All users can now login with this password.</p>
            <p><a href="/login">Go to Login</a></p>
            <p><a href="/admin/view-passwords">View All Passwords</a></p>
        </body>
        </html>
        """
    except Exception as e:
        return f"""
        <html>
        <head><title>Error</title></head>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1 style="color: red;">❌ Error</h1>
            <p>{str(e)}</p>
            <p><a href="/">Go Home</a></p>
        </body>
        </html>
        """

@app.route('/admin/view-passwords')
def admin_view_passwords():
    """Admin route to view all passwords (encrypted and decrypted)"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("SELECT id, name, email, password FROM users")
        users = cursor.fetchall()
        
        # Get all agencies
        cursor.execute("SELECT id, name, email, password FROM agencies")
        agencies = cursor.fetchall()
        
        conn.close()
        
        html = """
        <html>
        <head>
            <title>Password Viewer</title>
            <style>
                body { font-family: Arial; padding: 20px; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #4CAF50; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
                h2 { color: #333; }
                .encrypted { color: #666; font-family: monospace; }
                .decrypted { color: #4CAF50; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>🔐 Password Viewer (Admin)</h1>
            
            <h2>Contractors ({} users)</h2>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Encrypted Password</th>
                    <th>Decrypted Password</th>
                </tr>
        """.format(len(users))
        
        for user in users:
            decrypted = decrypt_password(user['password'])
            html += f"""
                <tr>
                    <td>{user['id']}</td>
                    <td>{user['name']}</td>
                    <td>{user['email']}</td>
                    <td class="encrypted">{user['password']}</td>
                    <td class="decrypted">{decrypted}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>Agencies ({} agencies)</h2>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Encrypted Password</th>
                    <th>Decrypted Password</th>
                </tr>
        """.format(len(agencies))
        
        for agency in agencies:
            decrypted = decrypt_password(agency['password'])
            html += f"""
                <tr>
                    <td>{agency['id']}</td>
                    <td>{agency['name']}</td>
                    <td>{agency['email']}</td>
                    <td class="encrypted">{agency['password']}</td>
                    <td class="decrypted">{decrypted}</td>
                </tr>
            """
        
        html += """
            </table>
            <p><a href="/admin/fix-passwords-now">Reset All Passwords</a> | <a href="/">Go Home</a></p>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"""
        <html>
        <head><title>Error</title></head>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1 style="color: red;">❌ Error</h1>
            <p>{str(e)}</p>
            <p><a href="/">Go Home</a></p>
        </body>
        </html>
        """

if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("  DailyHands Server Starting...")
    print("=" * 50)
    print("  Open: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True)
