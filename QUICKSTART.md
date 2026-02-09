# DailyHands - Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide gets you up and running with the enhanced DailyHands system.

---

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Web browser (Chrome, Firefox, Edge, Safari)

---

## Installation

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

**What this installs:**
- Flask 3.0.0 (web framework)
- Flask-WTF 1.2.1 (CSRF protection)
- Werkzeug 3.0.1 (password hashing)
- matplotlib 3.8.2 (legacy charts)

---

### Step 2: Initialize Database (Optional)
The database is already initialized. If you need to reset it:
```bash
python app.py
# Database will be created automatically on first run
```

---

### Step 3: Run the Application
```bash
python app.py
```

**Expected Output:**
```
==================================================
  DailyHands Server Starting...
==================================================
  Open: http://127.0.0.1:5000
==================================================
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

---

### Step 4: Open in Browser
Navigate to: **http://127.0.0.1:5000**

---

## First Time Setup

### Option 1: Use Existing Demo Accounts

**Contractor Account:**
- Email: (check database with `python view_db.py`)
- Password: (original password still works)

**Agency Account:**
- Email: (check database with `python view_db.py`)
- Password: (original password still works)

---

### Option 2: Register New Account

1. Click "Register" on landing page
2. Select role: **Contractor** or **Agency**
3. Fill in details:
   - Name: Your Name
   - Email: your@email.com
   - Phone: 1234567890
   - City: Mumbai
   - Area: Andheri
   - Password: Test@123 (must meet requirements)
4. Click "Create Account"
5. Login with your credentials

---

## Quick Tour

### As Contractor:

1. **Dashboard** - View statistics and request trends
   - Interactive line chart shows requests over time
   - Hover for details

2. **Create Request** - Post a work requirement
   - Add multiple worker types
   - Set wages and duration
   - Submit and wait for agency

3. **My Requests** - Track all your requests
   - View status (Pending, Accepted, Assigned, Completed)
   - See assigned workers
   - Mark as completed

4. **Rate Agency** - After completion
   - Give 1-5 star rating
   - Write review

---

### As Agency:

1. **Dashboard** - View business overview
   - Interactive bar chart shows earnings
   - See new requests, active jobs, workers

2. **New Requests** - Browse available work
   - See requests in your city
   - View worker requirements
   - Accept requests

3. **Manage Workers** - Add your workforce
   - Add workers with skills and wages
   - Edit worker details
   - Delete available workers

4. **Assign Workers** - Match workers to requests
   - Select workers matching requirements
   - System validates wage matching
   - Submit assignment

5. **Mark Attendance** - Daily tracking
   - Mark Present/Absent
   - Automatic payment calculation
   - Earnings updated in real-time

6. **View Earnings** - Financial overview
   - Interactive charts (doughnut + bar)
   - Worker-wise breakdown
   - Commission and penalties

---

## Key Features to Try

### 1. Password Security ✅
- Register new user → Password is hashed
- Check database: `python view_db.py`
- Passwords start with "pbkdf2:sha256:"

### 2. CSRF Protection ✅
- Inspect any form (right-click → Inspect)
- Look for: `<input type="hidden" name="csrf_token" .../>`
- All forms are protected

### 3. Interactive Charts ✅
- **Contractor Dashboard**: Line chart (requests over time)
- **Agency Dashboard**: Bar chart (earnings vs penalties)
- **Request Earnings**: Doughnut + Bar charts (worker breakdown)
- Hover over charts for tooltips

### 4. Real-time Validation ✅
- Start typing email on register page
- See instant feedback if email exists
- Same for phone numbers

---

## Common Tasks

### View Database Contents
```bash
python view_db.py
```

### Check Hashed Passwords
```bash
python view_db.py | grep "pbkdf2"
```

### Reset Password
1. Go to login page
2. Click "Forgot Password?"
3. Enter phone number
4. Note the OTP displayed
5. Enter OTP and set new password

### Create Work Request
1. Login as contractor
2. Click "Create New Request"
3. Fill details:
   - Title: "Construction Work"
   - Description: "Need workers for building"
   - Worker Type: Mason
   - Workers Needed: 5
   - Wage: 800
   - Duration: 10 days
   - Start Date: Tomorrow
4. Submit

### Accept and Assign Workers
1. Login as agency
2. Go to "New Requests"
3. Click "Accept" on a request
4. Go to "My Jobs"
5. Click "Assign Workers"
6. Select workers matching requirements
7. Submit assignment

### Mark Attendance
1. Login as agency
2. Go to request detail page
3. Click "Mark Attendance"
4. Select worker, date, status
5. Submit
6. Payment automatically calculated

---

## Troubleshooting

### Server won't start
```bash
# Check if port 5000 is in use
netstat -ano | findstr :5000

# Kill process if needed
taskkill /PID <process_id> /F

# Try again
python app.py
```

### Charts not showing
1. Check browser console (F12)
2. Verify Chart.js CDN loaded
3. Check API endpoints return data:
   - http://127.0.0.1:5000/api/contractor/dashboard-data
   - http://127.0.0.1:5000/api/agency/earnings-data

### Login fails
1. Check if migration ran: `python view_db.py`
2. Passwords should start with "pbkdf2:sha256:"
3. If not, run: `python migrate_passwords.py`
4. Try again

### CSRF token error
1. Clear browser cache
2. Restart server
3. Try again
4. Check `{{ csrf_token() }}` in form

---

## Testing the Enhancements

### Test Password Hashing
```bash
# 1. Register new user with password: Test@123
# 2. Check database
python view_db.py
# 3. Look for pbkdf2:sha256: prefix
# 4. Login with Test@123 - should work
```

### Test CSRF Protection
```bash
# 1. Open login page
# 2. Right-click → Inspect Element
# 3. Find form
# 4. Look for: <input type="hidden" name="csrf_token" .../>
# 5. Token should be present
```

### Test Interactive Charts
```bash
# 1. Login as contractor
# 2. Go to dashboard
# 3. See line chart (not PNG image)
# 4. Hover over chart - tooltip appears
# 5. Resize browser - chart adapts
```

---

## API Endpoints

### Chart Data (JSON)
```bash
# Contractor dashboard data
curl http://127.0.0.1:5000/api/contractor/dashboard-data

# Agency earnings data
curl http://127.0.0.1:5000/api/agency/earnings-data

# Worker earnings for request
curl http://127.0.0.1:5000/api/request/1/worker-earnings

# Worker days for request
curl http://127.0.0.1:5000/api/request/1/worker-days
```

**Note:** You need to be logged in (session cookie) to access these APIs.

---

## Development Tips

### Enable Debug Mode
Already enabled by default in `app.py`:
```python
app.run(debug=True)
```

### View Logs
Server logs appear in terminal where you ran `python app.py`

### Database Location
`dailyhands.db` in project root

### Static Files
- CSS: Inline in templates
- JavaScript: `static/js/charts.js`
- Images: Not used (charts are canvas-based)

---

## Production Deployment

### Before Going Live:

1. **Set Secret Key**
```bash
export FLASK_SECRET_KEY='your-random-secret-key-here'
```

2. **Disable Debug Mode**
```python
# In app.py
app.run(debug=False)
```

3. **Use Production Server**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

4. **Enable HTTPS**
- Use nginx or Apache as reverse proxy
- Get SSL certificate (Let's Encrypt)

5. **Add Rate Limiting**
```bash
pip install Flask-Limiter
```

---

## Next Steps

1. **Read Full Documentation**
   - `README.md` - Complete project overview
   - `SECURITY_AND_CHARTS_UPDATE.md` - Feature details
   - `TESTING_GUIDE.md` - Comprehensive testing

2. **Explore the Code**
   - `app.py` - Main application logic
   - `forms.py` - Form validation classes
   - `static/js/charts.js` - Chart configurations

3. **Customize**
   - Change colors in `charts.js`
   - Modify templates in `templates/`
   - Add new features

4. **Deploy**
   - Follow production checklist
   - Set up monitoring
   - Configure backups

---

## Support

### Documentation Files:
- `README.md` - Main documentation
- `SECURITY_AND_CHARTS_UPDATE.md` - Feature documentation
- `TESTING_GUIDE.md` - Testing checklist
- `IMPLEMENTATION_SUMMARY.md` - Technical summary
- `QUICKSTART.md` - This file

### Useful Commands:
```bash
# View database
python view_db.py

# Run migration
python migrate_passwords.py

# Start server
python app.py

# Install dependencies
pip install -r requirements.txt

# Check Python version
python --version
```

---

## Demo Checklist

For hackathon or client demo:

- [ ] Server running on http://127.0.0.1:5000
- [ ] Landing page loads correctly
- [ ] Can register new user
- [ ] Can login with existing user
- [ ] Contractor dashboard shows line chart
- [ ] Agency dashboard shows bar chart
- [ ] Request earnings shows doughnut + bar charts
- [ ] Charts are interactive (hover tooltips)
- [ ] Forms have CSRF tokens (inspect element)
- [ ] Passwords are hashed (check database)
- [ ] Mobile responsive (test on phone or dev tools)

---

## 🎉 You're Ready!

Your DailyHands application is now:
- ✅ Secure (password hashing + CSRF)
- ✅ Interactive (Chart.js dashboards)
- ✅ Fast (client-side rendering)
- ✅ Mobile-friendly (responsive design)
- ✅ Production-ready (backward compatible)

**Enjoy building with DailyHands! 🚀**

---

**Questions?** Check the documentation files or inspect the code comments.

**Version:** 2.0.0  
**Last Updated:** February 8, 2026
