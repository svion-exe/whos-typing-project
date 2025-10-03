import csv
import os
import time
import random
from pynput import keyboard

# --- Configuration ---
# These should match the styles and words your project is built around.
STYLES = [
    'fast_consistent',
    'slow_deliberate',
    'average_rhythmic',
    'erratic_bursty',
    'peck_typer'
]
WORDS = ['python', 'galaxy', 'security', 'jupiter', 'velocity']
DATA_FILE = 'keystroke_data.csv'
FIELDNAMES = ['style_id', 'session_id', 'target_word', 'key', 'event', 'timestamp']

# --- Global State ---
session_data = []
current_typed_word = ""
target_word_for_session = ""
listener = None

def on_press(key):
    """Callback function to handle key press events."""
    global current_typed_word

    try:
        char = key.char
        if char and char.isalnum():
            timestamp = time.perf_counter()
            session_data.append({'key': char, 'event': 'press', 'timestamp': timestamp})
            current_typed_word += char
            print(f"Typed: '{current_typed_word}'", end='\r', flush=True)

            # Check if the target word has been typed fully
            if len(current_typed_word) >= len(target_word_for_session):
                return False # Stop the listener
    except AttributeError:
        # Ignore special keys
        pass

def on_release(key):
    """Callback function to handle key release events."""
    try:
        char = key.char
        if char and char.isalnum():
            timestamp = time.perf_counter()
            session_data.append({'key': char, 'event': 'release', 'timestamp': timestamp})
    except AttributeError:
        pass

def get_next_session_id():
    """Calculates the next available session ID from the CSV file."""
    if not os.path.exists(DATA_FILE):
        return 1
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None) # Skip header
            last_row = None
            for last_row in reader: pass
            if last_row:
                return int(last_row[1]) + 1
            return 1
    except (IOError, IndexError, ValueError):
        return 1 # Start from 1 if file is corrupt or empty

def save_data(style_id, session_id, target_word):
    """Saves the collected session data to the CSV file."""
    file_exists = os.path.isfile(DATA_FILE) and os.path.getsize(DATA_FILE) > 0

    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()

        for event in session_data:
            writer.writerow({
                'style_id': style_id,
                'session_id': session_id,
                'target_word': target_word,
                'key': event['key'],
                'event': event['event'],
                'timestamp': event['timestamp']
            })
    print(f"\nSession {session_id} for style '{style_id}' saved successfully.")

def main():
    """Main function to run the data collection loop."""
    global session_data, current_typed_word, target_word_for_session, listener

    print("--- Keystroke Data Collector (Style Version) ---")
    print("Available styles:")
    for i, style in enumerate(STYLES):
        print(f"  {i+1}. {style}")
    
    try:
        choice = int(input(f"Select a typing style to record (1-{len(STYLES)}): ")) - 1
        if not 0 <= choice < len(STYLES):
            raise ValueError
        style_id = STYLES[choice]
    except (ValueError, IndexError):
        print("Invalid selection. Exiting.")
        return

    while True:
        # Reset state for the new session
        session_data = []
        current_typed_word = ""
        target_word_for_session = random.choice(WORDS)
        session_id = get_next_session_id()

        print("\n" + "="*50)
        print(f"Starting Session {session_id} for style '{style_id}'")
        print(f"Please type the word: '{target_word_for_session}'")
        input("Press Enter when you are ready to start typing...")

        # Create and start a new listener for the session
        listener = keyboard.Listener(on_press=on_press, on_release=on_release) # type: ignore
        with listener:
            listener.join() # This blocks until the listener is stopped

        # Brief pause to ensure the final release event is captured
        time.sleep(0.1)

        # Validate and save the collected data
        if current_typed_word.lower() == target_word_for_session:
            save_data(style_id, session_id, target_word_for_session)
        else:
            print(f"\nInput '{current_typed_word}' did not match '{target_word_for_session}'. Session discarded.")

        another = input("Record another session for this style? (y/n): ").strip().lower()
        if another != 'y':
            break
            
    print(f"\nData collection finished.")

if __name__ == "__main__":
    main()