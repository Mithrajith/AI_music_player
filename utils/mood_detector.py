import os
import librosa
from utils.audio_utils import extract_bpm_key

def classify_mood(bpm, key):
    if bpm < 80 and key == "minor":
        return "sad"
    elif bpm > 120 and key == "major":
        return "happy"
    elif 90 <= bpm <= 110:
        return "vibe"
    else:
        return "motivation"

def process_folder(folder_path):
    mood_tags = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".mp3"):
            full_path = os.path.join(folder_path, filename)
            try:
                bpm, key = extract_bpm_key(full_path)
                mood = classify_mood(bpm, key)
                mood_tags[filename] = mood
                print(f"[TAGGED] {filename} as {mood} (BPM={bpm}, Key={key})")
            except Exception as e:
                print(f"[ERROR] Failed to process {filename}: {e}")
    return mood_tags
