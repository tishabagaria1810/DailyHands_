# DailyHands - Labour Management System

A comprehensive web-based platform that connects contractors with skilled workers through verified agencies. DailyHands streamlines the entire workflow of labour management—from posting work requests to tracking attendance and managing payments.

## Project Description

DailyHands solves the real-world problem of inefficient labour hiring and management in the construction and contracting industry. Contractors often struggle to find reliable workers, while agencies need better tools to manage their workforce and track earnings. This platform bridges that gap by providing:

- **For Contractors**: Easy posting of work requirements, real-time tracking of requests, transparent worker assignment, and agency rating system
- **For Agencies**: Access to work opportunities in their city, worker management tools, attendance tracking, and earnings analytics
- **For Workers**: Registration through verified agencies, consistent work opportunities, and transparent payment tracking

The system ensures accountability through digital attendance, automatic payment calculations, and a rating system that promotes quality service.

## Tech Stack

### Backend
- **Flask 3.0.0** - Python web framework
- **Flask-WTF 1.2.1** - CSRF protection and form validation
- **Werkzeug 3.0.1** - Password hashing and security utilities
- **SQLite3** - Lightweight relational database
- **Python 3.x** - Core programming language

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Custom styling with gradients and animations
- **Bootstrap 5** - Responsive UI framework
- **Bootstrap Icons** - Icon library
- **JavaScript (Vanilla)** - Client-side interactivity
- **Chart.js 4.4.0** - Interactive data visualization

### Data Visualization
- **Chart.js 4.4.0** - Interactive charts with hover tooltips and animations
- **Matplotlib 3.8.2** - Legacy chart generation (being phased out)

### Session Management & Security
- **Flask Sessions** - Secure server-side session handling
- **CSRF Protection** - Flask-WTF CSRF tokens on all forms
- **Password Hashing** - Werkzeug pbkdf2:sha256 hashing
- **Cookies** - Session persistence

## Key Features

### Authentication & Security
- **Role-based authentication** with separate login flows for Contractors and Agencies
- **Password hashing** using Werkzeug's pbkdf2:sha256 algorithm
- **Password validation** requiring 8+ characters, uppercase, numbers, and special characters
- **CSRF protection** on all forms using Flask-WTF
- **Unique constraint enforcement** across email, phone, and password fields
- **Session-based authorization** with decorator-protected routes
- **Forgot password flow** with OTP verification (simulated)
- **Real-time field validation** via AJAX to check email/phone availability during registration
- **Secure password storage** - all passwords hashed before database insertion

### Contractor Features
- **Work Request Creation** with multiple worker types, custom wages, and duration
- **Dashboard** with statistics (total, pending, active, completed requests)
- **Request tracking** with status updates (Pending → Accepted → Assigned → Completed)
- **Agency rating system** to rate service quality after job completion
- **Request detail view** showing assigned workers, attendance records, and payment totals
- **Profile management** to update contact information and location
- **Visual analytics** with request trends over time

### Agency Features
- **City-based request discovery** - only see requests in agency's city
- **Request acceptance** to claim work opportunities
- **Worker management** with CRUD operations (add, edit, delete workers)
- **Worker filtering** by skill type
- **Smart worker assignment** with validation:
  - Must select exact number of workers required
  - Worker wage must match request wage
  - Workers grouped by skill type
- **Attendance marking** with Present/Absent status
- **Automatic payment calculation** when marking attendance as Present
- **Earnings dashboard** showing total earned, penalties, and commission breakdown
- **Request-specific earnings** with worker-wise breakdown and visual charts
- **Profile with ratings** displaying average rating from contractors
- **Visual analytics** for earnings over time

### Work Request Management
- **Multi-worker type support** - single request can require multiple skill types (e.g., 5 Masons + 3 Electricians)
- **Status workflow**: Pending → Accepted → Assigned → Completed
- **Delay tracking** with automatic penalty calculation (₹100/day after expected completion)
- **Worker assignment tracking** with join table for many-to-many relationships
- **Request detail pages** for both contractors and agencies with different views

### Attendance & Payment System
- **Digital attendance** with date-wise tracking
- **Automatic payment generation** when worker marked Present
- **Worker-wise payment summary** showing days worked and total earned
- **Agency commission calculation** (10% of total payments)
- **Earnings aggregation** at request and agency level
- **Penalty earnings** added to agency when contractor delays completion

### Data Visualization
- **Interactive Chart.js dashboards** with hover tooltips and smooth animations
- **Contractor analytics**: Request trends over 6 months (line chart)
- **Agency analytics**: Earnings vs penalties over 6 months (bar chart)
- **Request-specific charts**: Worker-wise earnings distribution (doughnut chart) and days worked (bar chart)
- **Real-time graph rendering** with JSON API endpoints
- **Responsive charts** that adapt to mobile, tablet, and desktop
- **Export capabilities** for data analysis

### User Experience
- **Responsive design** that works on mobile, tablet, and desktop
- **Modern UI** with gradient backgrounds, glass-morphism cards, and smooth animations
- **Status badges** with color coding (Pending=orange, Accepted=blue, Assigned=purple, Completed=green)
- **Real-time validation** with instant feedback on registration forms
- **Toast notifications** for success/error messages
- **Smooth page transitions** with CSS animations
- **Intuitive navigation** with role-specific sidebars

### Database Features
- **Referential integrity** with foreign key constraints
- **Automatic timestamps** for created_at fields
- **Unique constraints** on email and phone across all user tables
- **Efficient queries** with JOINs for related data
- **Aggregate functions** for statistics and earnings calculations

## User Roles & Permissions

### Contractor
- Create and manage work requests
- View all their requests with status tracking
- View assigned workers and attendance
- Mark requests as completed
- Rate agencies after job completion
- Update profile information
- **Cannot**: Accept other requests, manage workers, mark attendance

### Agency
- Browse new requests in their city
- Accept requests to claim work
- Manage their worker pool (add/edit/delete)
- Assign workers to accepted requests
- Mark daily attendance for assigned workers
- View earnings breakdown by request
- Update profile information
- **Cannot**: Create work requests, complete requests, rate other agencies

### Access Control
- All routes protected with `@login_required` decorator
- Role-specific routes enforce role parameter
- Session-based authentication prevents unauthorized access
- Automatic redirect to login for unauthenticated users
- Role-based dashboard redirection after login

## Project Structure

```
dailyhands/
│
├── app.py                          # Main Flask application with all routes
├── requirements.txt                # Python dependencies
├── view_db.py                      # Database viewer utility script
├── dailyhands.db                   # SQLite database file
│
├── templates/                      # HTML templates
│   ├── base.html                   # Base template with common layout
│   ├── landing.html                # Public landing page
│   ├── login.html                  # Login page with role selection
│   ├── register.html               # Registration page
│   ├── forgot_password.html        # Password reset flow
│   │
│   ├── contractor/                 # Contractor-specific templates
│   │   ├── base.html               # Contractor layout with sidebar
│   │   ├── dashboard.html          # Contractor dashboard with stats
│   │   ├── create_request.html     # Multi-worker type request form
│   │   ├── requests.html           # List all contractor requests
│   │   ├── request_detail.html     # Detailed request view
│   │   ├── rate.html               # Agency rating form
│   │   └── profile.html            # Contractor profile management
│   │
│   └── agency/                     # Agency-specific templates
│       ├── base.html               # Agency layout with sidebar
│       ├── dashboard.html          # Agency dashboard with stats
│       ├── new_requests.html       # Browse available requests
│       ├── my_requests.html        # Agency's accepted requests
│       ├── request_detail.html     # Detailed request view
│       ├── assign_workers.html     # Worker assignment interface
│       ├── workers.html            # Worker management CRUD
│       ├── attendance.html         # Attendance marking form
│       ├── earnings.html           # Earnings overview
│       ├── request_earnings.html   # Request-specific earnings
│       └── profile.html            # Agency profile with ratings
│
└── venv/                           # Virtual environment (not in repo)
```

### Key Files Explained

- **app.py**: Contains all Flask routes, database logic, authentication decorators, validation functions, and graph generation
- **view_db.py**: Utility script to inspect database tables and records
- **templates/base.html**: Common HTML structure, CSS variables, and Bootstrap setup
- **templates/contractor/base.html**: Contractor-specific navigation sidebar
- **templates/agency/base.html**: Agency-specific navigation sidebar

## Database Schema

### Tables

#### users (Contractors)
- `id` - Primary key
- `name` - Full name
- `email` - Unique email address
- `password` - Plain text password (needs hashing)
- `phone` - Contact number (unique across all tables)
- `city` - Location for request matching
- `area` - Specific area/locality
- `role` - Always 'contractor'
- `created_at` - Registration timestamp

#### agencies
- `id` - Primary key
- `name` - Agency name (unique)
- `email` - Unique email address
- `password` - Plain text password (needs hashing)
- `phone` - Contact number (unique across all tables)
- `city` - Location for request matching
- `area` - Specific area/locality
- `created_at` - Registration timestamp

#### workers
- `id` - Primary key
- `agency_id` - Foreign key to agencies
- `name` - Worker name
- `phone` - Contact number (unique across all tables)
- `skill` - Worker type (Mason, Electrician, Plumber, etc.)
- `daily_wage` - Wage per day in rupees
- `status` - 'Available' or 'Busy'
- `created_at` - Registration timestamp

#### work_requests
- `id` - Primary key
- `contractor_id` - Foreign key to users
- `agency_id` - Foreign key to agencies (null until accepted)
- `title` - Request title
- `description` - Detailed description
- `worker_type` - Summary of required worker types
- `workers_needed` - Total number of workers
- `expected_duration` - Duration in days
- `wage_per_day` - Average wage per day
- `start_date` - Project start date
- `city` - Location
- `status` - Pending/Accepted/Assigned/Completed
- `delay_days` - Days delayed beyond expected duration
- `penalty_amount` - Penalty earned by agency
- `created_at` - Request creation timestamp
- `completed_at` - Completion timestamp

#### request_worker_types
- `id` - Primary key
- `request_id` - Foreign key to work_requests
- `worker_type` - Specific skill required
- `workers_needed` - Number of workers for this type
- `wage_per_day` - Wage for this worker type

#### request_workers (Assignment Junction Table)
- `id` - Primary key
- `request_id` - Foreign key to work_requests
- `worker_id` - Foreign key to workers
- `assigned_at` - Assignment timestamp

#### attendance
- `id` - Primary key
- `request_id` - Foreign key to work_requests
- `worker_id` - Foreign key to workers
- `date` - Attendance date
- `status` - 'Present' or 'Absent'

#### payments
- `id` - Primary key
- `request_id` - Foreign key to work_requests
- `worker_id` - Foreign key to workers
- `date` - Payment date
- `amount` - Payment amount (worker's daily wage)

#### agency_earnings
- `id` - Primary key
- `agency_id` - Foreign key to agencies
- `request_id` - Foreign key to work_requests
- `total_earned` - Total from worker payments
- `penalty_earned` - Bonus from contractor delays

#### ratings
- `id` - Primary key
- `request_id` - Foreign key to work_requests
- `agency_id` - Foreign key to agencies
- `contractor_id` - Foreign key to users
- `rating` - Integer rating (1-5)
- `review` - Text review
- `created_at` - Rating timestamp

### Relationships

- **One-to-Many**: Agency → Workers
- **One-to-Many**: Contractor → Work Requests
- **One-to-Many**: Agency → Work Requests (accepted)
- **Many-to-Many**: Work Requests ↔ Workers (via request_workers)
- **One-to-Many**: Work Request → Attendance Records
- **One-to-Many**: Work Request → Payments
- **One-to-Many**: Work Request → Worker Type Requirements
- **One-to-One**: Work Request → Agency Earnings
- **One-to-One**: Work Request → Rating

## API Endpoints

### Chart Data APIs (JSON)
```
GET /api/contractor/dashboard-data
    Authentication: Required (contractor role)
    Returns: { labels: ['2025-08', '2025-09', ...], counts: [5, 8, ...] }
    Description: Request trends over last 6 months for line chart

GET /api/agency/earnings-data
    Authentication: Required (agency role)
    Returns: { labels: [...], earned: [...], penalty: [...] }
    Description: Earnings and penalties over last 6 months for bar chart

GET /api/request/<int:request_id>/worker-earnings
    Authentication: Required (agency role, must own request)
    Returns: { names: ['Worker 1', ...], earnings: [5000, ...] }
    Description: Worker-wise earnings distribution for doughnut chart

GET /api/request/<int:request_id>/worker-days
    Authentication: Required (agency role, must own request)
    Returns: { names: ['Worker 1', ...], days: [15, ...] }
    Description: Days worked by each worker for bar chart
```

### Legacy Graph Routes (PNG - Deprecated)
```
GET /graph/contractor-requests
    Returns: PNG image of request trends

GET /graph/agency-earnings
    Returns: PNG image of earnings overview

GET /graph/request-earnings/<int:request_id>
    Returns: PNG image of worker earnings breakdown
```

### Validation APIs
```
POST /api/check-availability
    Parameters: field, value, role
    Returns: { available: true/false, message: '...' }
    Description: Real-time validation for email/phone/name uniqueness

GET /api/request-details/<int:request_id>
    Returns: Request details with worker types
    Description: Used for request preview modals

GET /api/request-status/<int:request_id>
    Returns: { status, created_at, agency_name, workers_assigned }
    Description: Real-time status updates

GET /api/payment-preview/<int:request_id>
    Returns: { total_payment, days_worked }
    Description: Payment calculation preview
```

## Application Flow

### Registration Flow
1. User visits landing page
2. Clicks "Register" and selects role (Contractor/Agency)
3. Fills form with real-time validation checking:
   - Email uniqueness across both user tables
   - Phone uniqueness across users, agencies, and workers
   - Agency name uniqueness
   - Password strength requirements
4. On success, redirected to login with success message

### Login Flow
1. User selects role (Contractor/Agency)
2. Enters email and password
3. System validates credentials against appropriate table
4. On success:
   - Session created with user_id, role, and name
   - Redirected to role-specific dashboard
5. On failure: Error message displayed

### Contractor Workflow
1. **Create Request**:
   - Fill title, description, duration, start date
   - Add multiple worker types with individual wages and quantities
   - Submit (status: Pending)
2. **Wait for Agency**:
   - Agency in same city sees request
   - Agency accepts (status: Accepted)
3. **Worker Assignment**:
   - Agency assigns workers matching requirements
   - Status changes to Assigned
4. **Track Progress**:
   - View assigned workers
   - Monitor attendance records
   - See payment calculations
5. **Complete**:
   - Mark request as completed
   - System calculates delays and penalties
   - Rate agency service

### Agency Workflow
1. **Browse Requests**:
   - View all pending requests in agency's city
   - See worker type requirements and wages
2. **Accept Request**:
   - Click accept to claim work
   - Agency earnings record created
   - Status changes to Accepted
3. **Assign Workers**:
   - Select workers matching each skill requirement
   - System validates:
     - Correct number of workers
     - Matching wage rates
   - Status changes to Assigned
   - Workers marked as Busy
4. **Mark Attendance**:
   - Daily attendance for each worker
   - Present = Payment auto-generated
   - Earnings automatically updated
5. **Track Earnings**:
   - View total earned per request
   - See worker-wise breakdown
   - Monitor penalties earned from delays

### Password Reset Flow
1. User clicks "Forgot Password"
2. Enters phone number and selects role
3. System generates 6-digit OTP (displayed on screen for demo)
4. User enters OTP for verification
5. User sets new password with validation
6. Password updated in database

## Setup Instructions

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Installation Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd dailyhands
```

2. **Create virtual environment**
```bash
python -m venv venv
```

3. **Activate virtual environment**

Windows:
```bash
venv\Scripts\activate
```

Linux/Mac:
```bash
source venv/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Initialize database**
The database will be automatically created when you first run the app. The `init_db()` function creates all necessary tables.

6. **Run the application**
```bash
python app.py
```

7. **Access the application**
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### Environment Variables
Currently, the app uses a hardcoded secret key. For production, set:
```bash
export FLASK_SECRET_KEY='your-secret-key-here'
```

## How to Run the Project

### Development Mode
```bash
python app.py
```
The Flask development server will start with debug mode enabled on port 5000.

### View Database Contents
```bash
python view_db.py
```
This utility script displays all tables and their contents for debugging.

### Default Access
- **Landing Page**: http://127.0.0.1:5000
- **Login**: http://127.0.0.1:5000/login
- **Register**: http://127.0.0.1:5000/register

### Testing the Application
1. Register as a Contractor in a specific city (e.g., Mumbai)
2. Register as an Agency in the same city
3. Login as Contractor and create a work request
4. Login as Agency, add workers, and accept the request
5. Assign workers to the request
6. Mark attendance and track earnings
7. Login as Contractor and complete the request
8. Rate the agency

## Security Considerations

### Current Implementation ✅
- Session-based authentication with server-side storage
- Role-based access control with decorators
- Unique constraints on email and phone numbers
- Password validation (length, complexity)
- **Password hashing** using Werkzeug's pbkdf2:sha256
- **CSRF protection** via Flask-WTF on all forms
- SQL injection prevention via parameterized queries
- Environment variable support for secret keys

### Security Improvements Made 🎉
✅ **Passwords now hashed** - All passwords stored securely with pbkdf2:sha256  
✅ **CSRF tokens implemented** - All forms protected from CSRF attacks  
✅ **Secure password reset** - New passwords automatically hashed  
✅ **Backward compatible** - Existing users can still login  

### Remaining Security Concerns (Need Improvement)
⚠️ **No HTTPS enforcement** - Data transmitted in plain text  
⚠️ **No rate limiting** - Vulnerable to brute force attacks  
⚠️ **OTP displayed on screen** - Should use SMS/email service  
⚠️ **No input sanitization** - Potential XSS vulnerabilities  
⚠️ **No session timeout** - Sessions persist indefinitely  
⚠️ **No password reset token expiration** - OTP doesn't expire

## Future Enhancements

### Critical Security Improvements (COMPLETED ✅)
- ✅ **Password hashing** using Werkzeug's pbkdf2:sha256 - IMPLEMENTED
- ✅ **CSRF token implementation** for all forms - IMPLEMENTED
- ✅ **Interactive Chart.js dashboards** - IMPLEMENTED
- **Environment-based configuration** for secret keys and database URLs
- **HTTPS enforcement** in production
- **Rate limiting** on login and registration endpoints
- **Input sanitization** to prevent XSS attacks
- **Real OTP service** integration (Twilio, AWS SNS)
- **Session timeout** configuration
- **Password reset token expiration**

### Feature Enhancements
- **Admin panel** for platform management and analytics
- **REST API** for mobile app integration
- **Real-time notifications** using WebSockets or push notifications
- **Email notifications** for request updates and assignments
- **SMS alerts** for attendance and payment confirmations
- **Advanced search** with filters for requests and agencies
- **Worker profiles** with ratings and work history
- **Payment gateway integration** for online payments
- **Document upload** for contracts and agreements
- **Multi-language support** for regional accessibility
- **Export functionality** for reports (PDF, Excel)
- **Calendar view** for request scheduling
- **Chat system** between contractors and agencies
- **Mobile app** (React Native or Flutter)

### Technical Improvements
- **Database migration** to PostgreSQL for production
- **Caching layer** using Redis for performance
- **Background tasks** using Celery for email/SMS
- **API documentation** using Swagger/OpenAPI
- **Unit tests** with pytest
- **Integration tests** for critical workflows
- **CI/CD pipeline** for automated deployment
- **Docker containerization** for easy deployment
- **Load balancing** for scalability
- **Monitoring and logging** with Sentry or ELK stack

### UI/UX Improvements (PARTIALLY COMPLETED)
- ✅ **Interactive charts** using Chart.js - IMPLEMENTED
- **Dark mode** toggle
- **Progressive Web App** (PWA) capabilities
- **Offline support** for basic features
- **Better mobile responsiveness** for complex tables
- **Drag-and-drop** worker assignment
- **Onboarding tutorial** for new users
- **Keyboard shortcuts** for power users
- **Accessibility improvements** (ARIA labels, screen reader support)

### Business Features
- **Subscription plans** for agencies (Basic, Pro, Enterprise)
- **Commission system** with configurable rates
- **Referral program** for user acquisition
- **Analytics dashboard** for platform administrators
- **Dispute resolution** system
- **Insurance integration** for workers
- **Background verification** for workers
- **Performance metrics** for agencies and workers
- **Seasonal demand forecasting** using ML

## Screenshots

*Screenshots to be added showing:*
- Landing page with hero section
- Login/Registration forms
- Contractor dashboard with statistics
- Work request creation form
- Agency dashboard
- Worker management interface
- Worker assignment screen
- Attendance marking
- Earnings breakdown with charts
- Rating system

## Author / Credits

**DailyHands** - Labour Management System

Developed as a comprehensive solution for connecting contractors with skilled workers through verified agencies.

---

**License**: Not specified

**Version**: 1.0.0

**Last Updated**: 2024

For questions, issues, or contributions, please contact the development team.
