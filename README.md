---
This README includes
- Project overview  
- Features  
- IoT hardware list  
- Workflow  
- Installation & setup (Mac + Windows)  
- Vue.js setup  
- ESP32 note  
- Alerts system  
- Future scope  

# ⚡ Smart Power Analytics System (AI + IoT)

## 📌 Overview  
In India, electricity bills are generated every **2 months**, which makes it difficult for households to track power consumption and budget their expenses in real time.  

This project provides an **AI + IoT based Smart Power Analytics System** that enables:  
- Real-time power consumption monitoring  
- Budget-based usage tracking & notifications  
- Online payment handling  
- Power theft detection using Machine Learning  

Built with **Flask (backend)**, **Vue.js (frontend)**, and **Random Forest Classifier (ML model)**.  

---

## 🚀 Features  
- 📊 **Power Analytics**  
  - Daily consumption tracking (units + cost)  
  - Estimated bill till date  
  - Budget monitor with real-time alerts  

- 💰 **Budget Monitoring & Payment**  
  - Set monthly/bi-monthly budgets  
  - Notifications if consumption exceeds budget  
  - Online partial/full payment option with balance tracking  

- 🔒 **Power Theft Detection**  
  - ML-based anomaly detection (Random Forest Classifier)  
  - Features include: time of day, weekend/holiday, seasonality, etc.  
  - Theft alerts sent via **email + dashboard alert tab**  
  - User can **Ignore** (mark as normal anomaly) or **Raise** (confirm theft)  
  - Model improves over time with feedback  

- 📡 **IoT Integration**  
  - ESP32 microcontroller + ACS712 current sensor  
  - Real-time data collection & transmission to backend  
  - Code for ESP32 is available inside the **`iot/`** folder  

---

## 🛠️ IoT Hardware Requirements  
- ESP32 (WiFi enabled)  
- ACS712 current sensor  
- Breadboard, jumper wires, push buttons  
- Power supply unit  
- Internet connectivity  

---

## ⚙️ Tech Stack  
- **Frontend:** Vue.js  
- **Backend:** Flask (Python)  
- **Database/Cache:** Redis  
- **Task Queue:** Celery  
- **Machine Learning:** Random Forest Classifier (Scikit-learn)  
- **IoT Layer:** ESP32 + ACS712 sensor  

---

## 🔄 Workflow  

**1. Data Collection (IoT Layer)**  
- ESP32 + ACS712 continuously measure power consumption.  
- Data is transmitted to Flask backend.  

**2. Data Processing (Backend)**  
- Flask API receives and stores consumption data.  
- Redis + Celery handle asynchronous tasks (alerts, notifications, theft detection).  

**3. Analytics & Budget Monitoring (Frontend)**  
- Vue.js dashboard shows:  
  - Daily consumption & cost  
  - Estimated bill till date  
  - Budget tracker + notifications  
  - Payment status  

**4. Power Theft Detection (ML Layer)**  
- Random Forest Classifier analyzes anomalies in usage.  
- Theft alerts are raised → sent via email + dashboard.  
- User feedback (Ignore/Raise) helps model improve.  

---

## ⚡ Installation & Setup  

### 🔹 Backend (Flask + Redis + Celery)  

#### MacOS Commands
```bash

#install dependencies
pip install -r requirements.txt

# Run Flask server
flask run --host=0.0.0.0 --port=5000

# Start Redis
brew services start redis
redis-server

# Stop Redis
brew services stop redis

# Restart Redis
brew services restart redis

# Check running services
brew services list

# Start Celery Worker
celery -A services.email_service worker -l info --pool gevent
```

#### Windows Commands
```bash

#install dependencies
pip install -r requirements.txt

#start redis
redis-server

#check redis status - expected output "pong"
redis-cli ping

#start flask server
set FLASK_APP=app.py
flask run --host=0.0.0.0 --port=5000

#celery worker
celery -A services.email_service worker -l info --pool gevent

```

### 🔹 Backend (Flask + Redis + Celery)  
```bash
# Navigate to frontend folder
cd frontend

# Install dependencies
npm install

# Run development server
npm run serve
```
### 🔹 IoT (ESP32 + ACS712)

- Upload the code from /IOT to the esp32 via ardunio IDE

- Code for ESP32 is available inside the iot/ folder.

- Flash the ESP32 with Arduino IDE / PlatformIO.

- Ensure WiFi credentials and backend server IP are configured in the code.

### Alerts & Notifications

-Theft or budget breach alerts are sent via Email and shown in Dashboard > Alerts tab.

-- Options:

--- Ignore → Mark as anomaly, not theft (model won’t raise alerts for this pattern).

--- Raise → Confirm theft, system continues alerting.

### Future Scope

- Support for multiple IoT devices per household.

- Advanced predictive analytics for power demand.

- Integration with government billing APIs.

- Mobile app support (React Native/Flutter).

### Authors

- Gokul Das G | Sri Hari Haran M

- Project using Flask + Vue.js + IoT + ML (Random Forest)
