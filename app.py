from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Patient, Doctor, Appointment, Bill, Prescription
from datetime import datetime
import os
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hospital-secret-key-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:root@localhost/hospital_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def init_database():
    db.create_all()
    if User.query.first():
        return
    
    users = [
        User(username='admin', password=generate_password_hash('admin123'), role='admin'),
        User(username='reception', password=generate_password_hash('reception123'), role='receptionist')
    ]
    for user in users:
        db.session.add(user)
    
    doctors = [
        Doctor(name='Dr. Peter Anderson', specialty='General Medicine', phone='555-0101', available=True),
        Doctor(name='Dr. Pete Johnson', specialty='Cardiology', phone='555-0102', available=True),
        Doctor(name='Dr. Qudus Brown', specialty='Pediatrics', phone='555-0103', available=True),
    ]
    for doctor in doctors:
        db.session.add(doctor)
    db.session.commit()
    
    doctor_user = User(username='doctor', password=generate_password_hash('doctor123'), role='doctor', doctor_id=1)
    db.session.add(doctor_user)
    
    patients = [
        Patient(name='Alice Williams', age=35, gender='Female', phone='555-1001', address='123 Main St'),
        Patient(name='Bob Martinez', age=45, gender='Male', phone='555-1002', address='456 Oak Ave'),
    ]
    for patient in patients:
        db.session.add(patient)
    db.session.commit()

with app.app_context():
    for attempt in range(5):
        try:
            init_database()
            break
        except Exception as e:
            if attempt < 4:
                time.sleep(3)
            else:
                print(f"Could not initialize database: {e}")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    stats = {
        'doctors': Doctor.query.count(),
        'patients': Patient.query.count()
    }
    doctors = Doctor.query.limit(4).all()
    return render_template('home.html', stats=stats, doctors=doctors)

@app.route('/app')
def app_index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'patients': Patient.query.count(),
        'doctors': Doctor.query.count(),
        'appointments': Appointment.query.filter_by(status='scheduled').count(),
        'bills_pending': Bill.query.filter_by(status='pending').count()
    }
    return render_template('dashboard.html', stats=stats)

@app.route('/patients')
@login_required
def patients():
    search = request.args.get('search', '')
    if search:
        patients_list = Patient.query.filter(
            (Patient.name.ilike(f'%{search}%')) | 
            (Patient.patient_id == search if search.isdigit() else False)
        ).all()
    else:
        patients_list = Patient.query.all()
    return render_template('patients.html', patients=patients_list, search=search)

@app.route('/patients/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        patient = Patient(
            name=request.form['name'],
            age=int(request.form['age']),
            gender=request.form['gender'],
            phone=request.form['phone'],
            address=request.form['address']
        )
        db.session.add(patient)
        db.session.commit()
        flash('Patient registered successfully!', 'success')
        return redirect(url_for('patients'))
    return render_template('add_patient.html')

@app.route('/patients/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    patient = Patient.query.get_or_404(id)
    if request.method == 'POST':
        patient.name = request.form['name']
        patient.age = int(request.form['age'])
        patient.gender = request.form['gender']
        patient.phone = request.form['phone']
        patient.address = request.form['address']
        db.session.commit()
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('patients'))
    return render_template('edit_patient.html', patient=patient)

@app.route('/patients/delete/<int:id>')
@login_required
def delete_patient(id):
    patient = Patient.query.get_or_404(id)
    db.session.delete(patient)
    db.session.commit()
    flash('Patient deleted successfully!', 'success')
    return redirect(url_for('patients'))

@app.route('/patients/view/<int:id>')
@login_required
def view_patient(id):
    patient = Patient.query.get_or_404(id)
    return render_template('view_patient.html', patient=patient)

@app.route('/doctors')
@login_required
def doctors():
    doctors_list = Doctor.query.all()
    return render_template('doctors.html', doctors=doctors_list)

@app.route('/doctors/add', methods=['GET', 'POST'])
@login_required
def add_doctor():
    if current_user.role != 'admin':
        flash('Only admins can add doctors', 'error')
        return redirect(url_for('doctors'))
    
    if request.method == 'POST':
        doctor = Doctor(
            name=request.form['name'],
            specialty=request.form['specialty'],
            phone=request.form['phone'],
            available=True
        )
        db.session.add(doctor)
        db.session.commit()
        flash('Doctor added successfully!', 'success')
        return redirect(url_for('doctors'))
    return render_template('add_doctor.html')

@app.route('/doctors/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_doctor(id):
    if current_user.role != 'admin':
        flash('Only admins can edit doctors', 'error')
        return redirect(url_for('doctors'))
    
    doctor = Doctor.query.get_or_404(id)
    if request.method == 'POST':
        doctor.name = request.form['name']
        doctor.specialty = request.form['specialty']
        doctor.phone = request.form['phone']
        doctor.available = 'available' in request.form
        db.session.commit()
        flash('Doctor updated successfully!', 'success')
        return redirect(url_for('doctors'))
    return render_template('edit_doctor.html', doctor=doctor)

@app.route('/doctors/delete/<int:id>')
@login_required
def delete_doctor(id):
    if current_user.role != 'admin':
        flash('Only admins can delete doctors', 'error')
        return redirect(url_for('doctors'))
    
    doctor = Doctor.query.get_or_404(id)
    db.session.delete(doctor)
    db.session.commit()
    flash('Doctor deleted successfully!', 'success')
    return redirect(url_for('doctors'))

@app.route('/appointments')
@login_required
def appointments():
    if current_user.role == 'doctor' and current_user.doctor_id:
        appointments_list = Appointment.query.filter_by(doctor_id=current_user.doctor_id).order_by(Appointment.date.desc()).all()
    else:
        appointments_list = Appointment.query.order_by(Appointment.date.desc()).all()
    return render_template('appointments.html', appointments=appointments_list)

@app.route('/appointments/book', methods=['GET', 'POST'])
@login_required
def book_appointment():
    if request.method == 'POST':
        appointment = Appointment(
            patient_id=int(request.form['patient_id']),
            doctor_id=int(request.form['doctor_id']),
            date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
            time=request.form['time'],
            status='scheduled'
        )
        db.session.add(appointment)
        db.session.commit()
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('appointments'))
    
    patients_list = Patient.query.all()
    doctors_list = Doctor.query.filter_by(available=True).all()
    return render_template('book_appointment.html', patients=patients_list, doctors=doctors_list)

@app.route('/appointments/cancel/<int:id>')
@login_required
def cancel_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    appointment.status = 'cancelled'
    db.session.commit()
    flash('Appointment cancelled!', 'success')
    return redirect(url_for('appointments'))

@app.route('/appointments/complete/<int:id>')
@login_required
def complete_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    appointment.status = 'completed'
    db.session.commit()
    flash('Appointment marked as completed!', 'success')
    return redirect(url_for('appointments'))

@app.route('/bills')
@login_required
def bills():
    bills_list = Bill.query.order_by(Bill.date.desc()).all()
    return render_template('bills.html', bills=bills_list)

@app.route('/bills/generate', methods=['GET', 'POST'])
@login_required
def generate_bill():
    if request.method == 'POST':
        bill = Bill(
            patient_id=int(request.form['patient_id']),
            amount=float(request.form['amount']),
            status='pending'
        )
        db.session.add(bill)
        db.session.commit()
        flash('Bill generated successfully!', 'success')
        return redirect(url_for('bills'))
    
    patients_list = Patient.query.all()
    return render_template('generate_bill.html', patients=patients_list)

@app.route('/bills/pay/<int:id>')
@login_required
def pay_bill(id):
    bill = Bill.query.get_or_404(id)
    bill.status = 'paid'
    db.session.commit()
    flash('Bill marked as paid!', 'success')
    return redirect(url_for('bills'))

@app.route('/bills/receipt/<int:id>')
@login_required
def print_receipt(id):
    bill = Bill.query.get_or_404(id)
    return render_template('receipt.html', bill=bill)

@app.route('/prescriptions')
@login_required
def prescriptions():
    if current_user.role == 'doctor' and current_user.doctor_id:
        prescriptions_list = Prescription.query.filter_by(doctor_id=current_user.doctor_id).order_by(Prescription.date.desc()).all()
    else:
        prescriptions_list = Prescription.query.order_by(Prescription.date.desc()).all()
    return render_template('prescriptions.html', prescriptions=prescriptions_list)

@app.route('/prescriptions/add', methods=['GET', 'POST'])
@login_required
def add_prescription():
    if request.method == 'POST':
        doctor_id = current_user.doctor_id if current_user.role == 'doctor' else int(request.form['doctor_id'])
        prescription = Prescription(
            patient_id=int(request.form['patient_id']),
            doctor_id=doctor_id,
            medicine=request.form['medicine'],
            dosage=request.form['dosage']
        )
        db.session.add(prescription)
        db.session.commit()
        flash('Prescription added successfully!', 'success')
        return redirect(url_for('prescriptions'))
    
    patients_list = Patient.query.all()
    doctors_list = Doctor.query.all()
    return render_template('add_prescription.html', patients=patients_list, doctors=doctors_list)

@app.route('/prescriptions/view/<int:id>')
@login_required
def view_prescription(id):
    prescription = Prescription.query.get_or_404(id)
    return render_template('view_prescription.html', prescription=prescription)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

