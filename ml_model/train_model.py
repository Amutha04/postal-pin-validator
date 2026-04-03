import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import pickle
import os

print("📦 Loading dataset...")
df = pd.read_csv("../dataset/india_postal.csv")
print(f"✅ Dataset loaded — {len(df)} records")

print("🧹 Cleaning dataset...")
df = df.dropna(subset=["pincode", "district", "statename", "circlename"])
df["pincode"] = df["pincode"].astype(str)
df["district"] = df["district"].str.lower().str.strip()
df["statename"] = df["statename"].str.lower().str.strip()
df["circlename"] = df["circlename"].str.lower().str.strip()
print(f"✅ Cleaned — {len(df)} records")

print("🎯 Getting unique combinations...")
df_unique = df.drop_duplicates(
    subset=["district", "statename", "circlename", "pincode"]
).copy()
print(f"✅ Unique combinations — {len(df_unique)} records")

print("🔢 Encoding features...")
le_district = LabelEncoder()
le_state = LabelEncoder()
le_circle = LabelEncoder()

df_unique["district_encoded"] = le_district.fit_transform(df_unique["district"])
df_unique["state_encoded"] = le_state.fit_transform(df_unique["statename"])
df_unique["circle_encoded"] = le_circle.fit_transform(df_unique["circlename"])
df_unique["pin_prefix"] = df_unique["pincode"].str[:3].astype(int)

X = df_unique[["district_encoded", "state_encoded", "circle_encoded"]]
y = df_unique["pin_prefix"]

print(f"✅ Unique PIN prefixes: {y.nunique()}")
print(f"✅ Total samples: {len(X)}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"✅ Train: {len(X_train)}, Test: {len(X_test)}")

print("🌲 Training Random Forest model...")
model = RandomForestClassifier(
    n_estimators=30,
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=1
)
model.fit(X_train, y_train)
print("✅ Model trained!")

print("📊 Evaluating...")
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"✅ Accuracy: {accuracy * 100:.2f}%")

print("💾 Saving...")
os.makedirs("saved_models", exist_ok=True)

with open("saved_models/rf_model.pkl", "wb") as f:
    pickle.dump(model, f)
with open("saved_models/le_district.pkl", "wb") as f:
    pickle.dump(le_district, f)
with open("saved_models/le_state.pkl", "wb") as f:
    pickle.dump(le_state, f)
with open("saved_models/le_circle.pkl", "wb") as f:
    pickle.dump(le_circle, f)

print("✅ Saved!")
print("🎉 Training complete!")