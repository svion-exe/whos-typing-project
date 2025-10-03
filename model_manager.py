import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

def load_assets(base_dir: Path) -> Dict[str, Any]:
    """
    Loads all machine learning assets (model, scaler, feature columns).
    This function is designed to be robust against common file and data errors.
    """
    assets = {
        "model": None,
        "scaler": None,
        "feature_columns": None,
        "known_styles": [],
        "loaded": False,
        "error_message": ""
    }
    try:
        # Define file paths
        model_file = base_dir / 'keystroke_model.joblib'
        scaler_file = base_dir / 'scaler.joblib'
        features_file = base_dir / 'features.csv'

        # 1. Load the features file first to get metadata. This fails fast if the data is wrong.
        features_df = pd.read_csv(features_file)
        assets["feature_columns"] = features_df.drop('style_id', axis=1).columns.tolist()

        # 2. Load the trained model and scaler
        assets["model"] = joblib.load(model_file)
        assets["scaler"] = joblib.load(scaler_file)
        
        # 3. Get the list of known styles directly from the trained model
        assets["known_styles"] = assets["model"].classes_.tolist()

        assets["loaded"] = True

    except FileNotFoundError as e:
        assets["error_message"] = f"A required asset file was not found: '{e.filename}'. Please ensure the model has been trained by running the pipeline scripts."
    except KeyError:
        assets["error_message"] = "The 'features.csv' file is malformed. It is missing the required 'style_id' column. Please re-run the feature engineering script."
    except Exception as e:
        assets["error_message"] = f"An unexpected error occurred while loading ML assets: {e}"
        
    return assets

def get_prediction(features_df: pd.DataFrame, model: Any, scaler: Any) -> Dict[str, Any]:
    """
    Scales features, performs a prediction, and returns a dictionary with JSON-compatible types.
    This function includes a defensive check to ensure feature consistency.
    """
    if features_df.empty:
        return {"error": "Cannot make a prediction on empty feature data."}
        
    # Defensive Check: Ensure the incoming data has the same features as the scaler expects.
    if len(features_df.columns) != scaler.n_features_in_:
        return {"error": f"Feature mismatch. The model expects {scaler.n_features_in_} features, but the live data has {len(features_df.columns)}."}

    # Scale the features
    scaled_features = scaler.transform(features_df)
    
    # Make predictions
    predicted_style = model.predict(scaled_features)[0]
    probabilities = model.predict_proba(scaled_features)[0]
    confidence = np.max(probabilities) * 100

    # --- ADDED FOR DEBUGGING ---
    # This will print the types to your terminal right before the return statement.
    print(f"--- DEBUG INFO ---")
    print(f"Predicted Style: '{predicted_style}', Type: {type(predicted_style)}")
    print(f"Confidence: {confidence}, Type: {type(confidence)}")
    print(f"--------------------")

    # THE DEFINITIVE FIX: Ensure all return values are standard Python types.
    return {
        "predicted_style": str(predicted_style), # Convert potential numpy.str_ to a standard string
        "confidence": float(confidence),     # Convert numpy.float64 to a standard float
    }

