import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

def train_classical_ml():
    # 1. Load data
    try:
        df = pd.read_csv('sensor_pothole_data.csv')
    except FileNotFoundError:
        print("Dataset not found. Run generate_dataset.py first.")
        return

    # 2. Features and Target
    X = df[['depth_mean', 'depth_max', 'depth_std', 'duration']]
    y = df['label']

    # 3. Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Train Classical ML Model (Random Forest)
    # This is a standard 'Machine Learning' approach using tabular sensor data
    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)

    # 5. Evaluate
    y_pred = model.predict(X_test)
    print(f"Model Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # 6. Save Model for Deployment on Pi
    joblib.dump(model, 'pothole_sensor_model.pkl')
    print("Model saved as 'pothole_sensor_model.pkl'")

if __name__ == "__main__":
    train_classical_ml()
