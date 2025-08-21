from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
from random import uniform
from time import sleep
import joblib  # Optional, for ML model
from services.email_service import send_html_email
from models import *
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

app = Flask(__name__)
app.secret_key = "your_secret_key"
# ✅ Enhanced CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
user_email_global = None
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

# Add OPTIONS handler for CORS preflight requests
from services.email_service import send_html_email
from flask import Flask, jsonify, request, render_template
try:
    model = joblib.load("theft_model.pkl")
    print("ML Model loaded")
except Exception as e:
    model = None
    print("Error in loading model:",e)
 
@app.route("/send-email", methods=["POST"])
def send_email():
   subject = request.json.get("subject")
   body = request.json.get("body")
   address = request.json.get("address")
   msg_email = render_template("registration.html")
   send_html_email.delay(msg_email,address, subject,"orenjagidraf@gmail.com")
   
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response
dic = {"current_key": 0, "power_key": 0}
@app.route('/api/data', methods=['POST'])
def receive_data():
    data = request.get_json()
    current = data.get("current")
    power = data.get("power")

    term = Term.query.filter_by(is_active=True).first()
    if not term:
        return jsonify({"error": "No active term."}), 400

    entry = PowerData(term_id=term.id, current=current, power=power)
    dic["current_key"]=current
    dic["power_key"]=power
    db.session.add(entry)
    db.session.commit()
    
    #ml part
    now = datetime.now()
    hour_of_day = now.hour
    day_of_week=now.weekday()
    is_weekend = 1 if day_of_week >= 5 else 0
    print(f"{current} got it!  letsgoooooo ")
    features = np.array([[current, power, hour_of_day, day_of_week, is_weekend]])
    theft = False # Replace this with real model logic if needed
    if model:
        prediction = model.predict(features)
        print("Model prediction done !!")
        theft = bool(prediction[0]) 

    if theft:
        alert = TheftAlert(term_id=term.id, current=current, power=power,message="possible threat!!")
        db.session.add(alert)
        db.session.commit()
        print("Theft alert created!")
        if user_email_global:
            print("Sending theft alert email to:", user_email_global)
            send_html_email("Theft detected! Take care", user_email_global, "theft", "gamerocker1002@gmail.com")
        return jsonify({"status": "data received", "theft": True}), 200

    return jsonify({"status": "data received", "theft": False}), 200

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    term = Term.query.filter_by(is_active=True).first()
    if not term:
        return jsonify([])

    # Get query parameters for filtering
    period = request.args.get('period', 'all')  # 'week', 'month', or 'all'
    
    # Base query
    query = PowerData.query.filter_by(term_id=term.id)
    
    # Apply date filtering based on period
    if period == 'week':
        week_ago = datetime.utcnow() - timedelta(days=7)
        query = query.filter(PowerData.timestamp >= week_ago)
    elif period == 'month':
        month_ago = datetime.utcnow() - timedelta(days=30)
        query = query.filter(PowerData.timestamp >= month_ago)
    
    # Order by timestamp
    data = query.order_by(PowerData.timestamp.asc()).all()
    
    return jsonify([
        {
            "timestamp": d.timestamp.isoformat(), 
            "current": float(d.current) if d.current else 0, 
            "power": float(d.power) if d.power else 0
        }
        for d in data
    ])

# ✅ ADD MISSING HEATMAP ENDPOINT
@app.route('/api/heatmap', methods=['GET'])
def get_heatmap():
    term = Term.query.filter_by(is_active=True).first()
    if not term:
        return jsonify([0.0] * 24)  # Return zeros if no active term

    # Get data from last 7 days for heatmap
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    data = PowerData.query.filter_by(term_id=term.id)\
                          .filter(PowerData.timestamp >= cutoff_date)\
                          .all()

    # Initialize hourly data (24 hours)
    hourly_data = [0.0] * 24
    hourly_counts = [0] * 24

    # Aggregate power by hour
    for entry in data:
        hour = entry.timestamp.hour
        hourly_data[hour] += float(entry.power) if entry.power else 0
        hourly_counts[hour] += 1

    # Calculate average power per hour
    heatmap_data = []
    for i in range(24):
        if hourly_counts[i] > 0:
            avg_power = hourly_data[i] / hourly_counts[i]
            heatmap_data.append(round(avg_power, 2))
        else:
            heatmap_data.append(0.0)

    return jsonify(heatmap_data)

# ✅ NEW ENDPOINT FOR CURRENT READING (DASHBOARD)
@app.route('/api/current-reading', methods=['GET'])
def get_current_reading():
    """Get the latest power and current reading for dashboard display"""
    term = Term.query.filter_by(is_active=True).first()
    if not term:
        return jsonify({
            "current": 0,
            "power": 0,
            "timestamp": None
        })

    # Get the most recent power data entry
    latest_entry = PowerData.query.filter_by(term_id=term.id)\
                                  .order_by(PowerData.timestamp.desc())\
                                  .first()
    
    if not latest_entry:
        return jsonify({
            "current": 0,
            "power": 0,
            "timestamp": None
        })

    return jsonify({
        "current": float(latest_entry.current) if latest_entry.current else 0,
        "power": float(latest_entry.power) if latest_entry.power else 0,
        "timestamp": latest_entry.timestamp.isoformat()
    })

# Only the budget_monitor function with fixes - replace in your app.py

@app.route('/api/budget', methods=['GET', 'POST'])
def budget_monitor():
    term = Term.query.filter_by(is_active=True).first()
    if not term:
        return jsonify({"error": "No active term."}), 400

    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        budget_value = data.get("budget")
        if budget_value is None:
            return jsonify({"error": "Budget value is required"}), 400
        
        try:
            term.budget = float(budget_value)
            db.session.commit()
            
            # Calculate spent amount
            spent = db.session.query(db.func.sum(PowerData.power)).filter_by(term_id=term.id).scalar() or 0.0
            spent = float(spent)
            # Calculate remaining bill (what user owes)
            remaining_bill = max(0, spent - term.paid_amount)
            
            return jsonify({
                "message": "Budget updated successfully",
                "budget": float(term.budget),
                "spent": spent,
                "paid_amount": float(term.paid_amount),
                "remaining": remaining_bill,  # ✅ Fixed: remaining bill, not budget remaining
                "over_budget": (spent - term.paid_amount) > term.budget
            })
        except (ValueError, TypeError) as e:
            return jsonify({"error": f"Invalid budget value: {str(e)}"}), 400

    # GET request - return current budget status
    spent = db.session.query(db.func.sum(PowerData.power)).filter_by(term_id=term.id).scalar() or 0.0
    spent = float(spent)
    budget = float(term.budget) if term.budget else 0.0
    paid_amount = float(term.paid_amount)
    # ✅ Fixed: remaining_bill is what user owes, not budget remaining
    remaining_bill = max(0, spent - paid_amount)
    
    # Only create alerts if budget is set and remaining is 0 or negative
    if budget > 0 and remaining_bill <= 0:
        actual = spent - paid_amount
        
        if actual == 0:
            # Check if "Budget completed" alert already exists for this term
            existing_alert = TheftAlert.query.filter_by(
                term_id=term.id, 
                message="Budget completed!! 0$ left"
            ).first()
            
            if not existing_alert:
                alert = TheftAlert(
                    term_id=term.id, 
                    current=dic["current_key"], 
                    power=dic["power_key"],
                    message="Budget completed!! 0$ left"
                )
                db.session.add(alert)
                db.session.commit()
                
        elif actual < 0:
            over_amount = (-1) * actual
            message = f"spending over budget!! {over_amount}$ over"
            if user_email_global:
                print("Sending theft alert email to:", user_email_global)
                send_html_email(f"spending over budget by {over_amount}", user_email_global, "theft", "gamerocker1002@gmail.com")
            # Check if similar "over budget" alert already exists for this term
            existing_alert = TheftAlert.query.filter_by(term_id=term.id)\
                .filter(TheftAlert.message.like("spending over budget!!%"))\
                .first()
            
            if not existing_alert:
                alert = TheftAlert(
                    term_id=term.id, 
                    current=dic["current_key"], 
                    power=dic["power_key"],
                    message=message
                )
                db.session.add(alert)
                db.session.commit()
            else:
                # Update existing alert with new over-budget amount
                existing_alert.message = message
                existing_alert.timestamp = datetime.utcnow()  # Update timestamp
                existing_alert.current = dic["current_key"]
                existing_alert.power = dic["power_key"]
                db.session.commit()

    # ✅ Fixed: Return correct values
    return jsonify({
        "budget": budget,
        "spent": spent,
        "paid_amount": paid_amount,
        "remaining": remaining_bill,  # This is the remaining bill amount
        "over_budget": (spent - paid_amount) > budget if budget > 0 else False
    })

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 400
        
        # In production, hash the password properly
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    global user_email_global
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            user_email_global = user.username   # ✅ treat username field as email
            return jsonify({
                "message": "Login successful", 
                "user_id": user.id,
                "email": user.username
            }), 200
        
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


@app.route('/api/alerts', methods=['GET', 'POST'])
def manage_alerts():
    term = Term.query.filter_by(is_active=True).first()
    if not term:
        return jsonify([])

    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        alert_id = data.get("alert_id")
        feed=data.get("feedback")
        alert = TheftAlert.query.get(alert_id)
        print(f"{feed}")
        if alert:
            # 1️⃣ Mark ignored in DB
            alert.is_ignored = True
            db.session.commit()

            # 2️⃣ Run ML retraining whenever ignore happens
            timestamp = alert.timestamp
            dataset = "power_dataset.csv"

            try:
                df = pd.read_csv(dataset)
            except FileNotFoundError:
                df = pd.DataFrame(columns=[
                    "current","power","hour_of_day","day_of_week","is_weekend","label"
                ])
            label=0
            if feed == "accept":
                label=1
            else:
                label=0
            new_row = {
                "current": alert.current,
                "power": alert.power,
                "hour_of_day": timestamp.hour,
                "day_of_week": timestamp.weekday(),
                "is_weekend": 1 if timestamp.weekday() >= 5 else 0,
                "label": label  # 👈 ignoring means "not theft"
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(dataset, index=False)

            if len(df) > 5:  # only retrain if some data exists
                X = df[["current","power","hour_of_day","day_of_week","is_weekend"]]
                y = df["label"]

                global model
                model = RandomForestClassifier(n_estimators=100, random_state=42)
                model.fit(X, y)
                joblib.dump(model, "theft_model.pkl")

                print("✅ Model retrained after ignoring alert")

            return jsonify({"message": "Alert ignored, model updated."})

    # GET request
    alerts = TheftAlert.query.filter_by(term_id=term.id).all()
    return jsonify([
        {
            "id": a.id,
            "timestamp": a.timestamp.isoformat(),
            "current": float(a.current) if a.current else 0,
            "power": float(a.power) if a.power else 0,
            "ignored": a.is_ignored,
            "message": a.message
        } for a in alerts
    ])

@app.route('/api/logout', methods=['POST'])
def logout():
    global user_email_global
    user_email_global = None
    return jsonify({"message": "Logout successful"}), 200


@app.route('/api/pay', methods=['POST'])
def pay():
    print("payment called")
    term = Term.query.filter_by(is_active=True).first()
    if not term:
        return jsonify({"error": "No active term."}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "No payment data provided"}), 400
    
    payment_amount = data.get("amount")
    if payment_amount is None or payment_amount <= 0:
        return jsonify({"error": "Valid payment amount is required"}), 400
    
    
    try:
        payment_amount = float(payment_amount)
        
        # Calculate current bill (spent - already paid)
        spent = db.session.query(db.func.sum(PowerData.power)).filter_by(term_id=term.id).scalar() or 0.0
        spent = float(spent)
        current_bill = spent - term.paid_amount
        
        if payment_amount > current_bill:
            return jsonify({
                "error": f"Payment amount (${payment_amount}) exceeds current bill (${current_bill})"
            }), 400
        
        # Add payment to paid_amount
        term.paid_amount += payment_amount
        
        # Check if bill is fully paid
        remaining_bill = current_bill - payment_amount
        
        if remaining_bill <= 0.01:  # Considering floating point precision
            # Bill fully paid - close current term and start new one
            term.bill_paid = True
            term.is_active = False
            term.end_date = datetime.utcnow()
            db.session.commit()
            
            # Create new term
            new_term = Term()
            db.session.add(new_term)
            db.session.commit()
            
            return jsonify({
                "message": "Bill fully paid. New term started.",
                "payment_amount": payment_amount,
                "total_paid": float(term.paid_amount),
                "remaining_bill": current_bill - float(term.paid_amount),
                "term_closed": True,
                "new_term_id": new_term.id
            })
        else:
            # Partial payment
            db.session.commit()
            
            return jsonify({
                "message": f"Partial payment of ${payment_amount} processed.",
                "payment_amount": payment_amount,
                "total_paid": float(term.paid_amount),
                "remaining_bill": remaining_bill,
                "term_closed": False
            })
            
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid payment amount: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Payment processing failed: {str(e)}"}), 500

@app.route('/api/fake_data', methods=['POST'])
def generate_fake_data():
    term = Term.query.filter_by(is_active=True).first()
    if not term:
        return jsonify({"error": "No active term found."}), 400

    data = request.get_json() or {}
    count = data.get("count", 100)  # Number of entries to create
    min_current = data.get("min_current", 1.0)
    max_current = data.get("max_current", 5.0)
    min_power = data.get("min_power", 100.0)
    max_power = data.get("max_power", 500.0)

    new_entries = []
    
    # Generate data spread over the last 30 days for better testing
    for i in range(count):
        # Random timestamp within last 30 days
        days_ago = uniform(0, 30)
        hours_ago = uniform(0, 24)
        timestamp = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)
        
        current = round(uniform(min_current, max_current), 2)
        power = round(uniform(min_power, max_power), 2)
        
        entry = PowerData(
            term_id=term.id, 
            current=current, 
            power=power,
            timestamp=timestamp  # Add custom timestamp
        )
        new_entries.append(entry)

    db.session.bulk_save_objects(new_entries)
    db.session.commit()

    return jsonify({"message": f"{count} fake entries added with spread timestamps."})

# ✅ ADD TEST ENDPOINT
@app.route('/api/test', methods=['GET'])
def test_endpoint():
    return jsonify({"message": "API is working!", "timestamp": datetime.utcnow().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


'''
    lsof -i :5000
    flask run --host=0.0.0.0 --port=5000

    brew services start redis
    redis-server
    brew services stop redis
    brew services restart redis
    brew services list
    celery -A services.email_service worker -l info --pool gevent


'''


