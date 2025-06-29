import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

# Sample data for training
data = {
    'pm2_5': [20, 40, 60, 80, 100],
    'humidity': [30, 40, 50, 60, 70],
    'temperature': [20, 25, 30, 35, 40],
    'aqi': [50, 100, 150, 200, 250]
}

# Convert to DataFrame
df = pd.DataFrame(data)

# Train a simple model
X = df[['pm2_5', 'humidity', 'temperature']]
y = df['aqi']

model = RandomForestRegressor()
model.fit(X, y)

# Save model to model/model.pkl
os.makedirs('model', exist_ok=True)
joblib.dump(model, 'model/model.pkl')
print("✅ Model saved at model/model.pkl")
