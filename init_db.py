"""
Database Initialization Script
Run this file to create the database and add sample data
"""

from app import app, db
from models import User, Patient, Doctor, Appointment, Bill, Prescription
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta

def init_database():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created")
        
        # Check if data already exists
        if User.query.first():
            print("! Database already contains data. Skipping initialization.")
            return
        
        # Create default users
        users = [
            User(
                username='admin',
                password=generate_password_hash('admin123'),
                role='admin'
            ),
            User(
                username='reception',
                password=generate_password_hash('reception123'),
                role='receptionist'
            )
        ]
        
        for user in users:
            db.session.add(user)
        print("✓ Default users created")
        
        # Create sample doctors
        doctors = [
            Doctor(name='Dr. John Smith', specialty='General Medicine', phone='555-0101', available=True),
            Doctor(name='Dr. Sarah Johnson', specialty='Cardiology', phone='555-0102', available=True),
            Doctor(name='Dr. Michael Brown', specialty='Pediatrics', phone='555-0103', available=True),
            Doctor(name='Dr. Emily Davis', specialty='Dermatology', phone='555-0104', available=True),
            Doctor(name='Dr. Robert Wilson', specialty='Orthopedics', phone='555-0105', available=False),
        ]
        
        for doctor in doctors:
            db.session.add(doctor)
        db.session.commit()
        print("✓ Sample doctors added")
        
        # Create doctor user account for Dr. John Smith
        doctor_user = User(
            username='doctor',
            password=generate_password_hash('doctor123'),
            role='doctor',
            doctor_id=1  # Link to Dr. John Smith
        )
        db.session.add(doctor_user)
        print("✓ Doctor user account created")
        
        # Create sample patients
        patients = [
            Patient(name='Alice Williams', age=35, gender='Female', phone='555-1001', address='123 Main St'),
            Patient(name='Bob Martinez', age=45, gender='Male', phone='555-1002', address='456 Oak Ave'),
            Patient(name='Carol Taylor', age=28, gender='Female', phone='555-1003', address='789 Pine Rd'),
            Patient(name='David Anderson', age=52, gender='Male', phone='555-1004', address='321 Elm Blvd'),
            Patient(name='Eva Thomas', age=8, gender='Female', phone='555-1005', address='654 Maple Dr'),
        ]
        
        for patient in patients:
            db.session.add(patient)
        db.session.commit()
        print("✓ Sample patients added")
        
        # Create sample appointments
        today = date.today()
        appointments = [
            Appointment(patient_id=1, doctor_id=1, date=today + timedelta(days=1), time='09:00', status='scheduled'),
            Appointment(patient_id=2, doctor_id=2, date=today + timedelta(days=1), time='10:00', status='scheduled'),
            Appointment(patient_id=3, doctor_id=1, date=today + timedelta(days=2), time='11:00', status='scheduled'),
            Appointment(patient_id=4, doctor_id=3, date=today - timedelta(days=1), time='14:00', status='completed'),
            Appointment(patient_id=5, doctor_id=3, date=today - timedelta(days=2), time='15:00', status='completed'),
        ]
        
        for apt in appointments:
            db.session.add(apt)
        db.session.commit()
        print("✓ Sample appointments added")
        
        # Create sample bills
        bills = [
            Bill(patient_id=4, amount=150.00, status='paid'),
            Bill(patient_id=5, amount=75.00, status='paid'),
            Bill(patient_id=1, amount=200.00, status='pending'),
            Bill(patient_id=2, amount=350.00, status='pending'),
        ]
        
        for bill in bills:
            db.session.add(bill)
        db.session.commit()
        print("✓ Sample bills added")
        
        # Create sample prescriptions
        prescriptions = [
            Prescription(
                patient_id=4, doctor_id=3,
                medicine='Amoxicillin 500mg, Ibuprofen 400mg',
                dosage='Amoxicillin: 1 tablet 3 times daily for 7 days\nIbuprofen: 1 tablet as needed for pain'
            ),
            Prescription(
                patient_id=5, doctor_id=3,
                medicine='Children\'s Tylenol',
                dosage='5ml every 6 hours as needed for fever'
            ),
        ]
        
        for presc in prescriptions:
            db.session.add(presc)
        db.session.commit()
        print("✓ Sample prescriptions added")
        
        print("\n" + "="*50)
        print("Database initialized successfully!")
        print("="*50)
        print("\nDefault Login Credentials:")
        print("-" * 30)
        print("Admin:        admin / admin123")
        print("Doctor:       doctor / doctor123")
        print("Receptionist: reception / reception123")
        print("-" * 30)
        print("\nRun 'python app.py' to start the server")

if __name__ == '__main__':
    init_database()

