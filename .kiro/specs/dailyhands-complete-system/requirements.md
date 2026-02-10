# Requirements Document

## Introduction

DailyHands is a work request management system connecting contractors who need workers with agencies that provide skilled labor. The system manages the complete workflow from request creation through worker assignment, attendance tracking, payment calculation, and performance ratings.

## Glossary

- **System**: The DailyHands web application
- **Contractor**: User who creates work requests requiring skilled workers
- **Agency**: Organization that manages workers and fulfills work requests
- **Worker**: Skilled laborer managed by an agency
- **Work_Request**: Job posting created by contractor specifying worker requirements
- **Attendance**: Daily record of worker presence on a work request
- **Payment**: Calculated amount owed based on attendance and daily wage
- **Rating**: Contractor's evaluation of agency performance after request completion
- **Session**: Authenticated user's active login state

## Requirements

### Requirement 1: User Authentication

**User Story:** As a user, I want to securely log in and register, so that I can access role-specific features.

#### Acceptance Criteria

1. WHEN a contractor or agency registers, THE System SHALL validate email uniqueness across both user types
2. WHEN a user registers, THE System SHALL validate phone uniqueness across users, agencies, and workers
3. WHEN a user registers, THE System SHALL hash passwords before storage
4. WHEN a user logs in with valid credentials, THE System SHALL create a session with user_id, role, and name
5. WHEN a user accesses a protected route without authentication, THE System SHALL redirect to login page
6. WHEN a user accesses a route requiring a different role, THE System SHALL redirect to login page

### Requirement 2: Password Management

**User Story:** As a user, I want to reset my password securely, so that I can regain access if I forget it.

#### Acceptance Criteria

1. WHEN a user requests password reset, THE System SHALL validate password contains at least 8 characters
2. WHEN a user requests password reset, THE System SHALL validate password contains at least 1 uppercase letter
3. WHEN a user requests password reset, THE System SHALL validate password contains at least 1 number
4. WHEN a user requests password reset, THE System SHALL validate password contains at least 1 special character
5. WHEN a user submits phone number for reset, THE System SHALL generate a 6-digit OTP
6. WHEN a user verifies correct OTP, THE System SHALL allow password reset
7. WHEN a user completes password reset, THE System SHALL hash the new password before storage

### Requirement 3: Real-time Validation

**User Story:** As a user, I want immediate feedback during registration, so that I know if my information is valid.

#### Acceptance Criteria

1. WHEN a user enters an email during registration, THE System SHALL check uniqueness across users and agencies
2. WHEN a user enters a phone number during registration, THE System SHALL check uniqueness across users, agencies, and workers
3. WHEN an agency enters a name during registration, THE System SHALL check uniqueness case-insensitively
4. WHEN validation fails, THE System SHALL return a descriptive error message
5. WHEN validation succeeds, THE System SHALL return success confirmation

### Requirement 4: Contractor Dashboard

**User Story:** As a contractor, I want to view my request statistics, so that I can track my activity.

#### Acceptance Criteria

1. WHEN a contractor views dashboard, THE System SHALL display total request count
2. WHEN a contractor views dashboard, THE System SHALL display pending request count
3. WHEN a contractor views dashboard, THE System SHALL display completed request count
4. WHEN a contractor views dashboard, THE System SHALL display active request count
5. WHEN a contractor views dashboard, THE System SHALL display 5 most recent requests with agency names

### Requirement 5: Work Request Creation

**User Story:** As a contractor, I want to create work requests with multiple worker types, so that I can specify complex job requirements.

#### Acceptance Criteria

1. WHEN a contractor creates a request, THE System SHALL require title, description, expected duration, and start date
2. WHEN a contractor creates a request, THE System SHALL allow multiple worker types with individual counts and wages
3. WHEN a contractor creates a request, THE System SHALL set city to contractor's city
4. WHEN a contractor creates a request, THE System SHALL set initial status to Pending
5. WHEN a contractor creates a request, THE System SHALL store worker type requirements in request_worker_types table

### Requirement 6: Work Request Viewing

**User Story:** As a contractor, I want to view my requests and their details, so that I can track progress.

#### Acceptance Criteria

1. WHEN a contractor views requests list, THE System SHALL display all requests ordered by creation date
2. WHEN a contractor views requests list, THE System SHALL display agency name for accepted requests
3. WHEN a contractor views requests list, THE System SHALL display assigned worker count
4. WHEN a contractor views request details, THE System SHALL display worker type requirements
5. WHEN a contractor views request details, THE System SHALL display assigned workers
6. WHEN a contractor views request details, THE System SHALL display attendance records
7. WHEN a contractor views request details, THE System SHALL display total payment amount

### Requirement 7: Request Completion

**User Story:** As a contractor, I want to mark requests as complete, so that I can finalize the work.

#### Acceptance Criteria

1. WHEN a contractor completes a request, THE System SHALL calculate delay days from expected end date
2. WHEN a request has delay days, THE System SHALL calculate penalty as delay_days * 100
3. WHEN a request is completed with penalty, THE System SHALL add penalty to agency earnings
4. WHEN a request is completed, THE System SHALL set all assigned workers status to Available
5. WHEN a request is completed, THE System SHALL record completion timestamp

### Requirement 8: Agency Rating

**User Story:** As a contractor, I want to rate agencies after completion, so that I can provide feedback.

#### Acceptance Criteria

1. WHEN a contractor rates an agency, THE System SHALL require request status to be Completed
2. WHEN a contractor rates an agency, THE System SHALL accept rating value and optional review text
3. WHEN a contractor submits rating, THE System SHALL prevent duplicate ratings for same request
4. WHEN a contractor submits rating, THE System SHALL store rating with request_id, agency_id, and contractor_id

### Requirement 9: Contractor Profile

**User Story:** As a contractor, I want to update my profile, so that I can keep my information current.

#### Acceptance Criteria

1. WHEN a contractor updates profile, THE System SHALL allow editing name, phone, city, and area
2. WHEN a contractor updates profile, THE System SHALL update session name
3. WHEN a contractor updates profile, THE System SHALL persist changes to database

### Requirement 10: Agency Dashboard

**User Story:** As an agency, I want to view my statistics, so that I can monitor my business.

#### Acceptance Criteria

1. WHEN an agency views dashboard, THE System SHALL display new request count in agency's city
2. WHEN an agency views dashboard, THE System SHALL display active request count
3. WHEN an agency views dashboard, THE System SHALL display completed request count
4. WHEN an agency views dashboard, THE System SHALL display total worker count
5. WHEN an agency views dashboard, THE System SHALL display total earnings including penalties
6. WHEN an agency views dashboard, THE System SHALL display 5 most recent accepted requests

### Requirement 11: New Request Discovery

**User Story:** As an agency, I want to view available requests in my city, so that I can find work opportunities.

#### Acceptance Criteria

1. WHEN an agency views new requests, THE System SHALL display only Pending requests in agency's city
2. WHEN an agency views new requests, THE System SHALL display contractor name and phone
3. WHEN an agency views new requests, THE System SHALL display worker type requirements
4. WHEN an agency views new requests, THE System SHALL order by creation date descending

### Requirement 12: Request Acceptance

**User Story:** As an agency, I want to accept requests, so that I can commit to fulfilling them.

#### Acceptance Criteria

1. WHEN an agency accepts a request, THE System SHALL verify request is in agency's city
2. WHEN an agency accepts a request, THE System SHALL verify request status is Pending
3. WHEN an agency accepts a request, THE System SHALL set agency_id and change status to Accepted
4. WHEN an agency accepts a request, THE System SHALL create agency_earnings record with zero initial values

### Requirement 13: Worker Management

**User Story:** As an agency, I want to manage my workers, so that I can maintain my workforce.

#### Acceptance Criteria

1. WHEN an agency adds a worker, THE System SHALL require name, phone, skill, and daily_wage
2. WHEN an agency adds a worker, THE System SHALL validate phone uniqueness across all tables
3. WHEN an agency adds a worker, THE System SHALL set initial status to Available
4. WHEN an agency edits a worker, THE System SHALL validate phone uniqueness excluding current worker
5. WHEN an agency deletes a worker, THE System SHALL only allow deletion if status is Available
6. WHEN an agency views workers, THE System SHALL allow filtering by skill

### Requirement 14: Worker Assignment

**User Story:** As an agency, I want to assign workers to requests, so that I can fulfill work requirements.

#### Acceptance Criteria

1. WHEN an agency assigns workers, THE System SHALL verify request status is Accepted
2. WHEN an agency assigns workers, THE System SHALL require exact count matching each worker type requirement
3. WHEN an agency assigns workers, THE System SHALL validate each worker's wage matches required wage
4. WHEN an agency assigns workers, THE System SHALL validate each worker's skill matches required type
5. WHEN assignment succeeds, THE System SHALL create request_workers records
6. WHEN assignment succeeds, THE System SHALL set worker status to Busy
7. WHEN assignment succeeds, THE System SHALL change request status to Assigned

### Requirement 15: Attendance Tracking

**User Story:** As an agency, I want to mark daily attendance, so that I can track worker presence.

#### Acceptance Criteria

1. WHEN an agency marks attendance, THE System SHALL verify request status is Assigned
2. WHEN an agency marks attendance, THE System SHALL prevent duplicate entries for same worker and date
3. WHEN attendance status is Present, THE System SHALL create payment record with worker's daily wage
4. WHEN attendance status is Present, THE System SHALL increment agency_earnings total_earned
5. WHEN attendance is marked, THE System SHALL store request_id, worker_id, date, and status

### Requirement 16: Earnings Tracking

**User Story:** As an agency, I want to view my earnings, so that I can track revenue.

#### Acceptance Criteria

1. WHEN an agency views earnings, THE System SHALL display earnings per request
2. WHEN an agency views earnings, THE System SHALL display total earned and penalty amounts
3. WHEN an agency views request earnings detail, THE System SHALL display worker-wise attendance summary
4. WHEN an agency views request earnings detail, THE System SHALL display days present and absent per worker
5. WHEN an agency views request earnings detail, THE System SHALL display total earned per worker

### Requirement 17: Agency Profile

**User Story:** As an agency, I want to update my profile and view ratings, so that I can manage my reputation.

#### Acceptance Criteria

1. WHEN an agency updates profile, THE System SHALL allow editing name, phone, city, and area
2. WHEN an agency updates profile, THE System SHALL update session name
3. WHEN an agency views profile, THE System SHALL display average rating
4. WHEN an agency views profile, THE System SHALL display total rating count

### Requirement 18: Data Visualization

**User Story:** As a user, I want to see charts of my activity, so that I can understand trends.

#### Acceptance Criteria

1. WHEN a contractor views dashboard, THE System SHALL provide API endpoint for monthly request counts
2. WHEN an agency views dashboard, THE System SHALL provide API endpoint for monthly earnings breakdown
3. WHEN an agency views request earnings, THE System SHALL provide API endpoints for worker performance charts
4. WHEN chart data is empty, THE System SHALL return placeholder data

### Requirement 19: Request Status Workflow

**User Story:** As the system, I want to enforce status transitions, so that requests follow proper workflow.

#### Acceptance Criteria

1. WHEN a request is created, THE System SHALL set status to Pending
2. WHEN an agency accepts a request, THE System SHALL transition status from Pending to Accepted
3. WHEN workers are assigned, THE System SHALL transition status from Accepted to Assigned
4. WHEN a contractor completes a request, THE System SHALL transition status from Assigned to Completed
5. WHEN status changes, THE System SHALL maintain referential integrity

### Requirement 20: CSRF Protection

**User Story:** As the system, I want to protect against CSRF attacks, so that user actions are secure.

#### Acceptance Criteria

1. WHEN the application starts, THE System SHALL initialize CSRF protection
2. WHEN a form is submitted, THE System SHALL validate CSRF token
3. WHEN CSRF validation fails, THE System SHALL reject the request
4. WHEN CSRF tokens are generated, THE System SHALL have no time limit
