# Demo Data Generation Guide

## Overview

This guide explains how to generate and manage realistic demo data for the DailyHands application.

---

## Master Users

The demo data is generated for two existing users:

### Contractor
- **Name**: Jay Patel
- **Email**: jaypatel26@gmail.com
- **Role**: Contractor

### Agency
- **Name**: Khushi Patel
- **Email**: khushipatel12@gmail.com
- **Role**: Agency

---

## What Data Will Be Generated?

### 1. Workers (8 workers)
- Rajesh Kumar - Mason - ₹800/day
- Amit Singh - Electrician - ₹1000/day
- Suresh Yadav - Plumber - ₹900/day
- Vikram Sharma - Carpenter - ₹850/day
- Ramesh Patel - Painter - ₹700/day
- Dinesh Kumar - Helper - ₹500/day
- Prakash Verma - Mason - ₹800/day
- Santosh Gupta - Electrician - ₹1000/day

### 2. Work Requests (10 requests)
Spread across last 6 months with various statuses:
- **4 Completed** (with ratings and full attendance)
- **2 Assigned** (active work with ongoing attendance)
- **2 Accepted** (workers assigned, work not started)
- **2 Pending** (not yet accepted by agency)

### 3. Attendance & Payments (60-80 records)
- Daily attendance for assigned workers
- 85% Present, 15% Absent (realistic ratio)
- Automatic payment generation for Present days

### 4. Agency Earnings (8 records)
- Total earned per request
- 10% commission calculation
- Penalty earnings from delays

### 5. Delays & Penalties
- 2 requests with delays (5-7 days)
- ₹100/day penalty calculation

### 6. Ratings (4 ratings)
- Ratings from Jay Patel to Khushi Patel
- 3-5 stars with review text
- Only for completed requests

---

## How to Generate Demo Data

### Step 1: Verify Prerequisites

Ensure you have:
- Python 3.7+ installed
- Virtual environment activated
- Database file `dailyhands.db` exists
- Master users registered in database

### Step 2: Run the Seed Script

```bash
# Activate virtual environment (if not already active)
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run the seed script
python seed_demo_data.py
```

### Step 3: Confirm Generation

When prompted, type `yes` to proceed:

```
Proceed with data generation? (yes/no): yes
```

### Step 4: Review Output

The script will display:
- Master users verification
- Each data creation step
- Summary of inserted records
- Financial totals
- Status breakdown

---

## Expected Output

```
======================================================================
DailyHands - Demo Data Seed Script
======================================================================

STEP 1: Verifying Master Users
✓ Contractor found: Jay Patel (ID: 7, City: Mumbai)
✓ Agency found: Khushi Patel (ID: 4, City: Mumbai)

STEP 2: Checking for Existing Demo Data
✓ No existing demo data found. Starting fresh.

STEP 3: Creating Demo Workers
  ✓ Created: Rajesh Kumar [DEMO] - Mason - ₹800/day (ID: 1)
  ✓ Created: Amit Singh [DEMO] - Electrician - ₹1000/day (ID: 2)
  ...
✓ Total workers ready: 8

STEP 4: Creating Demo Work Requests
  ✓ Created: [DEMO] Residential Building Construction...
    Status: Completed, Workers: 5 Mason, 3 Helper, Start: 2025-08-15
  ...
✓ Total work requests created: 10

STEP 5: Assigning Workers to Requests
  ✓ Assigned: Rajesh Kumar [DEMO] (Mason)
  ...
✓ Total worker assignments: 45

STEP 6: Generating Attendance & Payments
  ✓ Worker attendance generated with payments
✓ Total attendance records: 72
✓ Total payment records: 61

STEP 7: Calculating Agency Earnings
  ✓ Request #1: Earned ₹48000, Penalty ₹0
  ...
✓ Total agency earnings records: 8

STEP 8: Creating Ratings
  ✓ Rated request #1: 5 stars - "Excellent work! Workers were professional..."
  ...
✓ Total ratings created: 4

======================================================================
SUMMARY: Demo Data Generation Complete
======================================================================

✓ Workers created: 8
✓ Work requests created: 10
✓ Worker type requirements: 18
✓ Worker assignments: 45
✓ Attendance records: 72
✓ Payment records: 61
✓ Agency earnings records: 8
✓ Ratings created: 4

✓ TOTAL RECORDS INSERTED: 226

💰 Financial Summary:
   Total Agency Earnings: ₹183,500.00
   Total Penalty Earnings: ₹1,200.00
   Grand Total: ₹184,700.00

📊 Request Status Breakdown:
   Completed: 4
   Assigned: 2
   Accepted: 2
   Pending: 2

======================================================================
✅ Demo data generation completed successfully!
======================================================================
```

---

## Features Demonstrated

After generating demo data, you can explore:

### Contractor Dashboard (Jay Patel)
- ✅ Total requests: 10
- ✅ Pending: 2
- ✅ Active: 4
- ✅ Completed: 4
- ✅ Request trends chart (last 6 months)
- ✅ Recent requests list

### Agency Dashboard (Khushi Patel)
- ✅ New requests: 2 (pending in city)
- ✅ Active work: 4
- ✅ Completed: 4
- ✅ Total workers: 8
- ✅ Total earnings: ₹184,700
- ✅ Earnings vs penalties chart (last 6 months)

### Work Request Details
- ✅ Multiple worker types per request
- ✅ Worker assignment with validation
- ✅ Status workflow (Pending → Accepted → Assigned → Completed)

### Attendance & Payments
- ✅ Daily attendance tracking
- ✅ Present/Absent status
- ✅ Automatic payment generation
- ✅ Worker-wise earnings breakdown

### Charts & Analytics
- ✅ Contractor request trends (line chart)
- ✅ Agency earnings overview (bar chart)
- ✅ Worker earnings distribution (doughnut chart)
- ✅ Days worked by worker (bar chart)

### Ratings & Reviews
- ✅ 4 ratings from contractor to agency
- ✅ Average rating display
- ✅ Review text

---

## How to Clean Up Demo Data

### Option 1: Run Cleanup Script

```bash
python cleanup_demo_data.py
```

The script will:
1. Scan for all demo data (marked with `[DEMO]`)
2. Show what will be deleted
3. Ask for confirmation
4. Delete only demo data (preserves real data)

### Option 2: Manual Cleanup

If you prefer manual cleanup:

```sql
-- Delete demo workers
DELETE FROM workers WHERE name LIKE '%[DEMO]%';

-- Delete demo work requests
DELETE FROM work_requests WHERE title LIKE '%[DEMO]%';

-- Related data will be deleted automatically due to foreign key constraints
```

---

## Safety Features

### Idempotent
- Safe to run multiple times
- Checks for existing demo data
- Won't create duplicates

### Non-Destructive
- Does NOT delete existing data
- Does NOT modify real user data
- Does NOT change authentication

### Clearly Marked
- All demo data contains `[DEMO]` marker
- Easy to identify and remove
- Separate from real data

### Rollback Support
- Transaction-based insertion
- Automatic rollback on error
- Cleanup script available

---

## Troubleshooting

### Error: Master users not found

**Solution**: Ensure Jay Patel and Khushi Patel are registered:
```bash
# Check if users exist
python -c "import sqlite3; conn = sqlite3.connect('dailyhands.db'); cursor = conn.cursor(); cursor.execute('SELECT * FROM users WHERE email = \"jaypatel26@gmail.com\"'); print(cursor.fetchone()); cursor.execute('SELECT * FROM agencies WHERE email = \"khushipatel12@gmail.com\"'); print(cursor.fetchone())"
```

### Error: Database locked

**Solution**: Close any other connections to the database:
- Stop the Flask app if running
- Close any database viewers
- Try again

### Error: Foreign key constraint failed

**Solution**: This shouldn't happen, but if it does:
- Run the cleanup script first
- Then run the seed script again

### Demo data already exists

**Solution**: The script will add MORE demo data. To start fresh:
```bash
python cleanup_demo_data.py
python seed_demo_data.py
```

---

## Testing Checklist

After generating demo data, test these features:

### Contractor (Jay Patel)
- [ ] Login successful
- [ ] Dashboard shows correct statistics
- [ ] Request trends chart displays data
- [ ] Can view all 10 requests
- [ ] Can see request details
- [ ] Can view assigned workers
- [ ] Can see attendance records
- [ ] Can view ratings given

### Agency (Khushi Patel)
- [ ] Login successful
- [ ] Dashboard shows correct statistics
- [ ] Earnings chart displays data
- [ ] Can see new requests (2 pending)
- [ ] Can view accepted/assigned requests
- [ ] Can see all 8 workers
- [ ] Can view worker assignments
- [ ] Can see attendance records
- [ ] Can view earnings breakdown
- [ ] Can see ratings received

### Charts
- [ ] Contractor request trends (6 months)
- [ ] Agency earnings overview (6 months)
- [ ] Worker earnings distribution
- [ ] Days worked by worker

---

## Notes

- Demo data covers **last 6 months** (August 2025 - February 2026)
- All dates are relative to current date
- Financial calculations are realistic
- Attendance patterns are realistic (85% present)
- Worker assignments respect business rules
- All demo data is clearly marked with `[DEMO]`

---

## Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Review the script output for error messages
3. Ensure master users exist in database
4. Try running cleanup script first
5. Check database file permissions

---

## Files

- `seed_demo_data.py` - Generates demo data
- `cleanup_demo_data.py` - Removes demo data
- `DEMO_DATA_README.md` - This file

---

**Last Updated**: February 10, 2026
