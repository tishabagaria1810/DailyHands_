# DailyHands – Labour Management System

DailyHands is a full-stack web application that connects **contractors** with **skilled workers** through **verified agencies**.

It digitises the entire labour workflow — from work request creation to attendance tracking, payment calculation, and performance analytics.

---

## 🚀 Project Overview

DailyHands solves real-world labour management problems by providing:

- **Contractors** have a simple way to post work requirements and track execution
- **Agencie’s** tools to manage workers, attendance, and earnings
- **Transparency** through digital attendance, automated payments, and ratings

The system is designed for **clarity, accountability, and scalability**.

---

## ✨ Core Features

### 🔐 Authentication & Security

- Role-based authentication (Contractor & Agency)
- Session-based access control with route protection
- Simple shift cipher password encryption (shift by +3)
- CSRF protection on all forms (Flask-WTF)
- Login, logout, and password reset (OTP via SMS/Email)
- Unique constraints on email, phone, and agency name
- Backwards-compatible password migration

---

### 🧑‍💼 Contractor Features

- Create work requests with **multiple worker types**
- Custom wages and quantities per skill
- Dashboard with request statistics
- Request lifecycle tracking
    
    *(Pending → Accepted → Assigned → Completed)*
    
- View assigned workers, attendance, and payments
- Rate agencies after completion
- Profile management (name, phone, city, area)
- Automatic delay penalty calculation

---

### 🏢 Agency Features

- Discover requests **city-wise**
- Accept and manage work requests
- Worker management (CRUD)
- Smart worker assignment with strict validation
- Attendance marking (Present / Absent)
- Automatic payment & commission calculation
- Earnings dashboard with penalties & breakdowns
- Profile with average rating

---

### 📋 Work, Attendance & Payments

- Multi-skill job requests
- Many-to-many worker assignment
- Daily digital attendance tracking
- Automatic payment generation
- Agency commission (10%)
- Delay penalty earnings

---

### 📊 Data Visualization

- Interactive **Chart.js dashboards**
- Contractor: Request trends (line chart)
- Agency: Earnings vs penalties (bar chart)
- Request-level worker analytics (doughnut + bar)
- JSON APIs for real-time charts
- Legacy Matplotlib PNG charts (deprecated, maintained)

---

### ⚡ Real-Time Validation & UX

- Live password strength validation
- Password visibility toggle (eye icon)
- Live phone number validation (digits only, 10-digit)
- AJAX availability checks (email, phone, agency name)
- Form reset on role switch
- Responsive, modern UI (Bootstrap 5)
- Floating labels, status badges, animations
- Role-specific navigation & dashboards

---

## 🧪 Preview Mode

- Isolated UI preview route (`/preview/dashboard`)
- No authentication or database usage
- Safe for design inspection

---

## 🛠️ Tech Stack

### Backend

- **Python 3.x**
- **Flask 3.0.0**
- **Flask-WTF** (CSRF protection)
- **Twilio** (SMS OTP)
- **SQLite3** (relational database)

### Frontend

- **Jinja2** templating
- **Bootstrap 5.3.2**
- **Bootstrap Icons**
- **Vanilla JavaScript**
- **Custom CSS** (gradients, animations, glass-morphism)

### Visualization

- **Chart.js 4.4.0** (primary)
- **Matplotlib 3.8.2** (legacy)

---

## 🗄️ Database Overview

### Core Tables

- users (contractors)
- agencies
- workers
- work_requests
- request_worker_types

### Relationship Tables

- request_workers
- attendance
- payments
- agency_earnings
- ratings

Supports:

- One-to-many and many-to-many relationships
- Aggregate analytics and reporting
- Referential integrity via foreign keys

---

## 🔁 Application Flow (High Level)

### Registration

1. Select role (Contractor / Agency)
2. Fill form with live validation
3. Password hashed & stored securely
4. Redirect to login

### Login

1. Role selection
2. Credential verification
3. Session creation
4. Redirect to role dashboard

### Contractor Workflow

- Create request → Track → Complete → Rate agency

### Agency Workflow

- Discover → Accept → Assign workers → Mark attendance → Track earnings

---

## ⚙️ Setup & Run

### Prerequisites

- Python 3.7+
- pip

### Installation

```bash
git clone <repository-url>
cd dailyhands
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate # Linux/Mac
pip install -r requirements.txt
python app.py
```

Open:

```
http://127.0.0.1:5000
```

---

## 🔐 Security Status

### Implemented ✅

- Password hashing
- CSRF protection
- Parameterised SQL queries
- Role-based access control

### Known Limitations ⚠️

- No HTTPS enforcement (dev only)
- No rate limiting
- OTP is simulated
- No session timeout
- No XSS sanitisation
- SQLite is not recommended for production

---

## 🔮 Future Enhancements (Planned)

- Third-party dashboard UI kit integration
- Dark/light mode toggle
- Rate limiting & session expiry
- Real OTP (SMS / Email)
- PostgreSQL migration
- Admin panel
- REST API
- Mobile app integration
- CI/CD & Docker support

---

## 📄 License & Metadata

- **Version**: 2.0.0
- **Status**: Stable (Internal / Demo Ready)
- **License**: Not specified