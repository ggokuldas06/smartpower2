import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
from datetime import datetime, timedelta


# --------------------------
# Simulated Data Generation
# --------------------------
def simulate_power_data(n=1000, start_time=datetime.now()):
    timestamps = [start_time + timedelta(minutes=i) for i in range(n)]
    
    # baseline current ~5A
    current = np.random.normal(5, 1, n)
    
    # approximate power (kW) = current * voltage
    power = current * np.random.normal(220, 5, n)
    
    # introduce theft cases (spikes or mismatches)
    theft_indices = np.random.choice(range(n), size=int(0.1 * n), replace=False)
    power[theft_indices] *= np.random.uniform(1.5, 3, len(theft_indices))
    
    # create dataframe
    df = pd.DataFrame({
        "timestamp": timestamps,
        "current": current,
        "power": power,
    })
    
    # labels
    df["theft"] = 0
    df.loc[theft_indices, "theft"] = 1
    
    # engineered time-based features
    df["hour_of_day"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["label"] = np.random.choice([0,1], size=n, p=[0.9, 0.1])  # 90% not theft, 10% theft for training
    
    return df


# --------------------------
# Data + Model Training
# --------------------------
data = simulate_power_data(n=2000)
print("Sample Data:\n", data.head())
data.to_csv("power_dataset.csv", index=False)

X = data[["current", "power", "hour_of_day", "day_of_week", "is_weekend"]]
y = data["theft"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

print("Training Accuracy:", model.score(X_train, y_train))
print("Testing Accuracy:", model.score(X_test, y_test))

# Save model
joblib.dump(model, "theft_model.pkl")
print("✅ Model saved as theft_model.pkl")
