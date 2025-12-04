from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User table for login system"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, doctor, receptionist
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=True)
    
    doctor = db.relationship('Doctor', backref='user', uselist=False)

