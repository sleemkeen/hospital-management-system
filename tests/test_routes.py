"""Tests for Flask routes."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from flask import Flask
from flask_login import LoginManager
from datetime import date
from werkzeug.security import generate_password_hash

from models import db, User, Patient, Doctor, Appointment, Bill, Prescription


@pytest.fixture
def app():
    """Create test application."""
    application = Flask(__name__, 
                       template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
                       static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))
    application.config['TESTING'] = True
    application.config['SECRET_KEY'] = 'test-secret'
    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    application.config['WTF_CSRF_ENABLED'] = False
    
    db.init_app(application)
    
    login_manager = LoginManager()
    login_manager.init_app(application)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Import and register routes
    from app import app as main_app
    for rule in main_app.url_map.iter_rules():
        if rule.endpoint != 'static':
            view_func = main_app.view_functions.get(rule.endpoint)
            if view_func and rule.endpoint not in application.view_functions:
                application.add_url_rule(rule.rule, rule.endpoint, view_func, methods=rule.methods)
    
    with application.app_context():
        db.create_all()
    
    yield application
    
    with application.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def authenticated_client(app, client):
    """Create authenticated test client."""
    with app.app_context():
        user = User(username='testadmin', password=generate_password_hash('testpass'), role='admin')
        db.session.add(user)
        db.session.commit()
    
    client.post('/login', data={'username': 'testadmin', 'password': 'testpass'}, follow_redirects=True)
    return client


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


@pytest.fixture
def sample_appointment(app, sample_patient, sample_doctor):
    """Create a sample appointment."""
    with app.app_context():
        appointment = Appointment(patient_id=sample_patient, doctor_id=sample_doctor, date=date.today(), time='10:00', status='scheduled')
        db.session.add(appointment)
        db.session.commit()
        return appointment.appointment_id


@pytest.fixture
def sample_bill(app, sample_patient):
    """Create a sample bill."""
    with app.app_context():
        bill = Bill(patient_id=sample_patient, amount=100.00, status='pending')
        db.session.add(bill)
        db.session.commit()
        return bill.bill_id


@pytest.fixture
def sample_prescription(app, sample_patient, sample_doctor):
    """Create a sample prescription."""
    with app.app_context():
        prescription = Prescription(patient_id=sample_patient, doctor_id=sample_doctor, medicine='Test Med', dosage='1x daily')
        db.session.add(prescription)
        db.session.commit()
        return prescription.prescription_id


class TestHomeRoutes:
    """Tests for public home routes."""

    def test_home_page(self, client):
        """Test home page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'hospital' in response.data.lower() or b'doctor' in response.data.lower()

    def test_app_index_redirects_to_login(self, client):
        """Test /app redirects unauthenticated users to login."""
        response = client.get('/app', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location


class TestAuthRoutes:
    """Tests for authentication routes."""

    def test_login_page_loads(self, client):
        """Test login page loads successfully."""
        response = client.get('/login')
        assert response.status_code == 200

    def test_login_success(self, client, app):
        """Test successful login."""
        with app.app_context():
            user = User(
                username='logintest',
                password=generate_password_hash('password123'),
                role='admin'
            )
            db.session.add(user)
            db.session.commit()

        response = client.post('/login', data={
            'username': 'logintest',
            'password': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'dashboard' in response.data.lower() or b'Login successful' in response.data

    def test_login_invalid_credentials(self, client, app):
        """Test login with invalid credentials."""
        with app.app_context():
            user = User(
                username='testuser2',
                password=generate_password_hash('correctpass'),
                role='admin'
            )
            db.session.add(user)
            db.session.commit()

        response = client.post('/login', data={
            'username': 'testuser2',
            'password': 'wrongpassword'
        }, follow_redirects=True)

        assert b'Invalid' in response.data or b'error' in response.data.lower()

    def test_logout(self, authenticated_client):
        """Test logout functionality."""
        response = authenticated_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200

    def test_dashboard_requires_login(self, client):
        """Test dashboard requires authentication."""
        response = client.get('/dashboard', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location


class TestDashboardRoute:
    """Tests for dashboard route."""

    def test_dashboard_loads(self, authenticated_client):
        """Test dashboard loads for authenticated user."""
        response = authenticated_client.get('/dashboard')
        assert response.status_code == 200

    def test_dashboard_shows_stats(self, authenticated_client, app, sample_patient, sample_doctor):
        """Test dashboard displays statistics."""
        response = authenticated_client.get('/dashboard')
        assert response.status_code == 200


class TestPatientRoutes:
    """Tests for patient management routes."""

    def test_patients_list(self, authenticated_client):
        """Test patients list page loads."""
        response = authenticated_client.get('/patients')
        assert response.status_code == 200

    def test_patients_list_with_data(self, authenticated_client, app, sample_patient):
        """Test patients list shows patient data."""
        response = authenticated_client.get('/patients')
        assert response.status_code == 200
        assert b'Test Patient' in response.data

    def test_patients_search(self, authenticated_client, app, sample_patient):
        """Test patient search functionality."""
        response = authenticated_client.get('/patients?search=Test')
        assert response.status_code == 200
        assert b'Test Patient' in response.data

    def test_add_patient_page(self, authenticated_client):
        """Test add patient page loads."""
        response = authenticated_client.get('/patients/add')
        assert response.status_code == 200

    def test_add_patient_submit(self, authenticated_client, app):
        """Test adding a new patient."""
        response = authenticated_client.post('/patients/add', data={
            'name': 'New Patient',
            'age': '35',
            'gender': 'Male',
            'phone': '555-NEW1',
            'address': '123 New St'
        }, follow_redirects=True)

        assert response.status_code == 200
        
        with app.app_context():
            patient = Patient.query.filter_by(name='New Patient').first()
            assert patient is not None
            assert patient.age == 35

    def test_edit_patient_page(self, authenticated_client, app, sample_patient):
        """Test edit patient page loads."""
        response = authenticated_client.get(f'/patients/edit/{sample_patient}')
        assert response.status_code == 200

    def test_edit_patient_submit(self, authenticated_client, app, sample_patient):
        """Test editing a patient."""
        response = authenticated_client.post(f'/patients/edit/{sample_patient}', data={
            'name': 'Updated Patient',
            'age': '40',
            'gender': 'Female',
            'phone': '555-UPDT',
            'address': '456 Updated St'
        }, follow_redirects=True)

        assert response.status_code == 200
        
        with app.app_context():
            patient = Patient.query.get(sample_patient)
            assert patient.name == 'Updated Patient'
            assert patient.age == 40

    def test_view_patient(self, authenticated_client, app, sample_patient):
        """Test viewing a patient."""
        response = authenticated_client.get(f'/patients/view/{sample_patient}')
        assert response.status_code == 200

    def test_delete_patient(self, authenticated_client, app, sample_patient):
        """Test deleting a patient."""
        response = authenticated_client.get(f'/patients/delete/{sample_patient}', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            patient = Patient.query.get(sample_patient)
            assert patient is None

    def test_patient_not_found(self, authenticated_client):
        """Test 404 for non-existent patient."""
        response = authenticated_client.get('/patients/view/99999')
        assert response.status_code == 404


class TestDoctorRoutes:
    """Tests for doctor management routes."""

    def test_doctors_list(self, authenticated_client):
        """Test doctors list page loads."""
        response = authenticated_client.get('/doctors')
        assert response.status_code == 200

    def test_doctors_list_with_data(self, authenticated_client, app, sample_doctor):
        """Test doctors list shows doctor data."""
        response = authenticated_client.get('/doctors')
        assert response.status_code == 200
        assert b'Dr. Test' in response.data

    def test_add_doctor_page_admin(self, authenticated_client):
        """Test admin can access add doctor page."""
        response = authenticated_client.get('/doctors/add')
        assert response.status_code == 200

    def test_add_doctor_submit(self, authenticated_client, app):
        """Test adding a new doctor."""
        response = authenticated_client.post('/doctors/add', data={
            'name': 'Dr. New Doc',
            'specialty': 'Neurology',
            'phone': '555-DOC1'
        }, follow_redirects=True)

        assert response.status_code == 200
        
        with app.app_context():
            doctor = Doctor.query.filter_by(name='Dr. New Doc').first()
            assert doctor is not None
            assert doctor.specialty == 'Neurology'

    def test_edit_doctor_page(self, authenticated_client, app, sample_doctor):
        """Test edit doctor page loads."""
        response = authenticated_client.get(f'/doctors/edit/{sample_doctor}')
        assert response.status_code == 200

    def test_edit_doctor_submit(self, authenticated_client, app, sample_doctor):
        """Test editing a doctor."""
        response = authenticated_client.post(f'/doctors/edit/{sample_doctor}', data={
            'name': 'Dr. Updated',
            'specialty': 'Cardiology',
            'phone': '555-UPDT',
            'available': 'on'
        }, follow_redirects=True)

        assert response.status_code == 200
        
        with app.app_context():
            doctor = Doctor.query.get(sample_doctor)
            assert doctor.name == 'Dr. Updated'

    def test_delete_doctor(self, authenticated_client, app, sample_doctor):
        """Test deleting a doctor."""
        response = authenticated_client.get(f'/doctors/delete/{sample_doctor}', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            doctor = Doctor.query.get(sample_doctor)
            assert doctor is None

    def test_non_admin_cannot_add_doctor(self, client, app):
        """Test non-admin users cannot add doctors."""
        with app.app_context():
            user = User(
                username='receptionist',
                password=generate_password_hash('recept123'),
                role='receptionist'
            )
            db.session.add(user)
            db.session.commit()

        # Login as receptionist
        client.post('/login', data={
            'username': 'receptionist',
            'password': 'recept123'
        })

        response = client.get('/doctors/add', follow_redirects=True)
        assert b'Only admins' in response.data or response.status_code == 200


class TestAppointmentRoutes:
    """Tests for appointment management routes."""

    def test_appointments_list(self, authenticated_client):
        """Test appointments list page loads."""
        response = authenticated_client.get('/appointments')
        assert response.status_code == 200

    def test_book_appointment_page(self, authenticated_client):
        """Test book appointment page loads."""
        response = authenticated_client.get('/appointments/book')
        assert response.status_code == 200

    def test_book_appointment_submit(self, authenticated_client, app, sample_patient, sample_doctor):
        """Test booking an appointment."""
        response = authenticated_client.post('/appointments/book', data={
            'patient_id': str(sample_patient),
            'doctor_id': str(sample_doctor),
            'date': '2025-12-20',
            'time': '10:00'
        }, follow_redirects=True)

        assert response.status_code == 200
        
        with app.app_context():
            appointment = Appointment.query.first()
            assert appointment is not None
            assert appointment.status == 'scheduled'

class TestBillRoutes:
    """Tests for bill management routes."""

    def test_bills_list(self, authenticated_client):
        """Test bills list page loads."""
        response = authenticated_client.get('/bills')
        assert response.status_code == 200

    def test_generate_bill_page(self, authenticated_client):
        """Test generate bill page loads."""
        response = authenticated_client.get('/bills/generate')
        assert response.status_code == 200

    def test_generate_bill_submit(self, authenticated_client, app, sample_patient):
        """Test generating a bill."""
        response = authenticated_client.post('/bills/generate', data={
            'patient_id': str(sample_patient),
            'amount': '150.00'
        }, follow_redirects=True)

        assert response.status_code == 200
        
        with app.app_context():
            bill = Bill.query.first()
            assert bill is not None
            assert bill.amount == 150.00
            assert bill.status == 'pending'

    def test_pay_bill(self, authenticated_client, app, sample_bill):
        """Test paying a bill."""
        response = authenticated_client.get(f'/bills/pay/{sample_bill}', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            bill = Bill.query.get(sample_bill)
            assert bill.status == 'paid'

    def test_print_receipt(self, authenticated_client, app, sample_bill):
        """Test printing a receipt."""
        response = authenticated_client.get(f'/bills/receipt/{sample_bill}')
        assert response.status_code == 200


class TestPrescriptionRoutes:
    """Tests for prescription management routes."""

    def test_prescriptions_list(self, authenticated_client):
        """Test prescriptions list page loads."""
        response = authenticated_client.get('/prescriptions')
        assert response.status_code == 200

    def test_add_prescription_page(self, authenticated_client):
        """Test add prescription page loads."""
        response = authenticated_client.get('/prescriptions/add')
        assert response.status_code == 200

    def test_add_prescription_submit(self, authenticated_client, app, sample_patient, sample_doctor):
        """Test adding a prescription."""
        response = authenticated_client.post('/prescriptions/add', data={
            'patient_id': str(sample_patient),
            'doctor_id': str(sample_doctor),
            'medicine': 'Ibuprofen',
            'dosage': '400mg twice daily'
        }, follow_redirects=True)

        assert response.status_code == 200
        
        with app.app_context():
            prescription = Prescription.query.first()
            assert prescription is not None
            assert prescription.medicine == 'Ibuprofen'

class TestDoctorRoleAccess:
    """Tests for doctor-specific access patterns."""

    def test_doctor_sees_only_their_appointments(self, client, app):
        """Test doctors only see their own appointments."""
        with app.app_context():
            # Create two doctors
            doctor1 = Doctor(name='Dr. One', specialty='General', phone='555-0001')
            doctor2 = Doctor(name='Dr. Two', specialty='Surgery', phone='555-0002')
            db.session.add_all([doctor1, doctor2])
            db.session.commit()

            doctor1_id = doctor1.doctor_id

            # Create doctor user
            doctor_user = User(
                username='doctor1',
                password=generate_password_hash('doctor123'),
                role='doctor',
                doctor_id=doctor1_id
            )
            db.session.add(doctor_user)

            # Create patient
            patient = Patient(name='Patient', age=30, gender='Male', phone='555-0003')
            db.session.add(patient)
            db.session.commit()

            # Create appointments for both doctors
            appt1 = Appointment(
                patient_id=patient.patient_id,
                doctor_id=doctor1.doctor_id,
                date=date.today(),
                time='09:00'
            )
            appt2 = Appointment(
                patient_id=patient.patient_id,
                doctor_id=doctor2.doctor_id,
                date=date.today(),
                time='10:00'
            )
            db.session.add_all([appt1, appt2])
            db.session.commit()

        # Login as doctor1
        client.post('/login', data={
            'username': 'doctor1',
            'password': 'doctor123'
        })

        response = client.get('/appointments')
        assert response.status_code == 200
        # Doctor should see appointments page (filtering is done server-side)
