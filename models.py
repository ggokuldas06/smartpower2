from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  # hashed

class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    budget = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)  # New field for partial payments
    is_active = db.Column(db.Boolean, default=True)
    bill_paid = db.Column(db.Boolean, default=False)

class PowerData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    current = db.Column(db.Float)
    power = db.Column(db.Float)

class TheftAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    power = db.Column(db.Float)
    current = db.Column(db.Float)
    is_ignored = db.Column(db.Boolean, default=False)
    message= db.Column(db.String,nullable=True)