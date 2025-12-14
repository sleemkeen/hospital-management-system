"""Tests for database models."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from flask import Flask
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Patient, Doctor, Appointment, Bill, Prescription


@pytest.fixture
def app():
    """Create test application."""
    application = Flask(__name__)
    application.config['TESTING'] = True
    application.config['SECRET_KEY'] = 'test-secret'
    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(application)
    
    with application.app_context():
        db.create_all()
    
    yield application
    
    with application.app_context():
        db.drop_all()


@pytest.fixture
def sample_doctor(app):
    """Create a sample doctor."""
    with app.app_context():
        doctor = Doctor(name='Dr. Test', specialty='General', phone='555-0001', available=True)
        db.session.add(doctor)
        db.session.commit()
        return doctor.doctor_id


@pytest.fixture
def sample_patient(app):
    """Create a sample patient."""
    with app.app_context():
        patient = Patient(name='Test Patient', age=30, gender='Male', phone='555-1234', address='123 Test St')
        db.session.add(patient)
        db.session.commit()
        return patient.patient_id


class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, app):
        """Test creating a new user."""
        with app.app_context():
            user = User(
                username='testuser',
                password=generate_password_hash('testpass'),
                role='admin'
            )
            db.session.add(user)
            db.session.commit()

            saved_user = User.query.filter_by(username='testuser').first()
            assert saved_user is not None
            assert saved_user.username == 'testuser'
            assert saved_user.role == 'admin'
            assert check_password_hash(saved_user.password, 'testpass')

    def test_user_is_authenticated(self, app):
        """Test UserMixin is_authenticated property."""
        with app.app_context():
            user = User(
                username='authuser',
                password=generate_password_hash('pass123'),
                role='receptionist'
            )
            db.session.add(user)
            db.session.commit()

            assert user.is_authenticated is True

    def test_user_with_doctor_relationship(self, app, sample_doctor):
        """Test user can be linked to a doctor."""
        with app.app_context():
            user = User(
                username='druser',
                password=generate_password_hash('drpass'),
                role='doctor',
                doctor_id=sample_doctor
            )
            db.session.add(user)
            db.session.commit()

            saved_user = User.query.filter_by(username='druser').first()
            assert saved_user.doctor is not None
            assert saved_user.doctor.name == 'Dr. Test'


class TestPatientModel:
    """Tests for the Patient model."""

    def test_create_patient(self, app):
        """Test creating a new patient."""
        with app.app_context():
            patient = Patient(
                name='John Doe',
                age=30,
                gender='Male',
                phone='555-1234',
                address='123 Test St'
            )
            db.session.add(patient)
            db.session.commit()

            saved = Patient.query.filter_by(name='John Doe').first()
            assert saved is not None
            assert saved.age == 30
            assert saved.gender == 'Male'
            assert saved.phone == '555-1234'

    def test_patient_reg_date_default(self, app):
        """Test patient registration date is set automatically."""
        with app.app_context():
            patient = Patient(
                name='Jane Doe',
                age=25,
                gender='Female',
                phone='555-5678'
            )
            db.session.add(patient)
            db.session.commit()

            assert patient.reg_date is not None
            assert isinstance(patient.reg_date, datetime)

    def test_patient_relationships(self, app, sample_patient, sample_doctor):
        """Test patient has relationships to appointments, bills, prescriptions."""
        with app.app_context():
            patient = Patient.query.get(sample_patient)
            doctor = Doctor.query.get(sample_doctor)

            # Create related records
            appointment = Appointment(
                patient_id=patient.patient_id,
                doctor_id=doctor.doctor_id,
                date=date.today(),
                time='10:00'
            )
            bill = Bill(
                patient_id=patient.patient_id,
                amount=100.00
            )
            prescription = Prescription(
                patient_id=patient.patient_id,
                doctor_id=doctor.doctor_id,
                medicine='Test Medicine',
                dosage='1 pill daily'
            )
            db.session.add_all([appointment, bill, prescription])
            db.session.commit()

            # Refresh patient
            patient = Patient.query.get(sample_patient)
            assert len(patient.appointments) == 1
            assert len(patient.bills) == 1
            assert len(patient.prescriptions) == 1


class TestDoctorModel:
    """Tests for the Doctor model."""

    def test_create_doctor(self, app):
        """Test creating a new doctor."""
        with app.app_context():
            doctor = Doctor(
                name='Dr. Test',
                specialty='Surgery',
                phone='555-9999',
                available=True
            )
            db.session.add(doctor)
            db.session.commit()

            saved = Doctor.query.filter_by(name='Dr. Test').first()
            assert saved is not None
            assert saved.specialty == 'Surgery'
            assert saved.available is True

    def test_doctor_availability_default(self, app):
        """Test doctor availability defaults to True."""
        with app.app_context():
            doctor = Doctor(
                name='Dr. Default',
                specialty='General',
                phone='555-0000'
            )
            db.session.add(doctor)
            db.session.commit()

            assert doctor.available is True

    def test_doctor_relationships(self, app, sample_doctor, sample_patient):
        """Test doctor has relationships to appointments and prescriptions."""
        with app.app_context():
            doctor = Doctor.query.get(sample_doctor)
            patient = Patient.query.get(sample_patient)

            appointment = Appointment(
                patient_id=patient.patient_id,
                doctor_id=doctor.doctor_id,
                date=date.today(),
                time='14:00'
            )
            prescription = Prescription(
                patient_id=patient.patient_id,
                doctor_id=doctor.doctor_id,
                medicine='Medicine',
                dosage='2x daily'
            )
            db.session.add_all([appointment, prescription])
            db.session.commit()

            doctor = Doctor.query.get(sample_doctor)
            assert len(doctor.appointments) == 1
            assert len(doctor.prescriptions) == 1


class TestAppointmentModel:
    """Tests for the Appointment model."""

    def test_create_appointment(self, app, sample_patient, sample_doctor):
        """Test creating an appointment."""
        with app.app_context():
            appointment = Appointment(
                patient_id=sample_patient,
                doctor_id=sample_doctor,
                date=date(2025, 12, 20),
                time='09:00',
                status='scheduled'
            )
            db.session.add(appointment)
            db.session.commit()

            saved = Appointment.query.first()
            assert saved is not None
            assert saved.status == 'scheduled'
            assert saved.patient.name == 'Test Patient'
            assert saved.doctor.name == 'Dr. Test'

    def test_appointment_status_default(self, app, sample_patient, sample_doctor):
        """Test appointment status defaults to scheduled."""
        with app.app_context():
            appointment = Appointment(
                patient_id=sample_patient,
                doctor_id=sample_doctor,
                date=date.today(),
                time='11:00'
            )
            db.session.add(appointment)
            db.session.commit()

            assert appointment.status == 'scheduled'


class TestBillModel:
    """Tests for the Bill model."""

    def test_create_bill(self, app, sample_patient):
        """Test creating a bill."""
        with app.app_context():
            bill = Bill(
                patient_id=sample_patient,
                amount=250.50,
                status='pending'
            )
            db.session.add(bill)
            db.session.commit()

            saved = Bill.query.first()
            assert saved is not None
            assert saved.amount == 250.50
            assert saved.status == 'pending'

    def test_bill_date_default(self, app, sample_patient):
        """Test bill date is set automatically."""
        with app.app_context():
            bill = Bill(
                patient_id=sample_patient,
                amount=100.00
            )
            db.session.add(bill)
            db.session.commit()

            assert bill.date is not None
            assert isinstance(bill.date, datetime)

    def test_bill_status_default(self, app, sample_patient):
        """Test bill status defaults to pending."""
        with app.app_context():
            bill = Bill(
                patient_id=sample_patient,
                amount=75.00
            )
            db.session.add(bill)
            db.session.commit()

            assert bill.status == 'pending'


class TestPrescriptionModel:
    """Tests for the Prescription model."""

    def test_create_prescription(self, app, sample_patient, sample_doctor):
        """Test creating a prescription."""
        with app.app_context():
            prescription = Prescription(
                patient_id=sample_patient,
                doctor_id=sample_doctor,
                medicine='Amoxicillin',
                dosage='500mg 3x daily for 7 days'
            )
            db.session.add(prescription)
            db.session.commit()

            saved = Prescription.query.first()
            assert saved is not None
            assert saved.medicine == 'Amoxicillin'
            assert saved.dosage == '500mg 3x daily for 7 days'

    def test_prescription_date_default(self, app, sample_patient, sample_doctor):
        """Test prescription date is set automatically."""
        with app.app_context():
            prescription = Prescription(
                patient_id=sample_patient,
                doctor_id=sample_doctor,
                medicine='Test Med',
                dosage='1x daily'
            )
            db.session.add(prescription)
            db.session.commit()

            assert prescription.date is not None
            assert isinstance(prescription.date, datetime)

    def test_prescription_relationships(self, app, sample_patient, sample_doctor):
        """Test prescription backrefs to patient and doctor."""
        with app.app_context():
            prescription = Prescription(
                patient_id=sample_patient,
                doctor_id=sample_doctor,
                medicine='Medicine',
                dosage='As needed'
            )
            db.session.add(prescription)
            db.session.commit()

            saved = Prescription.query.first()
            assert saved.patient.name == 'Test Patient'
            assert saved.doctor.name == 'Dr. Test'
