import os
import librosa
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Your provided extract_bpm_key function
def extract_bpm_key(filepath):
    y, sr = librosa.load(filepath)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    # tempo might still be a numpy array if extracted differently — safeguard
    if isinstance(tempo, (list, tuple, np.ndarray)):
        tempo = tempo[0] if len(tempo) else 0

    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)
    
    key = "major" if chroma_mean.argmax() in [0, 5, 7] else "minor"

    return round(float(tempo)), key

def extract_audio_features(audio_path, duration=30):
    """
    Extract a comprehensive set of audio features for mood classification.
    """
    try:
        # Load audio file (first 'duration' seconds for efficiency)
        y, sr = librosa.load(audio_path, duration=duration)

        # Extract BPM and key using provided function
        bpm, key = extract_bpm_key(audio_path)

        # Additional features for better mood detection
        # 1. Energy (RMS)
        rms = np.mean(librosa.feature.rms(y=y))

        # 2. Spectral Centroid (brightness)
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))

        # 3. Spectral Roll-off (high-frequency content)
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))

        # 4. Zero-Crossing Rate (noisiness)
        zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(y=y))

        # 5. Valence (harmonic pleasantness)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        valence = np.mean(chroma.mean(axis=1))

        # 6. MFCCs (timbre)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)

        # 7. Tempo stability (variance in beat intervals)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        tempo_stability = np.std(np.diff(beat_times)) if len(beat_times) > 1 else 0

        # Combine features
        features = np.concatenate([
            [bpm, 1 if key == "major" else 0],  # Encode key as binary
            [rms, spectral_centroid, spectral_rolloff, zero_crossing_rate, valence, tempo_stability],
            mfcc_mean
        ])

        return features, bpm, key

    except Exception as e:
        print(f"[ERROR] Feature extraction failed for {audio_path}: {e}")
        return None, None, None

def train_mood_classifier(X_train=None, y_train=None):
    """
    Train a RandomForest classifier. Uses mock data if no training data is provided.
    """
    if X_train is None or y_train is None:
        # Mock training data (replace with real labeled dataset)
        X_train = np.array([
            [60, 0, 0.1, 1500, 3000, 0.05, 0.4, 0.02, *np.random.rand(13)],  # Sad
            [140, 1, 0.3, 2000, 5000, 0.1, 0.7, 0.01, *np.random.rand(13)],  # Happy
            [100, 1, 0.2, 1800, 4000, 0.08, 0.5, 0.015, *np.random.rand(13)],  # Vibe
            [120, 0, 0.25, 1900, 4500, 0.09, 0.6, 0.012, *np.random.rand(13)]   # Motivation
        ])
        y_train = np.array(["sad", "happy", "vibe", "motivation"])

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    # Train RandomForest
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train_scaled, y_train)

    return clf, scaler

def classify_mood(features, clf, scaler):
    """
    Classify mood using extracted features and a trained classifier.
    """
    if features is None:
        return "unknown"
    features_scaled = scaler.transform([features])
    mood = clf.predict(features_scaled)[0]
    return mood
def parse_essentia_mood(json_path):
    """
    Read Essentia's JSON output and classify the mood.
    """
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        mood_valence = data['highlevel']['mood_valence']['value']
        mood_arousal = data['highlevel']['mood_arousal']['value']

        # Map to mood categories
        if mood_valence == "positive" and mood_arousal == "high":
            return "happy"
        elif mood_valence == "negative" and mood_arousal == "high":
            return "angry"
        elif mood_valence == "positive" and mood_arousal == "low":
            return "relaxed"
        elif mood_valence == "negative" and mood_arousal == "low":
            return "sad"
        else:
            return "unknown"
    except Exception as e:
        print(f"[ERROR] Parsing failed: {e}")
        return "unknown"

def process_folder_with_essentia(folder_path, extractor_path='streaming_extractor_music'):
    """
    Process audio files using Essentia's pre-trained model for mood detection.
    """
    mood_tags = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".mp3"):
            full_path = os.path.join(folder_path, filename)
            json_output = full_path.replace('.mp3', '_features.json')

            try:
                # Run Essentia's extractor
                run([extractor_path, full_path, json_output], check=True)

                # Get mood from JSON output
                mood = parse_essentia_mood(json_output)
                mood_tags[filename] = mood

                print(f"[TAGGED] {filename} as {mood}")

            except Exception as e:
                print(f"[ERROR] Failed to process {filename}: {e}")

    return mood_tags