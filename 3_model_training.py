import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
import os

def train_model():
    """
    Loads engineered features, trains a Gradient Boosting classifier,
    evaluates its performance with detailed reports, and saves the assets.
    This version is updated to classify 'style_id'.
    """
    FEATURES_FILE = 'features.csv'
    MODEL_FILE = 'keystroke_model.joblib'
    SCALER_FILE = 'scaler.joblib'

    if not os.path.exists(FEATURES_FILE):
        print(f"Error: '{FEATURES_FILE}' not found. Please run '2_feature_engineering.py' first.")
        return

    df = pd.read_csv(FEATURES_FILE)
    if df.empty:
        print(f"Error: '{FEATURES_FILE}' is empty. Please collect data.")
        return

    print(f"Loaded {len(df)} sessions from '{FEATURES_FILE}'.")

    # --- 1. Diagnose: Check for Data Imbalance ---
    print("\n--- Data Distribution ---")
    # FIX: Use 'style_id' instead of 'user_id'
    style_counts = df['style_id'].value_counts()
    print(style_counts)
    print("-------------------------\n")

    # FIX: Use 'style_id' for features (X) and labels (y)
    X = df.drop('style_id', axis=1)
    y = df['style_id']
    
    if any(count < 2 for count in style_counts):
        print("Error: At least one style has fewer than 2 samples. Cannot perform a train/test split.")
        return

    # --- 2. Train-Test Split ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    # --- 3. Scale the features ---
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # --- 4. Train a Gradient Boosting model ---
    print("Training a Gradient Boosting Classifier...")
    model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
    model.fit(X_train_scaled, y_train)
    print("Model training complete.")

    # --- 5. Evaluate the model ---
    print("\n--- Model Evaluation on Test Set ---")
    y_pred = model.predict(X_test_scaled)
    
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy:.2f}")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # --- 6. Generate and Save Confusion Matrix ---
    print("\nGenerating Confusion Matrix...")
    cm = confusion_matrix(y_test, y_pred, labels=model.classes_)
    plt.figure(figsize=(10, 7))
    
    class_labels = model.classes_.tolist()
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_labels, yticklabels=class_labels)
                
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.title('Confusion Matrix - Typing Styles')
    plt.savefig('confusion_matrix.png')
    print("Confusion matrix saved as 'confusion_matrix.png'.")

    # --- 7. Save the model and scaler ---
    joblib.dump(model, MODEL_FILE)
    joblib.dump(scaler, SCALER_FILE)
    print(f"\nTrained model and scaler saved successfully.")

if __name__ == "__main__":
    train_model()

