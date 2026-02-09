# DailyHands - Testing Guide

## 🧪 Complete Testing Checklist

This guide helps you verify that all security and chart features are working correctly.

---

## 1. Password Hashing Tests

### Test 1.1: Verify Existing Passwords Are Hashed
```bash
python view_db.py
```

**Expected Output:**
- Users table: passwords start with `pbkdf2:sha256:`
- Agencies table: passwords start with `pbkdf2:sha256:`

**✅ Pass Criteria:** All passwords are hashed, none in plain text

---

### Test 1.2: Login with Existing User
1. Open http://127.0.0.1:5000/login
2. Select "Contractor" or "Agency"
3. Enter existing credentials
4. Click "Login"

**✅ Pass Criteria:** Login successful, redirected to dashboard

---

### Test 1.3: Register New User
1. Open http://127.0.0.1:5000/register
2. Fill all fields with valid data
3. Password: `Test@123` (meets requirements)
4. Click "Create Account"
5. Run `python view_db.py` again

**✅ Pass Criteria:** 
- Registration successful
- New password is hashed in database
- Can login with new credentials

---

### Test 1.4: Password Reset
1. Open http://127.0.0.1:5000/forgot-password
2. Enter registered phone number
3. Note the OTP displayed
4. Enter OTP
5. Set new password: `NewPass@456`
6. Run `python view_db.py`

**✅ Pass Criteria:**
- Password reset successful
- New password is hashed
- Can login with new password

---

## 2. CSRF Protection Tests

### Test 2.1: Verify CSRF Tokens in Forms
1. Open http://127.0.0.1:5000/login
2. Right-click → Inspect Element
3. Find the form
4. Look for: `<input type="hidden" name="csrf_token" value="..."/>`

**✅ Pass Criteria:** CSRF token present in all forms (login, register, forgot password)

---

### Test 2.2: Test CSRF Protection
1. Open browser console (F12)
2. Try to submit form without CSRF token:
```javascript
fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'email=test@test.com&password=test&role=contractor'
})
```

**✅ Pass Criteria:** Request rejected with 400 Bad Request (CSRF token missing)

---

### Test 2.3: AJAX Requests Include CSRF
1. Open browser console on any page
2. Check network tab
3. Make any AJAX request (e.g., real-time validation)
4. Check request headers

**✅ Pass Criteria:** `X-CSRFToken` header present in all POST requests

---

## 3. Interactive Charts Tests

### Test 3.1: Contractor Dashboard Chart
1. Login as contractor
2. Go to dashboard
3. Observe the "Requests Over Time" chart

**✅ Pass Criteria:**
- Line chart renders correctly
- Hover shows tooltip with request count
- Chart is responsive (resize browser window)
- Data matches your actual requests

**Test Data:**
- If no requests: Chart shows "No Data"
- If requests exist: Shows last 6 months

---

### Test 3.2: Agency Dashboard Chart
1. Login as agency
2. Go to dashboard
3. Observe the "Earnings Overview" chart

**✅ Pass Criteria:**
- Bar chart renders with 2 datasets (Earned, Penalty Bonus)
- Hover shows currency amounts (₹)
- Legend displays correctly
- Chart is responsive
- Colors: Green (earned), Orange (penalty)

---

### Test 3.3: Request Earnings Charts
1. Login as agency
2. Go to "Earnings" page
3. Click on any completed request
4. Observe two charts:
   - Worker Earnings Distribution (Doughnut)
   - Days Worked by Worker (Bar)

**✅ Pass Criteria:**
- Both charts render side-by-side
- Doughnut chart shows percentages on hover
- Bar chart shows days worked
- Worker names displayed correctly
- Charts are responsive

---

### Test 3.4: Chart Interactivity
For each chart, test:
1. **Hover**: Tooltip appears with data
2. **Resize**: Chart adapts to window size
3. **Mobile**: Open on mobile device (or use browser dev tools)
4. **Legend**: Click legend items (if applicable)

**✅ Pass Criteria:** All interactions work smoothly

---

## 4. API Endpoint Tests

### Test 4.1: Contractor Dashboard Data API
```bash
# Login first, then:
curl -X GET http://127.0.0.1:5000/api/contractor/dashboard-data \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**Expected Response:**
```json
{
  "labels": ["2025-08", "2025-09", "2025-10", "2025-11", "2025-12", "2026-01"],
  "counts": [2, 5, 3, 8, 4, 6]
}
```

**✅ Pass Criteria:** Valid JSON with labels and counts arrays

---

### Test 4.2: Agency Earnings Data API
```bash
curl -X GET http://127.0.0.1:5000/api/agency/earnings-data \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**Expected Response:**
```json
{
  "labels": ["2025-08", "2025-09", ...],
  "earned": [5000, 8000, ...],
  "penalty": [0, 100, ...]
}
```

**✅ Pass Criteria:** Valid JSON with 3 arrays of equal length

---

### Test 4.3: Worker Earnings API
```bash
curl -X GET http://127.0.0.1:5000/api/request/1/worker-earnings \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**Expected Response:**
```json
{
  "names": ["Worker 1", "Worker 2", "Worker 3"],
  "earnings": [5000, 7500, 6000]
}
```

**✅ Pass Criteria:** Valid JSON with worker names and earnings

---

### Test 4.4: Unauthorized Access
Try accessing API without login:
```bash
curl -X GET http://127.0.0.1:5000/api/contractor/dashboard-data
```

**✅ Pass Criteria:** Redirected to login page (302) or 401 Unauthorized

---

## 5. Security Validation Tests

### Test 5.1: Password Strength Validation
Try registering with weak passwords:
1. `test` → Should fail (too short)
2. `testtest` → Should fail (no uppercase)
3. `Testtest` → Should fail (no number)
4. `Testtest1` → Should fail (no special char)
5. `Test@123` → Should succeed ✅

**✅ Pass Criteria:** Only strong passwords accepted

---

### Test 5.2: Email Uniqueness
1. Register user with email: `test@example.com`
2. Try registering another user with same email
3. Should show error: "Email already registered"

**✅ Pass Criteria:** Duplicate emails rejected

---

### Test 5.3: Phone Uniqueness
1. Register user with phone: `1234567890`
2. Try registering another user with same phone
3. Should show error: "Phone number already registered"

**✅ Pass Criteria:** Duplicate phones rejected across all tables (users, agencies, workers)

---

### Test 5.4: Real-time Validation
1. Go to register page
2. Start typing email that already exists
3. Observe validation message appears instantly

**✅ Pass Criteria:** Real-time feedback without form submission

---

## 6. Backward Compatibility Tests

### Test 6.1: Existing Users Can Login
1. Use credentials from before migration
2. Login should work normally

**✅ Pass Criteria:** No login issues for existing users

---

### Test 6.2: All Routes Still Work
Test these routes:
- `/` - Landing page
- `/login` - Login page
- `/register` - Register page
- `/contractor/dashboard` - Contractor dashboard
- `/agency/dashboard` - Agency dashboard
- `/contractor/create-request` - Create request
- `/agency/workers` - Worker management

**✅ Pass Criteria:** All pages load without errors

---

### Test 6.3: Sessions Preserved
1. Login
2. Navigate to different pages
3. Close browser
4. Reopen and go to dashboard

**✅ Pass Criteria:** Still logged in (session persists)

---

## 7. Performance Tests

### Test 7.1: Chart Loading Speed
1. Open contractor dashboard
2. Open browser dev tools → Network tab
3. Reload page
4. Check time for chart to render

**✅ Pass Criteria:** Chart renders in < 500ms

---

### Test 7.2: API Response Time
1. Open Network tab
2. Navigate to dashboard
3. Check API call to `/api/contractor/dashboard-data`

**✅ Pass Criteria:** API responds in < 200ms

---

### Test 7.3: Page Load Time
1. Clear cache
2. Open dashboard
3. Check total page load time

**✅ Pass Criteria:** Page loads in < 2 seconds

---

## 8. Mobile Responsiveness Tests

### Test 8.1: Mobile Chart Rendering
1. Open browser dev tools
2. Toggle device toolbar (Ctrl+Shift+M)
3. Select iPhone or Android device
4. Navigate to dashboard

**✅ Pass Criteria:** 
- Charts resize correctly
- Tooltips work on touch
- No horizontal scrolling
- All elements visible

---

### Test 8.2: Mobile Forms
1. Open login/register on mobile view
2. Fill forms
3. Submit

**✅ Pass Criteria:**
- Forms are easy to fill
- Buttons are tappable
- No layout issues

---

## 9. Error Handling Tests

### Test 9.1: Invalid Login
1. Try logging in with wrong password
2. Should show: "Invalid credentials"

**✅ Pass Criteria:** Clear error message, no crash

---

### Test 9.2: Network Error
1. Stop the Flask server
2. Try to load a page
3. Should show connection error

**✅ Pass Criteria:** Graceful error handling

---

### Test 9.3: Invalid API Request
```bash
curl -X GET http://127.0.0.1:5000/api/request/99999/worker-earnings \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**✅ Pass Criteria:** Returns 403 Forbidden or 404 Not Found

---

## 10. Database Integrity Tests

### Test 10.1: Check Database Structure
```bash
python view_db.py
```

**✅ Pass Criteria:**
- All tables exist
- No data corruption
- Passwords are hashed
- Foreign keys intact

---

### Test 10.2: Data Consistency
1. Create a work request
2. Accept as agency
3. Assign workers
4. Mark attendance
5. Check database

**✅ Pass Criteria:**
- All related records created
- No orphaned records
- Earnings calculated correctly

---

## 🎯 Quick Test Summary

Run these commands for quick verification:

```bash
# 1. Check password hashing
python view_db.py | grep "pbkdf2"

# 2. Start server
python app.py

# 3. Open in browser
# http://127.0.0.1:5000

# 4. Test login (existing user)
# 5. Test registration (new user)
# 6. Check charts on dashboards
# 7. Verify CSRF tokens in forms (inspect element)
```

---

## 📊 Test Results Template

Use this template to track your testing:

```
Date: ___________
Tester: ___________

[ ] Password Hashing (4 tests)
[ ] CSRF Protection (3 tests)
[ ] Interactive Charts (4 tests)
[ ] API Endpoints (4 tests)
[ ] Security Validation (4 tests)
[ ] Backward Compatibility (3 tests)
[ ] Performance (3 tests)
[ ] Mobile Responsiveness (2 tests)
[ ] Error Handling (3 tests)
[ ] Database Integrity (2 tests)

Total: ___/32 tests passed

Issues Found:
1. ___________
2. ___________
3. ___________

Notes:
___________
___________
```

---

## 🐛 Common Issues & Solutions

### Issue: Charts not rendering
**Solution:** 
1. Check browser console for errors
2. Verify Chart.js CDN is loaded
3. Check API returns valid JSON

### Issue: CSRF token missing
**Solution:**
1. Ensure `{{ csrf_token() }}` in form
2. Check Flask-WTF is installed
3. Verify CSRFProtect is initialized

### Issue: Login fails
**Solution:**
1. Run migration script again
2. Check password is hashed in DB
3. Try registering new user

### Issue: API returns 403
**Solution:**
1. Verify you're logged in
2. Check you have correct role
3. Verify request ownership

---

## ✅ All Tests Passed?

If all tests pass, your DailyHands application is:
- ✅ Secure (passwords hashed, CSRF protected)
- ✅ Interactive (Chart.js dashboards)
- ✅ Fast (client-side rendering)
- ✅ Mobile-friendly (responsive design)
- ✅ Production-ready (backward compatible)

**Ready for demo! 🎉**
