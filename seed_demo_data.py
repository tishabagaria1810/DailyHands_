"""
DailyHands - Demo Data Seed Script
===================================
Generates realistic dummy data for demonstration purposes.

MASTER USERS:
- Contractor: Jay Patel (jaypatel26@gmail.com)
- Agency: Khushi Patel (khushipatel12@gmail.com)

SAFETY:
- Idempotent (safe to run multiple times)
- Does NOT delete existing data
- Does NOT modify authentication
- Only inserts demo data with clear markers
"""

import sqlite3
from datetime import datetime, timedelta
import random

DATABASE = 'dailyhands.db'

# Master Users (MUST exist in database)
MASTER_CONTRACTOR_EMAIL = 'jaypatel26@gmail.com'
MASTER_AGENCY_EMAIL = 'khushipatel12@gmail.com'

# Demo data markers
DEMO_MARKER = '[DEMO]'

class DemoDataSeeder:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.contractor_id = None
        self.agency_id = None
        self.city = None
        self.inserted_data = {
            'workers': [],
            'work_requests': [],
            'request_worker_types': [],
            'request_workers': [],
            'attendance': [],
            'payments': [],
            'agency_earnings': [],
            'ratings': []
        }
    
    def verify_master_users(self):
        """Verify master users exist in database"""
        print("=" * 70)
        print("STEP 1: Verifying Master Users")
        print("=" * 70)
        
        # Find contractor
        self.cursor.execute(
            "SELECT id, name, city FROM users WHERE email = ?",
            (MASTER_CONTRACTOR_EMAIL,)
        )
        contractor = self.cursor.fetchone()
        
        if not contractor:
            raise Exception(f"❌ Contractor not found: {MASTER_CONTRACTOR_EMAIL}")
        
        self.contractor_id = contractor['id']
        self.city = contractor['city']
        print(f"✓ Contractor found: {contractor['name']} (ID: {self.contractor_id}, City: {self.city})")
        
        # Find agency
        self.cursor.execute(
            "SELECT id, name, city FROM agencies WHERE email = ?",
            (MASTER_AGENCY_EMAIL,)
        )
        agency = self.cursor.fetchone()
        
        if not agency:
            raise Exception(f"❌ Agency not found: {MASTER_AGENCY_EMAIL}")
        
        self.agency_id = agency['id']
        print(f"✓ Agency found: {agency['name']} (ID: {self.agency_id}, City: {agency['city']})")
        
        if self.city != agency['city']:
            print(f"⚠️  Warning: Contractor and Agency are in different cities!")
            print(f"   Contractor: {self.city}, Agency: {agency['city']}")
            print(f"   Using contractor's city: {self.city}")
        
        print()
    
    def check_existing_demo_data(self):
        """Check if demo data already exists"""
        print("=" * 70)
        print("STEP 2: Checking for Existing Demo Data")
        print("=" * 70)
        
        # Check for demo work requests
        self.cursor.execute(
            "SELECT COUNT(*) as count FROM work_requests WHERE contractor_id = ? AND title LIKE ?",
            (self.contractor_id, f"%{DEMO_MARKER}%")
        )
        existing_requests = self.cursor.fetchone()['count']
        
        # Check for demo workers
        self.cursor.execute(
            "SELECT COUNT(*) as count FROM workers WHERE agency_id = ? AND name LIKE ?",
            (self.agency_id, f"%{DEMO_MARKER}%")
        )
        existing_workers = self.cursor.fetchone()['count']
        
        if existing_requests > 0 or existing_workers > 0:
            print(f"⚠️  Found existing demo data:")
            print(f"   - Demo work requests: {existing_requests}")
            print(f"   - Demo workers: {existing_workers}")
            print(f"\n   This script will ADD MORE demo data.")
            print(f"   To clean up, run: python cleanup_demo_data.py")
        else:
            print("✓ No existing demo data found. Starting fresh.")
        
        print()
    
    def create_workers(self):
        """Create demo workers for the agency"""
        print("=" * 70)
        print("STEP 3: Creating Demo Workers")
        print("=" * 70)
        
        workers_data = [
            ("Rajesh Kumar", "9876543210", "Mason", 800),
            ("Amit Singh", "9876543211", "Electrician", 1000),
            ("Suresh Yadav", "9876543212", "Plumber", 900),
            ("Vikram Sharma", "9876543213", "Carpenter", 850),
            ("Ramesh Patel", "9876543214", "Painter", 700),
            ("Dinesh Kumar", "9876543215", "Helper", 500),
            ("Prakash Verma", "9876543216", "Mason", 800),
            ("Santosh Gupta", "9876543217", "Electrician", 1000),
        ]
        
        for name, phone, skill, wage in workers_data:
            demo_name = f"{name} {DEMO_MARKER}"
            
            # Check if worker already exists
            self.cursor.execute(
                "SELECT id FROM workers WHERE agency_id = ? AND name = ?",
                (self.agency_id, demo_name)
            )
            existing = self.cursor.fetchone()
            
            if existing:
                worker_id = existing['id']
                print(f"  ⊙ Worker exists: {demo_name} (ID: {worker_id})")
            else:
                self.cursor.execute("""
                    INSERT INTO workers (agency_id, name, phone, skill, daily_wage, status)
                    VALUES (?, ?, ?, ?, ?, 'Available')
                """, (self.agency_id, demo_name, phone, skill, wage))
                
                worker_id = self.cursor.lastrowid
                print(f"  ✓ Created: {demo_name} - {skill} - ₹{wage}/day (ID: {worker_id})")
            
            self.inserted_data['workers'].append({
                'id': worker_id,
                'name': demo_name,
                'skill': skill,
                'wage': wage
            })
        
        print(f"\n✓ Total workers ready: {len(self.inserted_data['workers'])}")
        print()
    
    def create_work_requests(self):
        """Create demo work requests with realistic timeline"""
        print("=" * 70)
        print("STEP 4: Creating Demo Work Requests")
        print("=" * 70)
        
        today = datetime.now()
        
        # Define requests with timeline (last 6 months)
        requests_data = [
            # August 2025 - Completed
            {
                'title': f'{DEMO_MARKER} Residential Building Construction',
                'description': 'Complete construction of 2-story residential building with modern amenities',
                'worker_types': [('Mason', 5, 800), ('Helper', 3, 500)],
                'duration': 30,
                'start_date': today - timedelta(days=180),
                'status': 'Completed',
                'delay_days': 0
            },
            # August 2025 - Pending
            {
                'title': f'{DEMO_MARKER} Office Interior Renovation',
                'description': 'Complete interior renovation of office space including electrical and painting',
                'worker_types': [('Electrician', 2, 1000), ('Painter', 2, 700)],
                'duration': 15,
                'start_date': today - timedelta(days=175),
                'status': 'Pending',
                'delay_days': 0
            },
            # September 2025 - Completed
            {
                'title': f'{DEMO_MARKER} Plumbing System Installation',
                'description': 'Installation of complete plumbing system for new apartment complex',
                'worker_types': [('Plumber', 3, 900), ('Helper', 2, 500)],
                'duration': 20,
                'start_date': today - timedelta(days=150),
                'status': 'Completed',
                'delay_days': 0
            },
            # September 2025 - Accepted
            {
                'title': f'{DEMO_MARKER} Electrical Wiring Project',
                'description': 'Complete electrical wiring for commercial building',
                'worker_types': [('Electrician', 4, 1000)],
                'duration': 25,
                'start_date': today - timedelta(days=140),
                'status': 'Accepted',
                'delay_days': 0
            },
            # October 2025 - Completed with delay
            {
                'title': f'{DEMO_MARKER} Carpentry Work for Villa',
                'description': 'Custom carpentry work including doors, windows, and furniture',
                'worker_types': [('Carpenter', 3, 850), ('Helper', 2, 500)],
                'duration': 20,
                'start_date': today - timedelta(days=120),
                'status': 'Completed',
                'delay_days': 7
            },
            # October 2025 - Assigned
            {
                'title': f'{DEMO_MARKER} Painting and Finishing Work',
                'description': 'Complete painting and finishing work for residential complex',
                'worker_types': [('Painter', 4, 700), ('Helper', 2, 500)],
                'duration': 18,
                'start_date': today - timedelta(days=110),
                'status': 'Assigned',
                'delay_days': 0
            },
            # November 2025 - Completed with delay
            {
                'title': f'{DEMO_MARKER} Foundation and Masonry Work',
                'description': 'Foundation laying and masonry work for new construction',
                'worker_types': [('Mason', 6, 800), ('Helper', 4, 500)],
                'duration': 25,
                'start_date': today - timedelta(days=90),
                'status': 'Completed',
                'delay_days': 5
            },
            # December 2025 - Assigned
            {
                'title': f'{DEMO_MARKER} Multi-Trade Renovation Project',
                'description': 'Complete renovation requiring multiple skilled workers',
                'worker_types': [('Mason', 2, 800), ('Electrician', 2, 1000), ('Plumber', 2, 900)],
                'duration': 30,
                'start_date': today - timedelta(days=60),
                'status': 'Assigned',
                'delay_days': 0
            },
            # January 2026 - Accepted
            {
                'title': f'{DEMO_MARKER} Commercial Kitchen Setup',
                'description': 'Complete setup of commercial kitchen with plumbing and electrical',
                'worker_types': [('Plumber', 2, 900), ('Electrician', 2, 1000)],
                'duration': 15,
                'start_date': today - timedelta(days=30),
                'status': 'Accepted',
                'delay_days': 0
            },
            # February 2026 - Pending
            {
                'title': f'{DEMO_MARKER} Warehouse Construction',
                'description': 'Construction of large warehouse facility',
                'worker_types': [('Mason', 8, 800), ('Carpenter', 3, 850), ('Helper', 5, 500)],
                'duration': 45,
                'start_date': today - timedelta(days=10),
                'status': 'Pending',
                'delay_days': 0
            },
        ]
        
        for req_data in requests_data:
            # Calculate dates
            start_date = req_data['start_date']
            created_at = start_date - timedelta(days=5)  # Request created 5 days before start
            
            # Calculate total workers and average wage
            total_workers = sum(wt[1] for wt in req_data['worker_types'])
            avg_wage = sum(wt[1] * wt[2] for wt in req_data['worker_types']) / total_workers
            worker_type_summary = ', '.join([f"{wt[1]} {wt[0]}" for wt in req_data['worker_types']])
            
            # Insert work request
            self.cursor.execute("""
                INSERT INTO work_requests 
                (contractor_id, agency_id, title, description, worker_type, workers_needed,
                 expected_duration, wage_per_day, start_date, city, status, delay_days,
                 penalty_amount, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.contractor_id,
                self.agency_id if req_data['status'] != 'Pending' else None,
                req_data['title'],
                req_data['description'],
                worker_type_summary,
                total_workers,
                req_data['duration'],
                avg_wage,
                start_date.strftime('%Y-%m-%d'),
                self.city,
                req_data['status'],
                req_data['delay_days'],
                req_data['delay_days'] * 100,  # ₹100 per day penalty
                created_at.strftime('%Y-%m-%d %H:%M:%S'),
                (start_date + timedelta(days=req_data['duration'] + req_data['delay_days'])).strftime('%Y-%m-%d %H:%M:%S') if req_data['status'] == 'Completed' else None
            ))
            
            request_id = self.cursor.lastrowid
            
            # Insert worker type requirements
            for worker_type, count, wage in req_data['worker_types']:
                self.cursor.execute("""
                    INSERT INTO request_worker_types (request_id, worker_type, workers_needed, wage_per_day)
                    VALUES (?, ?, ?, ?)
                """, (request_id, worker_type, count, wage))
                
                self.inserted_data['request_worker_types'].append({
                    'request_id': request_id,
                    'worker_type': worker_type,
                    'count': count,
                    'wage': wage
                })
            
            self.inserted_data['work_requests'].append({
                'id': request_id,
                'title': req_data['title'],
                'status': req_data['status'],
                'start_date': start_date,
                'duration': req_data['duration'],
                'delay_days': req_data['delay_days'],
                'worker_types': req_data['worker_types']
            })
            
            print(f"  ✓ Created: {req_data['title'][:50]}...")
            print(f"    Status: {req_data['status']}, Workers: {worker_type_summary}, Start: {start_date.strftime('%Y-%m-%d')}")
        
        print(f"\n✓ Total work requests created: {len(self.inserted_data['work_requests'])}")
        print()
    
    def assign_workers_to_requests(self):
        """Assign workers to accepted/assigned/completed requests"""
        print("=" * 70)
        print("STEP 5: Assigning Workers to Requests")
        print("=" * 70)
        
        for request in self.inserted_data['work_requests']:
            if request['status'] in ['Accepted', 'Assigned', 'Completed']:
                print(f"\n  Assigning workers to: {request['title'][:50]}...")
                
                for worker_type, count, wage in request['worker_types']:
                    # Find available workers with matching skill and wage
                    available_workers = [
                        w for w in self.inserted_data['workers']
                        if w['skill'] == worker_type and w['wage'] == wage
                    ]
                    
                    if len(available_workers) < count:
                        print(f"    ⚠️  Not enough {worker_type} workers (need {count}, have {len(available_workers)})")
                        count = len(available_workers)
                    
                    # Assign workers
                    for i in range(count):
                        worker = available_workers[i]
                        
                        self.cursor.execute("""
                            INSERT INTO request_workers (request_id, worker_id)
                            VALUES (?, ?)
                        """, (request['id'], worker['id']))
                        
                        # Update worker status if assigned or active
                        if request['status'] in ['Assigned']:
                            self.cursor.execute("""
                                UPDATE workers SET status = 'Busy' WHERE id = ?
                            """, (worker['id'],))
                        
                        self.inserted_data['request_workers'].append({
                            'request_id': request['id'],
                            'worker_id': worker['id'],
                            'worker_name': worker['name']
                        })
                        
                        print(f"    ✓ Assigned: {worker['name']} ({worker['skill']})")
        
        print(f"\n✓ Total worker assignments: {len(self.inserted_data['request_workers'])}")
        print()
    
    def generate_attendance_and_payments(self):
        """Generate attendance records and payments for assigned/completed requests"""
        print("=" * 70)
        print("STEP 6: Generating Attendance & Payments")
        print("=" * 70)
        
        for request in self.inserted_data['work_requests']:
            if request['status'] in ['Assigned', 'Completed']:
                print(f"\n  Processing: {request['title'][:50]}...")
                
                # Get assigned workers for this request
                assigned_workers = [
                    aw for aw in self.inserted_data['request_workers']
                    if aw['request_id'] == request['id']
                ]
                
                # Determine attendance period
                start_date = request['start_date']
                if request['status'] == 'Completed':
                    days_to_generate = request['duration'] + request['delay_days']
                else:
                    # For assigned requests, generate attendance up to today
                    days_elapsed = (datetime.now() - start_date).days
                    days_to_generate = min(days_elapsed, request['duration'])
                
                # Generate attendance for each worker
                for worker_assignment in assigned_workers:
                    worker_id = worker_assignment['worker_id']
                    worker_name = worker_assignment['worker_name']
                    
                    # Get worker wage
                    worker = next(w for w in self.inserted_data['workers'] if w['id'] == worker_id)
                    wage = worker['wage']
                    
                    present_days = 0
                    absent_days = 0
                    
                    for day in range(days_to_generate):
                        attendance_date = start_date + timedelta(days=day)
                        
                        # 85% chance of being present
                        status = 'Present' if random.random() < 0.85 else 'Absent'
                        
                        self.cursor.execute("""
                            INSERT INTO attendance (request_id, worker_id, date, status)
                            VALUES (?, ?, ?, ?)
                        """, (request['id'], worker_id, attendance_date.strftime('%Y-%m-%d'), status))
                        
                        self.inserted_data['attendance'].append({
                            'request_id': request['id'],
                            'worker_id': worker_id,
                            'date': attendance_date,
                            'status': status
                        })
                        
                        # Generate payment if present
                        if status == 'Present':
                            self.cursor.execute("""
                                INSERT INTO payments (request_id, worker_id, date, amount)
                                VALUES (?, ?, ?, ?)
                            """, (request['id'], worker_id, attendance_date.strftime('%Y-%m-%d'), wage))
                            
                            self.inserted_data['payments'].append({
                                'request_id': request['id'],
                                'worker_id': worker_id,
                                'amount': wage
                            })
                            
                            present_days += 1
                        else:
                            absent_days += 1
                    
                    print(f"    ✓ {worker_name}: {present_days} present, {absent_days} absent")
        
        print(f"\n✓ Total attendance records: {len(self.inserted_data['attendance'])}")
        print(f"✓ Total payment records: {len(self.inserted_data['payments'])}")
        print()
    
    def calculate_agency_earnings(self):
        """Calculate and insert agency earnings for each request"""
        print("=" * 70)
        print("STEP 7: Calculating Agency Earnings")
        print("=" * 70)
        
        for request in self.inserted_data['work_requests']:
            if request['status'] in ['Accepted', 'Assigned', 'Completed']:
                # Calculate total payments for this request
                total_payments = sum(
                    p['amount'] for p in self.inserted_data['payments']
                    if p['request_id'] == request['id']
                )
                
                # Calculate penalty earnings
                penalty_earned = request['delay_days'] * 100
                
                self.cursor.execute("""
                    INSERT INTO agency_earnings (agency_id, request_id, total_earned, penalty_earned)
                    VALUES (?, ?, ?, ?)
                """, (self.agency_id, request['id'], total_payments, penalty_earned))
                
                self.inserted_data['agency_earnings'].append({
                    'request_id': request['id'],
                    'total_earned': total_payments,
                    'penalty_earned': penalty_earned
                })
                
                print(f"  ✓ Request #{request['id']}: Earned ₹{total_payments}, Penalty ₹{penalty_earned}")
        
        print(f"\n✓ Total agency earnings records: {len(self.inserted_data['agency_earnings'])}")
        print()
    
    def create_ratings(self):
        """Create ratings for completed requests"""
        print("=" * 70)
        print("STEP 8: Creating Ratings")
        print("=" * 70)
        
        reviews = [
            (5, "Excellent work! Workers were professional and completed on time."),
            (4, "Good quality work. Minor delays but overall satisfied."),
            (5, "Outstanding service. Highly recommend Khushi Patel's agency."),
            (3, "Work was completed but there were some delays and communication issues."),
        ]
        
        completed_requests = [
            r for r in self.inserted_data['work_requests']
            if r['status'] == 'Completed'
        ]
        
        for i, request in enumerate(completed_requests[:4]):  # Rate first 4 completed requests
            rating, review = reviews[i]
            
            self.cursor.execute("""
                INSERT INTO ratings (request_id, agency_id, contractor_id, rating, review)
                VALUES (?, ?, ?, ?, ?)
            """, (request['id'], self.agency_id, self.contractor_id, rating, review))
            
            self.inserted_data['ratings'].append({
                'request_id': request['id'],
                'rating': rating,
                'review': review
            })
            
            print(f"  ✓ Rated request #{request['id']}: {rating} stars - \"{review[:50]}...\"")
        
        print(f"\n✓ Total ratings created: {len(self.inserted_data['ratings'])}")
        print()
    
    def print_summary(self):
        """Print summary of all inserted data"""
        print("=" * 70)
        print("SUMMARY: Demo Data Generation Complete")
        print("=" * 70)
        print(f"\n✓ Workers created: {len(self.inserted_data['workers'])}")
        print(f"✓ Work requests created: {len(self.inserted_data['work_requests'])}")
        print(f"✓ Worker type requirements: {len(self.inserted_data['request_worker_types'])}")
        print(f"✓ Worker assignments: {len(self.inserted_data['request_workers'])}")
        print(f"✓ Attendance records: {len(self.inserted_data['attendance'])}")
        print(f"✓ Payment records: {len(self.inserted_data['payments'])}")
        print(f"✓ Agency earnings records: {len(self.inserted_data['agency_earnings'])}")
        print(f"✓ Ratings created: {len(self.inserted_data['ratings'])}")
        
        total_records = sum(len(v) for v in self.inserted_data.values())
        print(f"\n✓ TOTAL RECORDS INSERTED: {total_records}")
        
        # Calculate totals
        total_earned = sum(e['total_earned'] for e in self.inserted_data['agency_earnings'])
        total_penalty = sum(e['penalty_earned'] for e in self.inserted_data['agency_earnings'])
        
        print(f"\n💰 Financial Summary:")
        print(f"   Total Agency Earnings: ₹{total_earned:,.2f}")
        print(f"   Total Penalty Earnings: ₹{total_penalty:,.2f}")
        print(f"   Grand Total: ₹{total_earned + total_penalty:,.2f}")
        
        print(f"\n📊 Request Status Breakdown:")
        status_counts = {}
        for req in self.inserted_data['work_requests']:
            status = req['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            print(f"   {status}: {count}")
        
        print("\n" + "=" * 70)
        print("✅ Demo data generation completed successfully!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Login as Jay Patel (jaypatel26@gmail.com) to see contractor dashboard")
        print("2. Login as Khushi Patel (khushipatel12@gmail.com) to see agency dashboard")
        print("3. Explore charts, requests, workers, attendance, and earnings")
        print("\nTo remove demo data: python cleanup_demo_data.py")
        print()
    
    def run(self):
        """Execute the complete seeding process"""
        try:
            self.verify_master_users()
            self.check_existing_demo_data()
            self.create_workers()
            self.create_work_requests()
            self.assign_workers_to_requests()
            self.generate_attendance_and_payments()
            self.calculate_agency_earnings()
            self.create_ratings()
            
            # Commit all changes
            self.conn.commit()
            
            self.print_summary()
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            print("Rolling back all changes...")
            self.conn.rollback()
            raise
        
        finally:
            self.conn.close()


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("DailyHands - Demo Data Seed Script")
    print("=" * 70)
    print("\nThis script will generate realistic demo data for:")
    print("- Contractor: Jay Patel (jaypatel26@gmail.com)")
    print("- Agency: Khushi Patel (khushipatel12@gmail.com)")
    print("\n⚠️  This will INSERT new data into the database.")
    print("⚠️  Existing data will NOT be modified or deleted.")
    print("\n" + "=" * 70)
    
    response = input("\nProceed with data generation? (yes/no): ").strip().lower()
    
    if response == 'yes':
        print("\nStarting demo data generation...\n")
        seeder = DemoDataSeeder()
        seeder.run()
    else:
        print("\n❌ Operation cancelled by user.")
