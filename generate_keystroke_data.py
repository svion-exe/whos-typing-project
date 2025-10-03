"""Generate synthetic keystroke data for all typing styles."""
import csv
import random

STYLES = {
    'fast_consistent': {'dwell': (75, 8), 'flight': (120, 12)},
    'slow_deliberate': {'dwell': (150, 10), 'flight': (200, 15)},
    'average_rhythmic': {'dwell': (100, 5), 'flight': (160, 8)},
    'erratic_bursty': {'dwell': (90, 25), 'flight': (150, 60)},
    'peck_typer': {'dwell': (60, 7), 'flight': (250, 20)}
}

WORDS = ['python', 'galaxy', 'security', 'jupiter', 'velocity']
SESSIONS_PER_COMBO = 20

def gen_time(mean, std):
    """Generate a realistic timing value."""
    return max(random.gauss(mean, std), mean * 0.3)

def gen_session(style_id, session_id, word, params):
    """Generate all events for one typing session."""
    events = []
    ts = random.uniform(1000000, 2000000)
    dwell_mean, dwell_std = params['dwell']
    flight_mean, flight_std = params['flight']
    
    for char in word:
        events.append([style_id, session_id, word, char, 'press', round(ts, 3)])
        ts += gen_time(dwell_mean, dwell_std)
        events.append([style_id, session_id, word, char, 'release', round(ts, 3)])
        ts += gen_time(flight_mean, flight_std)
    
    return events

def main():
    all_data = []
    session_id = 1

    for style_id, params in STYLES.items():
        for word in WORDS:
            for _ in range(SESSIONS_PER_COMBO):
                all_data.extend(gen_session(style_id, session_id, word, params))
                session_id += 1

    with open('keystroke_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['style_id', 'session_id', 'target_word', 'key', 'event', 'timestamp'])
        writer.writerows(all_data)

    print(f"✓ Generated keystroke_data.csv")
    print(f"✓ Total sessions: {session_id - 1}")
    print(f"✓ Total events: {len(all_data)}")
    print(f"✓ Styles: {list(STYLES.keys())}")

if __name__ == "__main__":
    main()