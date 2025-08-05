from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
from random import uniform
from time import sleep
# import joblib  # Optional, for ML model
from models import *

app = Flask(__name__)

# ✅ Enhanced CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

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
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

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
    print(f"{current} got it!  letsgoooooo ")
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
            remaining = max(0, term.budget - spent)
            
            return jsonify({
                "message": "Budget updated successfully",
                "budget": float(term.budget),
                "spent": spent,
                "remaining": remaining,
                "over_budget": spent > term.budget
            })
        except (ValueError, TypeError) as e:
            return jsonify({"error": f"Invalid budget value: {str(e)}"}), 400

    # GET request - return current budget status
    spent = db.session.query(db.func.sum(PowerData.power)).filter_by(term_id=term.id).scalar() or 0.0
    spent = float(spent)
    budget = float(term.budget) if term.budget else 0.0
    remaining = max(0, budget - spent)
    
    return jsonify({
        "budget": budget,
        "spent": spent,
        "remaining": remaining,
        "over_budget": spent > budget if budget > 0 else False
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
            return jsonify({
                "message": "Login successful", 
                "user_id": user.id,
                "username": user.username
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
            "current": float(a.current) if a.current else 0,
            "power": float(a.power) if a.power else 0,
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