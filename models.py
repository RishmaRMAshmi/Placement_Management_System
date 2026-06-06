from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db=SQLAlchemy()

# USERS 

class Admin(UserMixin, db.Model):
    id=db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(100), unique=True)
    password=db.Column(db.String(200))


class Student(UserMixin, db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(100))
    email=db.Column(db.String(100), unique=True)
    password=db.Column(db.String(200))
    department=db.Column(db.String(100))
    contact=db.Column(db.String(20))
    cgpa=db.Column(db.Float)
    resume=db.Column(db.String(200))
    active=db.Column(db.Boolean, default=True)

    applications=db.relationship('Application', backref='student', lazy=True)


class Company(UserMixin, db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(100))
    email=db.Column(db.String(100), unique=True)
    password=db.Column(db.String(200))
    website=db.Column(db.String(255))
    location=db.Column(db.String(100))
    hr_contact=db.Column(db.String(100))
    approved=db.Column(db.Boolean, default=False)
    active=db.Column(db.Boolean, default=True)

    drives=db.relationship('Drive', backref='company', lazy=True)


#DRIVES CREATED BY COMPANY

class Drive(db.Model):
    id=db.Column(db.Integer, primary_key=True)

    role=db.Column(db.String(100))
    eligibility=db.Column(db.Text)
    ctc=db.Column(db.String(50))
    deadline=db.Column(db.Date)
    description=db.Column(db.Text)
    approved=db.Column(db.Boolean, default=False)
    closed=db.Column(db.Boolean, default=False)

    company_id=db.Column(db.Integer, db.ForeignKey('company.id'))

    applications=db.relationship('Application', backref='drive', lazy=True)


# APPLICATIONS FROM STUDENTS


class Application(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    status=db.Column(db.String(50), default="Applied")
    applied_on=db.Column(db.DateTime, default=datetime.utcnow)

    student_id=db.Column(db.Integer, db.ForeignKey('student.id'))
    drive_id=db.Column(db.Integer, db.ForeignKey('drive.id'))