from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
# import joblib  # Optional, for ML model
from models import *

app = Flask(__name__)
CORS(app)

# ✅ Configuration BEFORE initializing anything
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///power_monitor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ Initialize DB with app
db.init_app(app)

# ✅ Now use app context to create tables
with app.app_context():
    db.create_all()
    if not Term.query.filter_by(is_active=True).first():
        db.session.add(Term())
        db.session.commit()


# --- Your routes stay unchanged below ---

@app.route('/api/data', methods=['POST'])
def receive_data():
    data = request.get_json()
    current = data.get("current")
    power = data.get("power")

    term = Term.query.filter_by(is_active=True).first()
    if not term:
        return jsonify({"error": "No active term."}), 400

    entry = PowerData(term_id=term.id, current=current, power=power)
    db.session.add(entry)
    db.session.commit()

    theft = False  # Replace this with real model logic if needed

    if theft:
        alert = TheftAlert(term_id=term.id, current=current, power=power)
        db.session.add(alert)
        db.session.commit()
        return jsonify({"status": "data received", "theft": True}), 200

    return jsonify({"status": "data received", "theft": False}), 200

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    term = Term.query.filter_by(is_active=True).first()
    if not term:
        return jsonify([])

    data = PowerData.query.filter_by(term_id=term.id).all()
    return jsonify([
        {"timestamp": d.timestamp.isoformat(), "current": d.current, "power": d.power}
        for d in data
    ])

@app.route('/api/budget', methods=['GET', 'POST'])
def budget_monitor():
    term = Term.query.filter_by(is_active=True).first()
    if not term:
        return jsonify({"error": "No active term."}), 400

    if request.method == 'POST':
        term.budget = request.json.get("budget")
        db.session.commit()
        return jsonify({"message": "Budget updated."})

    spent = db.session.query(db.func.sum(PowerData.power)).filter_by(term_id=term.id).scalar() or 0.0
    return jsonify({
        "budget": term.budget,
        "spent": spent,
        "remaining": max(0, term.budget - spent),
        "over_budget": spent > term.budget
    })

@app.route('/api/alerts', methods=['GET', 'POST'])
def manage_alerts():
    term = Term.query.filter_by(is_active=True).first()
    if not term:
        return jsonify([])

    if request.method == 'POST':
        alert_id = request.json.get("alert_id")
        alert = TheftAlert.query.get(alert_id)
        if alert:
            alert.is_ignored = True
            db.session.commit()
        return jsonify({"message": "Alert ignored."})

    alerts = TheftAlert.query.filter_by(term_id=term.id).all()
    return jsonify([
        {
            "id": a.id,
            "timestamp": a.timestamp.isoformat(),
            "current": a.current,
            "power": a.power,
            "ignored": a.is_ignored
        } for a in alerts
    ])

@app.route('/api/pay', methods=['POST'])
def pay_bill():
    term = Term.query.filter_by(is_active=True).first()
    if not term:
        return jsonify({"error": "No active term."}), 400

    term.bill_paid = True
    term.is_active = False
    db.session.commit()

    new_term = Term()
    db.session.add(new_term)
    db.session.commit()

    return jsonify({"message": "New term started."})

from random import uniform
from time import sleep

@app.route('/api/fake_data', methods=['POST'])
def generate_fake_data():
    term = Term.query.filter_by(is_active=True).first()
    if not term:
        return jsonify({"error": "No active term found."}), 400

    count = request.json.get("count", 100)  # Number of entries to create
    min_current = request.json.get("min_current", 1.0)
    max_current = request.json.get("max_current", 5.0)
    min_power = request.json.get("min_power", 100.0)
    max_power = request.json.get("max_power", 500.0)

    new_entries = []
    for _ in range(count):
        current = round(uniform(min_current, max_current), 2)
        power = round(uniform(min_power, max_power), 2)
        entry = PowerData(term_id=term.id, current=current, power=power)
        new_entries.append(entry)

    db.session.bulk_save_objects(new_entries)
    db.session.commit()

    return jsonify({"message": f"{count} fake entries added."})


if __name__ == '__main__':
    app.run(debug=True)
