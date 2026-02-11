# Design Document

## Overview

DailyHands is a Flask-based web application implementing a two-sided marketplace for work requests. The system uses session-based authentication, SQLite database, and server-side rendering with Jinja2 templates. The architecture follows a traditional MVC pattern with route handlers, database access layer, and template rendering.

## Architecture

### Technology Stack
- **Backend**: Flask (Python web framework)
- **Database**: SQLite with row_factory for dict-like access
- **Authentication**: Session-based with Werkzeug password hashing
- **Security**: Flask-WTF CSRF protection
- **Visualization**: Matplotlib for server-side chart generation, Chart.js for client-side rendering
- **Frontend**: Jinja2 templates, vanilla JavaScript for real-time validation

### System Components
1. **Authentication Layer**: Session management, password hashing, role-based access control
2. **Contractor Module**: Dashboard, request creation/viewing, rating system, profile management
3. **Agency Module**: Dashboard, request discovery/acceptance, worker management, assignment, attendance, earnings
4. **API Layer**: Real-time validation, chart data endpoints, request status queries
5. **Database Layer**: SQLite with 9 tables managing users, agencies, workers, requests, and transactions

### Request Lifecycle
```
Pending → Accepted → Assigned → Completed
   ↓         ↓          ↓           ↓
Created   Agency    Workers    Contractor
          accepts   assigned   completes
```

## Components and Interfaces

### Authentication Module

**Functions:**
- `login_required(role=None)`: Decorator enforcing authentication and optional role check
- `validate_password(password)`: Validates password complexity requirements
- `is_phone_unique(phone, exclude_table, exclude_id)`: Checks phone uniqueness across all tables

**Routes:**
- `POST /register`: Creates contractor or agency account with validation
- `POST /login`: Authenticates user and creates session
- `GET /logout`: Clears session and redirects to landing
- `POST /forgot-password`: Generates OTP for password reset
- `POST /verify-otp`: Validates OTP before password reset
- `POST /reset-password`: Updates password after OTP verification

### Contractor Module

**Routes:**
- `GET /contractor/dashboard`: Displays statistics and recent requests
- `GET /contractor/create-request`: Form for creating work request
- `POST /contractor/create-request`: Creates request with multiple worker types
- `GET /contractor/requests`: Lists all contractor's requests
- `GET /contractor/request/<id>`: Displays request details with workers and attendance
- `POST /contractor/complete-request/<id>`: Marks request complete, calculates penalties
- `GET /contractor/rate/<id>`: Form for rating agency
- `POST /contractor/rate/<id>`: Submits rating and review
- `GET /contractor/profile`: Displays profile
- `POST /contractor/profile`: Updates profile information

### Agency Module

**Routes:**
- `GET /agency/dashboard`: Displays statistics, earnings, and recent requests
- `GET /agency/new-requests`: Lists available requests in agency's city
- `POST /agency/accept-request/<id>`: Accepts pending request
- `GET /agency/my-requests`: Lists agency's accepted requests
- `GET /agency/workers`: Lists workers with optional skill filter
- `POST /agency/add-worker`: Creates new worker
- `GET /agency/edit-worker/<id>`: Returns worker data as JSON
- `POST /agency/edit-worker/<id>`: Updates worker information
- `POST /agency/delete-worker/<id>`: Deletes available worker
- `GET /agency/assign-workers/<id>`: Form for assigning workers to request
- `POST /agency/assign-workers/<id>`: Validates and assigns workers
- `GET /agency/request/<id>`: Displays request details
- `GET /agency/attendance/<id>`: Form for marking attendance
- `POST /agency/attendance/<id>`: Records attendance and creates payment
- `GET /agency/earnings`: Lists all earnings by request
- `GET /agency/earnings/<id>`: Detailed earnings breakdown for request
- `GET /agency/profile`: Displays profile with ratings
- `POST /agency/profile`: Updates profile information

### API Module

**Real-time Validation:**
- `POST /api/check-availability`: Validates email, phone, or agency name uniqueness

**Data Endpoints:**
- `GET /api/request-details/<id>`: Returns request and worker type data
- `GET /api/agencies`: Returns agencies in contractor's city with ratings
- `GET /api/request-status/<id>`: Returns request status and assignment count
- `GET /api/payment-preview/<id>`: Returns total payment and days worked
- `GET /api/contractor/dashboard-data`: Returns monthly request counts
- `GET /api/agency/earnings-data`: Returns monthly earnings breakdown
- `GET /api/request/<id>/worker-earnings`: Returns worker earnings for request
- `GET /api/request/<id>/worker-days`: Returns worker days worked for request

**Chart Generation:**
- `GET /graph/contractor-requests`: Generates PNG chart of request trends
- `GET /graph/agency-earnings`: Generates PNG chart of earnings trends
- `GET /graph/request-earnings/<id>`: Generates PNG chart of worker performance

## Data Models

### Database Schema

**users** (Contractors)
- id: INTEGER PRIMARY KEY
- name: TEXT NOT NULL
- email: TEXT UNIQUE NOT NULL
- password: TEXT NOT NULL (hashed)
- phone: TEXT
- city: TEXT NOT NULL
- area: TEXT
- role: TEXT DEFAULT 'contractor'
- created_at: TIMESTAMP

**agencies**
- id: INTEGER PRIMARY KEY
- name: TEXT NOT NULL
- email: TEXT UNIQUE NOT NULL
- password: TEXT NOT NULL (hashed)
- phone: TEXT
- city: TEXT NOT NULL
- area: TEXT
- created_at: TIMESTAMP

**workers**
- id: INTEGER PRIMARY KEY
- agency_id: INTEGER FOREIGN KEY → agencies(id)
- name: TEXT NOT NULL
- phone: TEXT
- skill: TEXT NOT NULL
- daily_wage: REAL NOT NULL
- status: TEXT DEFAULT 'Available' ('Available' | 'Busy')
- created_at: TIMESTAMP

**work_requests**
- id: INTEGER PRIMARY KEY
- contractor_id: INTEGER FOREIGN KEY → users(id)
- agency_id: INTEGER FOREIGN KEY → agencies(id)
- title: TEXT NOT NULL
- description: TEXT
- worker_type: TEXT NOT NULL (summary for display)
- workers_needed: INTEGER NOT NULL (total count)
- expected_duration: INTEGER NOT NULL (days)
- wage_per_day: REAL NOT NULL (average for display)
- start_date: DATE NOT NULL
- city: TEXT NOT NULL
- status: TEXT DEFAULT 'Pending' ('Pending' | 'Accepted' | 'Assigned' | 'Completed')
- delay_days: INTEGER DEFAULT 0
- penalty_amount: REAL DEFAULT 0
- created_at: TIMESTAMP
- completed_at: TIMESTAMP

**request_worker_types** (Multi-worker type support)
- id: INTEGER PRIMARY KEY
- request_id: INTEGER FOREIGN KEY → work_requests(id)
- worker_type: TEXT NOT NULL
- workers_needed: INTEGER NOT NULL
- wage_per_day: REAL NOT NULL

**request_workers** (Assignment junction table)
- id: INTEGER PRIMARY KEY
- request_id: INTEGER FOREIGN KEY → work_requests(id)
- worker_id: INTEGER FOREIGN KEY → workers(id)
- assigned_at: TIMESTAMP

**attendance**
- id: INTEGER PRIMARY KEY
- request_id: INTEGER FOREIGN KEY → work_requests(id)
- worker_id: INTEGER FOREIGN KEY → workers(id)
- date: DATE NOT NULL
- status: TEXT NOT NULL ('Present' | 'Absent')

**payments**
- id: INTEGER PRIMARY KEY
- request_id: INTEGER FOREIGN KEY → work_requests(id)
- worker_id: INTEGER FOREIGN KEY → workers(id)
- date: DATE NOT NULL
- amount: REAL NOT NULL

**agency_earnings**
- id: INTEGER PRIMARY KEY
- agency_id: INTEGER FOREIGN KEY → agencies(id)
- request_id: INTEGER FOREIGN KEY → work_requests(id)
- total_earned: REAL DEFAULT 0
- penalty_earned: REAL DEFAULT 0

**ratings**
- id: INTEGER PRIMARY KEY
- request_id: INTEGER FOREIGN KEY → work_requests(id)
- agency_id: INTEGER FOREIGN KEY → agencies(id)
- contractor_id: INTEGER FOREIGN KEY → users(id)
- rating: INTEGER NOT NULL
- review: TEXT
- created_at: TIMESTAMP

### Key Relationships
- One contractor has many work_requests
- One agency has many workers
- One agency accepts many work_requests
- One work_request has many request_worker_types (multi-type support)
- One work_request has many request_workers (assigned workers)
- One worker has many attendance records
- One worker has many payment records
- One request has one agency_earnings record
- One request has one rating

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.


### Property Reflection

After analyzing all acceptance criteria, I identified several areas where properties can be consolidated:

**Uniqueness Properties**: Email uniqueness (1.1), phone uniqueness (1.2, 13.2), and agency name uniqueness can be combined into a single comprehensive uniqueness validation property.

**Password Security**: Password hashing on registration (1.3) and password hashing on reset (2.7) can be combined into one property about password storage.

**Status Transitions**: Individual status transition requirements (5.4, 12.3, 14.7, 19.1-19.5) can be consolidated into a single state machine property.

**Worker Status Management**: Worker status changes on assignment (14.6) and completion (7.4) can be combined into a worker lifecycle property.

**Earnings Accumulation**: Payment creation (15.3), earnings increment (15.4), and penalty addition (7.3) can be consolidated into an earnings calculation property.

**Dashboard Statistics**: Contractor dashboard counts (4.1-4.4) and agency dashboard counts (10.1-10.5) follow the same pattern and can be generalized.

**Validation Properties**: Required field validations (5.1, 13.1) follow the same pattern across different entities.

### Core Correctness Properties

Property 1: System-wide Uniqueness Enforcement
*For any* email address, phone number, or agency name, attempting to register or create an entity with a value that already exists in the system SHALL be rejected with a descriptive error message.
**Validates: Requirements 1.1, 1.2, 3.1, 3.2, 3.3, 13.2**

Property 2: Password Security
*For any* user password (on registration or reset), the stored password in the database SHALL be a hash that does not match the plaintext input.
**Validates: Requirements 1.3, 2.7**

Property 3: Password Complexity Validation
*For any* password input, validation SHALL succeed only if the password contains at least 8 characters, at least 1 uppercase letter, at least 1 number, and at least 1 special character.
**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 4: Session Creation on Authentication
*For any* valid login credentials, successful authentication SHALL create a session containing user_id, role, and name fields.
**Validates: Requirements 1.4**

Property 5: Authentication and Authorization Enforcement
*For any* protected route access attempt, the system SHALL redirect to login if no valid session exists OR if the session role does not match the required role.
**Validates: Requirements 1.5, 1.6**

Property 6: Request Status State Machine
*For any* work request, status transitions SHALL follow the sequence: Pending → Accepted → Assigned → Completed, and no other transitions SHALL be allowed.
**Validates: Requirements 5.4, 12.3, 14.7, 19.1, 19.2, 19.3, 19.4**

Property 7: City-based Request Filtering
*For any* agency viewing new requests, only requests with status Pending AND city matching the agency's city SHALL be displayed.
**Validates: Requirements 11.1, 12.1**

Property 8: Multi-worker Type Persistence
*For any* work request created with N worker types, exactly N records SHALL be created in request_worker_types table with matching request_id.
**Validates: Requirements 5.2, 5.5**

Property 9: Worker Assignment Validation
*For any* worker assignment attempt, the system SHALL verify: (1) request status is Accepted, (2) exact worker count matches each worker type requirement, (3) each worker's wage matches required wage, and (4) each worker's skill matches required type. Assignment SHALL fail if any validation fails.
**Validates: Requirements 14.1, 14.2, 14.3, 14.4**

Property 10: Worker Status Lifecycle
*For any* worker, status SHALL transition from Available to Busy when assigned to a request, and from Busy to Available when the request is completed.
**Validates: Requirements 13.3, 14.6, 7.4**

Property 11: Attendance and Payment Coupling
*For any* attendance record with status Present, a payment record SHALL be created with amount equal to the worker's daily_wage, and agency_earnings.total_earned SHALL be incremented by the same amount.
**Validates: Requirements 15.3, 15.4**

Property 12: Attendance Uniqueness
*For any* combination of request_id, worker_id, and date, at most one attendance record SHALL exist.
**Validates: Requirements 15.2**

Property 13: Delay Penalty Calculation
*For any* completed request, if completion date exceeds (start_date + expected_duration), delay_days SHALL equal the difference in days, and penalty_amount SHALL equal delay_days * 100.
**Validates: Requirements 7.1, 7.2**

Property 14: Penalty Earnings Propagation
*For any* completed request with penalty_amount > 0, the agency_earnings.penalty_earned for that request SHALL be incremented by penalty_amount.
**Validates: Requirements 7.3**

Property 15: Rating Uniqueness and Preconditions
*For any* rating submission, the system SHALL verify request status is Completed AND no existing rating exists for that request_id, otherwise rejection SHALL occur.
**Validates: Requirements 8.1, 8.3**

Property 16: Dashboard Statistics Accuracy
*For any* user dashboard view, displayed counts SHALL match the actual count of records in the database satisfying the respective filter conditions (status, role, city).
**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 10.1, 10.2, 10.3, 10.4**

Property 17: Worker Deletion Precondition
*For any* worker deletion attempt, deletion SHALL succeed only if worker status is Available, otherwise SHALL be rejected.
**Validates: Requirements 13.5**

Property 18: Request City Inheritance
*For any* work request created by a contractor, the request city SHALL equal the contractor's city.
**Validates: Requirements 5.3**

Property 19: OTP Format Validation
*For any* OTP generated for password reset, the OTP SHALL be exactly 6 digits.
**Validates: Requirements 2.5**

Property 20: Earnings Aggregation Accuracy
*For any* agency viewing earnings for a request, the displayed total_earned SHALL equal the sum of all payment amounts for that request, and penalty_earned SHALL equal the sum of all penalties for that request.
**Validates: Requirements 16.1, 16.2, 16.5**

## Error Handling

### Validation Errors
- **Uniqueness Violations**: Return descriptive error messages indicating which field (email, phone, agency name) is already in use
- **Password Complexity**: Return specific error message indicating which requirement is not met
- **Required Fields**: Return error message listing missing required fields
- **Status Preconditions**: Return error message indicating current status and required status

### Authorization Errors
- **Unauthenticated Access**: Redirect to login page
- **Unauthorized Role Access**: Redirect to login page
- **Resource Ownership**: Redirect to appropriate dashboard if user attempts to access another user's resources

### Business Logic Errors
- **Worker Assignment Mismatch**: Display error message with specific mismatch (count, wage, or skill)
- **Duplicate Operations**: Prevent duplicate attendance entries, duplicate ratings
- **Invalid State Transitions**: Prevent operations on requests in wrong status

### Database Errors
- **Connection Failures**: Log error and display generic error message to user
- **Constraint Violations**: Catch and convert to user-friendly error messages
- **Transaction Failures**: Rollback and display error message

## Testing Strategy

### Dual Testing Approach

The system requires both unit testing and property-based testing for comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of valid and invalid inputs
- Edge cases (empty strings, boundary values, special characters)
- Integration points between modules
- Error conditions and exception handling
- UI interactions and form submissions

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs
- Comprehensive input coverage through randomization
- State machine transitions
- Data integrity constraints
- Calculation correctness across all values

### Property-Based Testing Configuration

- **Library**: Use Hypothesis for Python property-based testing
- **Iterations**: Minimum 100 iterations per property test
- **Test Tagging**: Each property test must include a comment referencing the design property
- **Tag Format**: `# Feature: dailyhands-complete-system, Property N: [property title]`
- **Coverage**: Each correctness property must be implemented by a single property-based test

### Test Organization

**Authentication Tests:**
- Unit: Test specific valid/invalid credentials, session creation, logout
- Property: Test password hashing for all inputs, authentication enforcement for all routes

**Request Workflow Tests:**
- Unit: Test specific request creation, acceptance, assignment, completion scenarios
- Property: Test status transitions for all possible state combinations

**Worker Management Tests:**
- Unit: Test specific worker CRUD operations, filtering
- Property: Test uniqueness constraints for all phone numbers, status lifecycle for all workers

**Attendance and Payment Tests:**
- Unit: Test specific attendance marking, payment calculation scenarios
- Property: Test payment creation for all attendance records, earnings accumulation for all requests

**Validation Tests:**
- Unit: Test specific validation scenarios (empty fields, invalid formats)
- Property: Test uniqueness validation for all inputs, required field validation for all entities

### Integration Testing

- Test complete request lifecycle from creation to completion
- Test worker assignment with multiple worker types
- Test attendance marking and payment calculation flow
- Test earnings aggregation across multiple requests
- Test rating submission after request completion

### Performance Considerations

- Test dashboard queries with large datasets
- Test chart generation with many data points
- Test concurrent attendance marking
- Test database connection pooling under load
