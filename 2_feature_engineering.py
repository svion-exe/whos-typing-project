import pandas as pd
import numpy as np
import os
# FIX: Import the feature names from the processor to ensure consistency
from keystroke_processor import STATISTICAL_FEATURE_NAMES

RAW_DATA_FILE = 'keystroke_data.csv'
FEATURES_FILE = 'features.csv'

def engineer_features():
    """
    Reads raw data and engineers the exact same statistical features used by the live app.
    """
    if not os.path.exists(RAW_DATA_FILE):
        print(f"Error: Raw data file '{RAW_DATA_FILE}' not found.")
        return

    df = pd.read_csv(RAW_DATA_FILE)
    if 'style_id' not in df.columns:
        print(f"Error: The CSV is missing the 'style_id' column.")
        return
        
    all_features = []
    grouped = df.groupby(['style_id', 'session_id', 'target_word'])
    
    for (style_id, session_id, target_word), session_df in grouped:
        presses = session_df[session_df['event'] == 'press'].sort_values('timestamp')
        releases = session_df[session_df['event'] == 'release'].sort_values('timestamp')
        
        if not (len(presses) == len(releases) == len(str(target_word))):
            continue

        try:
            dwell_times = [r['timestamp'] - p['timestamp'] for p, r in zip(presses.to_dict('records'), releases.to_dict('records'))]
            flight_times = [presses.iloc[i+1]['timestamp'] - releases.iloc[i]['timestamp'] for i in range(len(releases) - 1)]

            if not dwell_times: continue

            features = {
                'style_id': style_id,
                'dwell_mean': np.mean(dwell_times),
                'dwell_std': np.std(dwell_times),
                'dwell_min': np.min(dwell_times),
                'dwell_max': np.max(dwell_times),
                'flight_mean': np.mean(flight_times) if flight_times else 0,
                'flight_std': np.std(flight_times) if flight_times else 0,
                'flight_min': np.min(flight_times) if flight_times else 0,
                'flight_max': np.max(flight_times) if flight_times else 0,
                'duration': releases.iloc[-1]['timestamp'] - presses.iloc[0]['timestamp']
            }
            all_features.append(features)
        except (IndexError, ValueError):
            continue
            
    if not all_features:
        print("No valid sessions found.")
        return

    features_df = pd.DataFrame(all_features)
    # Ensure a consistent column order using the imported list
    cols = ['style_id'] + STATISTICAL_FEATURE_NAMES
    features_df = features_df[cols]
    
    features_df.to_csv(FEATURES_FILE, index=False)
    print(f"Successfully engineered features for {len(features_df)} sessions.")

if __name__ == "__main__":
    engineer_features()

