# Hospital Management System

A simple Flask-based Hospital Management System for university assignment.

## Features

### Core Features
- **Patient Management**: Register, view, search, edit, and delete patients
- **Doctor Management**: Add, view, edit doctor profiles with specialties
- **Appointment System**: Book, view, complete, and cancel appointments

### Additional Features
- **Billing System**: Generate bills, track payments, print receipts
- **Prescriptions**: Write and view prescriptions
- **Role-based Access**: Admin, Doctor, and Receptionist roles

## Database Schema

The system uses 6 tables:
1. **Users** - Login credentials and roles
2. **Patients** - Patient information
3. **Doctors** - Doctor profiles and specialties
4. **Appointments** - Appointment scheduling
5. **Bills** - Billing and payment tracking
6. **Prescriptions** - Medical prescriptions

## Installation

1. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**:
   ```bash
   python init_db.py
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Open in browser**:
   ```
   http://localhost:5000
   ```

## Default Login Credentials

| Role         | Username    | Password      |
|--------------|-------------|---------------|
| Admin        | admin       | admin123      |
| Doctor       | doctor      | doctor123     |
| Receptionist | reception   | reception123  |

## Project Structure

```
hospital-management/
├── app.py              # Main Flask application
├── models.py           # Database models
├── init_db.py          # Database initialization script
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── templates/          # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── patients.html
│   ├── add_patient.html
│   ├── edit_patient.html
│   ├── view_patient.html
│   ├── doctors.html
│   ├── add_doctor.html
│   ├── edit_doctor.html
│   ├── appointments.html
│   ├── book_appointment.html
│   ├── bills.html
│   ├── generate_bill.html
│   ├── receipt.html
│   ├── prescriptions.html
│   ├── add_prescription.html
│   └── view_prescription.html
└── static/
    └── style.css       # CSS styling
```

## Role Permissions

### Admin
- Full access to all features
- Can add/edit/delete doctors
- Can manage all patients and appointments

### Doctor
- View assigned appointments
- Write prescriptions
- View patient details

### Receptionist
- Register new patients
- Book appointments
- Generate bills

## Technologies Used

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **Frontend**: HTML, CSS (custom styling)

## ER Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     PATIENT     │     │   APPOINTMENT   │     │     DOCTOR      │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ patient_id (PK) │     │ appoint_id (PK) │     │ doctor_id (PK)  │
│ name            │◄───►│ patient_id (FK) │     │ name            │
│ age             │     │ doctor_id (FK)  │◄───►│ specialty       │
│ gender          │     │ date            │     │ phone           │
│ phone           │     │ time            │     │ available       │
│ address         │     │ status          │     └─────────────────┘
│ reg_date        │     └─────────────────┘
└─────────────────┘              │
        │                        │
        │                        ▼
        │               ┌─────────────────┐     ┌─────────────────┐
        │               │      BILL       │     │  PRESCRIPTION   │
        │               ├─────────────────┤     ├─────────────────┤
        └──────────────►│ bill_id (PK)    │     │ presc_id (PK)   │
                        │ patient_id (FK) │     │ patient_id (FK) │
                        │ amount          │     │ doctor_id (FK)  │
                        │ date            │     │ medicine        │
                        │ status          │     │ dosage          │
                        └─────────────────┘     │ date            │
                                                └─────────────────┘
```

---
Created for University Programming Assignment CA 2 Haruna and Pooja

