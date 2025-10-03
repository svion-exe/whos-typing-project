import pandas as pd
import numpy as np
from typing import List
import csv
import os
from pathlib import Path
from pydantic_models import KeystrokeEvent

# --- Configuration ---
TARGET_WORDS = ["galaxy", "python", "bridge", "machine", "quantum", "explore", "journey", "future"]
# The feature names are now defined here as the single source of truth.
STATISTICAL_FEATURE_NAMES = [
    'dwell_mean', 'dwell_std', 'dwell_min', 'dwell_max',
    'flight_mean', 'flight_std', 'flight_min', 'flight_max',
    'duration'
]

def process_live_keystrokes(events: List[KeystrokeEvent], target_word: str) -> pd.DataFrame | None:
    """
    Engineers statistical features from a list of raw keystroke events.
    """
    events_data = [event.dict() for event in events]
    
    presses = sorted([e for e in events_data if e['event'] == 'press'], key=lambda x: x['timestamp'])
    releases = sorted([e for e in events_data if e['event'] == 'release'], key=lambda x: x['timestamp'])

    if not (len(presses) == len(releases) == len(target_word)):
        return None
    
    typed_word = "".join([p['key'] for p in presses])
    if typed_word.lower() != target_word.lower():
        return None

    try:
        dwell_times = [r['timestamp'] - p['timestamp'] for p, r in zip(presses, releases)]
        flight_times = [presses[i+1]['timestamp'] - releases[i]['timestamp'] for i in range(len(releases) - 1)]

        if not dwell_times:
            return None

        features = {
            'dwell_mean': np.mean(dwell_times),
            'dwell_std': np.std(dwell_times),
            'dwell_min': np.min(dwell_times),
            'dwell_max': np.max(dwell_times),
            'flight_mean': np.mean(flight_times) if flight_times else 0,
            'flight_std': np.std(flight_times) if flight_times else 0,
            'flight_min': np.min(flight_times) if flight_times else 0,
            'flight_max': np.max(flight_times) if flight_times else 0,
            'duration': releases[-1]['timestamp'] - presses[0]['timestamp']
        }

        live_features_df = pd.DataFrame([features], columns=STATISTICAL_FEATURE_NAMES)
        
        if live_features_df.isnull().values.any():
            return None
            
        return live_features_df
        
    except (IndexError, ValueError):
        return None

def save_keystroke_data(style_id: str, target_word: str, events: List[KeystrokeEvent], base_dir: Path) -> dict:
    """
    Saves a new typing sample to the raw data CSV file.
    """
    style_id = style_id.strip().lower()
    data_file = base_dir / 'keystroke_data.csv'

    if not style_id:
        return {"error": "Style ID cannot be empty."}

    session_id = 1
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header:
                    max_session_id = 0
                    for row in reader:
                        if row:
                           max_session_id = max(max_session_id, int(row[1]))
                    session_id = max_session_id + 1
        except (IOError, IndexError, ValueError):
            return {"error": "Could not correctly read the existing data file."}

    try:
        file_exists_and_not_empty = os.path.isfile(data_file) and os.path.getsize(data_file) > 0
        with open(data_file, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['style_id', 'session_id', 'target_word', 'key', 'event', 'timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists_and_not_empty:
                writer.writeheader()

            for event in events:
                writer.writerow({
                    'style_id': style_id,
                    'session_id': session_id,
                    'target_word': target_word,
                    'key': event.key,
                    'event': event.event,
                    'timestamp': event.timestamp
                })
        return {"message": f"Successfully saved session {session_id} for style '{style_id}'. Please retrain the model."}
    except IOError as e:
        return {"error": f"Failed to write to data file: {e}"}

