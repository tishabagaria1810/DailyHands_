"""
Database Reset and Seed Script for DailyHands
Resets database and populates with realistic demo data
"""
import sqlite3
import random
from datetime import datetime, timedelta

DATABASE = 'dailyhands.db'

# Shift cipher encryption (shift by 3)
def encrypt_password(password):
    encrypted = ''
    for char in password:
        if char.isalpha():
            if char.isupper():
                encrypted += chr((ord(char) - ord('A') + 3) % 26 + ord('A'))
            else:
                encrypted += chr((ord(char) - ord('a') + 3) % 26 + ord('a'))
        elif char.isdigit():
            encrypted += str((int(char) + 3) % 10)
        else:
            encrypted += char
    return encrypted

def random_date_last_months(months=8):
    """Generate random date within last N months"""
    days_ago = random.randint(0, months * 30)
    return (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')

def random_past_date(start_days_ago, end_days_ago):
    """Generate random date between two points in past"""
    days_ago = random.randint(end_days_ago, start_days_ago)
    return (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

def reset_database():
    """Drop all tables and recreate schema"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("Dropping all tables...")
    cursor.executescript('''
        DROP TABLE IF EXISTS request_worker_types;
        DROP TABLE IF EXISTS ratings;
        DROP TABLE IF EXISTS agency_earnings;
        DROP TABLE IF EXISTS payments;
        DROP TABLE IF EXISTS attendance;
        DROP TABLE IF EXISTS request_workers;
        DROP TABLE IF EXISTS work_requests;
        DROP TABLE IF EXISTS workers;
        DROP TABLE IF EXISTS agencies;
        DROP TABLE IF EXISTS users;
    ''')
    
    print("Creating fresh schema...")
    cursor.executescript('''
        CREATE TABLE users (
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
        
        CREATE TABLE agencies (
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
        
        CREATE TABLE workers (
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
        
        CREATE TABLE work_requests (
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
        
        CREATE TABLE request_workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            worker_id INTEGER NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES work_requests(id),
            FOREIGN KEY (worker_id) REFERENCES workers(id)
        );
        
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            worker_id INTEGER NOT NULL,
            date DATE NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (request_id) REFERENCES work_requests(id),
            FOREIGN KEY (worker_id) REFERENCES workers(id)
        );
        
        CREATE TABLE payments (
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
        
        CREATE TABLE agency_earnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agency_id INTEGER NOT NULL,
            request_id INTEGER NOT NULL,
            total_earned REAL DEFAULT 0,
            penalty_earned REAL DEFAULT 0,
            FOREIGN KEY (agency_id) REFERENCES agencies(id),
            FOREIGN KEY (request_id) REFERENCES work_requests(id)
        );
        
        CREATE TABLE ratings (
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
        
        CREATE TABLE request_worker_types (
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
    print("✓ Database reset complete\n")

def seed_contractors():
    """Seed realistic contractor data"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("Seeding contractors...")
    
    contractors = [
        # Surat (2)
        ('Neeraj Desai', 'neeraj.desai@gmail.com', 'Password123!', '9876543210', 'Surat', 'Adajan'),
        ('Pooja Mehta', 'pooja.mehta@outlook.com', 'Secure456@', '9123456789', 'Surat', 'Vesu'),
        # Ahmedabad (1)
        ('Rohit Patel', 'rohit.patel@gmail.com', 'MyPass789#', '9812345678', 'Ahmedabad', 'Satellite'),
        # Jaipur (1)
        ('Ankit Sharma', 'ankit.sharma@yahoo.com', 'Strong321$', '9090909091', 'Jaipur', 'Malviya Nagar'),
        # Mumbai (1)
        ('Suresh Iyer', 'suresh.iyer@gmail.com', 'Mumbai@123', '9988776655', 'Mumbai', 'Andheri'),
        # Delhi (1)
        ('Vikram Singh', 'vikram.singh@gmail.com', 'Delhi#456', '9876501234', 'Delhi', 'Dwarka'),
    ]
    
    for name, email, password, phone, city, area in contractors:
        encrypted_pwd = encrypt_password(password)
        created = random_date_last_months(8)
        cursor.execute('''
            INSERT INTO users (name, email, password, phone, city, area, role, otp_verified, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'contractor', 1, ?)
        ''', (name, email.lower(), encrypted_pwd, phone, city, area, created))
    
    conn.commit()
    conn.close()
    print(f"✓ Seeded {len(contractors)} contractors\n")

def seed_agencies():
    """Seed one agency per city"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("Seeding agencies...")
    
    agencies = [
        ('Surat Labour Solutions', 'surat.labour@gmail.com', 'Agency@123', '9876000001', 'Surat', 'Piplod', 100),
        ('Ahmedabad Workforce Hub', 'ahmedabad.work@outlook.com', 'Work#456', '9876000002', 'Ahmedabad', 'Vastrapur', 120),
        ('Jaipur Manpower Services', 'jaipur.manpower@gmail.com', 'Jaipur789!', '9876000003', 'Jaipur', 'Vaishali Nagar', 90),
        ('Mumbai Skilled Workers', 'mumbai.skilled@yahoo.com', 'Mumbai@321', '9876000004', 'Mumbai', 'Bandra', 150),
        ('Delhi Construction Crew', 'delhi.crew@gmail.com', 'Delhi#654', '9876000005', 'Delhi', 'Rohini', 110),
    ]
    
    for name, email, password, phone, city, area, commission in agencies:
        encrypted_pwd = encrypt_password(password)
        created = random_date_last_months(8)
        cursor.execute('''
            INSERT INTO agencies (name, email, password, phone, city, area, commission_per_worker, otp_verified, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        ''', (name, email.lower(), encrypted_pwd, phone, city, area, commission, created))
    
    conn.commit()
    conn.close()
    print(f"✓ Seeded {len(agencies)} agencies\n")

def seed_workers():
    """Seed 30+ workers per agency"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("Seeding workers...")
    
    # Get all agencies
    cursor.execute("SELECT id, city FROM agencies")
    agencies = cursor.fetchall()
    
    skills = ['Mason', 'Electrician', 'Painter', 'Plumber', 'Helper', 'Carpenter', 'Welder']
    
    first_names = ['Rajesh', 'Amit', 'Sunil', 'Prakash', 'Dinesh', 'Ramesh', 'Mahesh', 'Vijay', 
                   'Anil', 'Sanjay', 'Ravi', 'Manoj', 'Ashok', 'Deepak', 'Rahul', 'Kiran',
                   'Ganesh', 'Santosh', 'Vishal', 'Nitin', 'Sachin', 'Ajay', 'Pankaj', 'Yogesh']
    
    last_names = ['Kumar', 'Singh', 'Patel', 'Sharma', 'Verma', 'Gupta', 'Yadav', 'Joshi',
                  'Reddy', 'Nair', 'Pillai', 'Desai', 'Shah', 'Mehta', 'Agarwal', 'Jain']
    
    phone_base = 7000000000
    total_workers = 0
    
    for agency_id, city in agencies:
        for i in range(35):  # 35 workers per agency
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            phone = str(phone_base + total_workers)
            skill = skills[i % len(skills)]
            wage = random.choice([400, 450, 500, 550, 600, 650, 700])
            status = 'Available'
            created = random_date_last_months(7)
            
            cursor.execute('''
                INSERT INTO workers (agency_id, name, phone, skill, daily_wage, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (agency_id, name, phone, skill, wage, status, created))
            
            total_workers += 1
    
    conn.commit()
    conn.close()
    print(f"✓ Seeded {total_workers} workers\n")

def seed_requests():
    """Seed 3-5 requests per contractor with various statuses"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("Seeding work requests...")
    
    # Get contractors
    cursor.execute("SELECT id, city FROM users WHERE role = 'contractor'")
    contractors = cursor.fetchall()
    
    # Get agencies by city
    cursor.execute("SELECT id, city, commission_per_worker FROM agencies")
    agencies_data = cursor.fetchall()
    agencies_by_city = {}
    for ag_id, city, commission in agencies_data:
        agencies_by_city[city] = (ag_id, commission)
    
    project_titles = [
        'Residential Building Construction',
        'Office Renovation Project',
        'Villa Interior Work',
        'Commercial Complex Painting',
        'Apartment Electrical Wiring',
        'Shopping Mall Plumbing',
        'House Extension Work',
        'Factory Floor Construction',
        'Warehouse Repair Work',
        'School Building Renovation',
    ]
    
    statuses = ['Pending', 'Accepted', 'Assigned', 'Completed_Payment_Pending', 'Completed_Paid', 'Cancelled', 'Rejected']
    skills = ['Mason', 'Electrician', 'Painter', 'Plumber', 'Helper', 'Carpenter', 'Welder']
    
    request_id = 1
    
    for contractor_id, city in contractors:
        num_requests = random.randint(3, 5)
        
        for _ in range(num_requests):
            title = random.choice(project_titles)
            description = f"Need skilled workers for {title.lower()} in {city}"
            skill = random.choice(skills)
            workers_needed = random.randint(2, 6)
            duration = random.randint(5, 30)
            wage = random.choice([500, 550, 600, 650, 700])
            
            # Determine status and dates
            status = random.choice(statuses)
            created_days_ago = random.randint(30, 240)
            created = random_date_last_months(8)
            
            if status == 'Pending':
                start_date = random_past_date(0, -5)  # Future date
                agency_id = None
            elif status == 'Cancelled':
                start_date = random_past_date(created_days_ago - 10, created_days_ago - 20)
                agency_id = None
            elif status == 'Rejected':
                start_date = random_past_date(created_days_ago - 5, created_days_ago - 15)
                agency_id = agencies_by_city.get(city, (None, 0))[0]
            else:
                start_date = random_past_date(created_days_ago - 10, created_days_ago - 30)
                agency_id = agencies_by_city.get(city, (None, 0))[0]
            
            # Payment status
            if status == 'Completed_Paid':
                payment_status = 'Paid'
                completed_at = random_date_last_months(6)
            elif status == 'Completed_Payment_Pending':
                payment_status = 'Pending'
                completed_at = random_date_last_months(4)
            else:
                payment_status = 'Pending'
                completed_at = None
            
            cursor.execute('''
                INSERT INTO work_requests 
                (contractor_id, agency_id, title, description, worker_type, workers_needed, 
                 expected_duration, wage_per_day, start_date, city, status, payment_status, 
                 completed_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (contractor_id, agency_id, title, description, skill, workers_needed,
                  duration, wage, start_date, city, status, payment_status, completed_at, created))
            
            # Add worker type requirements
            cursor.execute('''
                INSERT INTO request_worker_types (request_id, worker_type, workers_needed, wage_per_day)
                VALUES (?, ?, ?, ?)
            ''', (request_id, skill, workers_needed, wage))
            
            # Handle Assigned and Completed requests
            if status in ['Assigned', 'Completed_Payment_Pending', 'Completed_Paid'] and agency_id:
                # Get available workers from same city with matching skill
                cursor.execute('''
                    SELECT id FROM workers 
                    WHERE agency_id = ? AND skill = ? AND status = 'Available'
                    LIMIT ?
                ''', (agency_id, skill, workers_needed))
                
                available_workers = cursor.fetchall()
                
                if len(available_workers) >= workers_needed:
                    for worker_id_tuple in available_workers[:workers_needed]:
                        worker_id = worker_id_tuple[0]
                        
                        # Assign worker
                        cursor.execute('''
                            INSERT INTO request_workers (request_id, worker_id)
                            VALUES (?, ?)
                        ''', (request_id, worker_id))
                        
                        # Update worker status
                        if status == 'Assigned':
                            cursor.execute('UPDATE workers SET status = "Busy" WHERE id = ?', (worker_id,))
                        
                        # Add attendance for completed requests
                        if status in ['Completed_Payment_Pending', 'Completed_Paid']:
                            for day in range(duration):
                                att_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=day)).strftime('%Y-%m-%d')
                                att_status = 'Present' if random.random() > 0.15 else 'Absent'
                                
                                cursor.execute('''
                                    INSERT INTO attendance (request_id, worker_id, date, status)
                                    VALUES (?, ?, ?, ?)
                                ''', (request_id, worker_id, att_date, att_status))
                                
                                # Add payment for present days
                                if att_status == 'Present':
                                    cursor.execute('''
                                        INSERT INTO payments (request_id, worker_id, date, amount)
                                        VALUES (?, ?, ?, ?)
                                    ''', (request_id, worker_id, att_date, wage))
                    
                    # Add agency earnings
                    if status in ['Completed_Payment_Pending', 'Completed_Paid']:
                        cursor.execute('''
                            SELECT SUM(amount) FROM payments WHERE request_id = ?
                        ''', (request_id,))
                        total_paid = cursor.fetchone()[0] or 0
                        
                        penalty = random.choice([0, 0, 0, 100, 200]) if status == 'Completed_Paid' else 0
                        
                        cursor.execute('''
                            INSERT INTO agency_earnings (agency_id, request_id, total_earned, penalty_earned)
                            VALUES (?, ?, ?, ?)
                        ''', (agency_id, request_id, total_paid, penalty))
                        
                        # Add rating for completed paid requests
                        if status == 'Completed_Paid' and random.random() > 0.3:
                            rating = random.randint(3, 5)
                            reviews = [
                                'Excellent service, workers were skilled and punctual',
                                'Good work quality, satisfied with the results',
                                'Professional team, completed on time',
                                'Workers were hardworking and cooperative',
                                'Satisfactory work, would recommend'
                            ]
                            review = random.choice(reviews)
                            
                            cursor.execute('''
                                INSERT INTO ratings (request_id, agency_id, contractor_id, rating, review)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (request_id, agency_id, contractor_id, rating, review))
            
            request_id += 1
    
    conn.commit()
    conn.close()
    print(f"✓ Seeded {request_id - 1} work requests with related data\n")

def verify_data():
    """Verify seeded data integrity"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("DATA VERIFICATION")
    print("=" * 60)
    
    cursor.execute("SELECT COUNT(*) FROM users")
    print(f"Contractors: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM agencies")
    print(f"Agencies: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM workers")
    print(f"Workers: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM work_requests")
    print(f"Work Requests: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM request_workers")
    print(f"Worker Assignments: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM attendance")
    print(f"Attendance Records: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM payments")
    print(f"Payment Records: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM agency_earnings")
    print(f"Agency Earnings: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM ratings")
    print(f"Ratings: {cursor.fetchone()[0]}")
    
    print("=" * 60)
    
    conn.close()

def main():
    print("\n" + "=" * 60)
    print("DAILYHANDS DATABASE RESET & SEED")
    print("=" * 60 + "\n")
    
    reset_database()
    seed_contractors()
    seed_agencies()
    seed_workers()
    seed_requests()
    verify_data()
    
    print("\n✓ Database reset and seeding complete!")
    print("=" * 60 + "\n")

if __name__ == '__main__':
    main()
