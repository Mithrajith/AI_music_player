import os
import librosa
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from utils.audio_utils import extract_bpm_key  # Assuming this extracts BPM and key

# Mock function for extract_bpm_key if not provided
try:
    from utils.audio_utils import extract_bpm_key
except ImportError:
    def extract_bpm_key(audio_path):
        y, sr = librosa.load(audio_path)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        # Simplified key detection (you may have a better implementation)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        key_idx = np.argmax(np.mean(chroma, axis=1))
        key = "major" if key_idx < 6 else "minor"  # Rough heuristic
        return tempo, key

def extract_audio_features(audio_path):
    """
    Extract a comprehensive set of audio features for mood classification.
    """
    try:
        # Load audio file
        y, sr = librosa.load(audio_path, duration=30)  # Analyze first 30 seconds for efficiency

        # Extract BPM and key
        bpm, key = extract_bpm_key(audio_path)

        # Extract additional features
        # 1. Energy (RMS - Root Mean Square)
        rms = np.mean(librosa.feature.rms(y=y))

        # 2. Spectral Centroid (brightness of sound)
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))

        # 3. Spectral Roll-off (high-frequency content)
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))

        # 4. Zero-Crossing Rate (noisiness)
        zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(y=y))

        # 5. Chroma Features (harmonic content)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        valence = np.mean(chroma_mean)  # Rough valence approximation

        # 6. MFCCs (timbre)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)

        # Combine features into a feature vector
        features = np.concatenate([
            [bpm, 1 if key == "major" else 0],  # Encode key as binary
            [rms, spectral_centroid, spectral_rolloff, zero_crossing_rate, valence],
            mfcc_mean
        ])

        return features

    except Exception as e:
        print(f"[ERROR] Feature extraction failed for {audio_path}: {e}")
        return None

def train_mood_classifier():
    """
    Train a simple RandomForest classifier for mood classification.
    This is a placeholder; ideally, train on a labeled dataset.
    """
    # Mock training data (replace with real labeled dataset)
    # Features: [bpm, key (0=minor, 1=major), rms, spectral_centroid, spectral_rolloff, zcr, valence, mfcc1-13]
    X = np.array([
        [60, 0, 0.1, 1500, 3000, 0.05, 0.4, *np.random.rand(13)],  # Sad
        [140, 1, 0.3, 2000, 5000, 0.1, 0.7, *np.random.rand(13)],  # Happy
        [100, 1, 0.2, 1800, 4000, 0.08, 0.5, *np.random.rand(13)],  # Vibe
        [120, 0, 0.25, 1900, 4500, 0.09, 0.6, *np.random.rand(13)]   # Motivation
    ])
    y = np.array(["sad", "happy", "vibe", "motivation"])

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train RandomForest
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_scaled, y)

    return clf, scaler

def classify_mood(features, clf, scaler):
    """
    Classify mood using extracted features and a trained classifier.
    """
    if features is None:
        return "unknown"

    # Scale features
    features_scaled = scaler.transform([features])
    mood = clf.predict(features_scaled)[0]
    return mood

def process_folder(folder_path):
    """
    Process audio files in a folder and classify their mood.
    """
    # Initialize classifier and scaler
    clf, scaler = train_mood_classifier()

    mood_tags = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".mp3"):
            full_path = os.path.join(folder_path, filename)
            try:
                # Extract features
                features = extract_audio_features(full_path)
                if features is None:
                    continue

                # Classify mood
                mood = classify_mood(features, clf, scaler)
                mood_tags[filename] = mood

                # Extract BPM and key for logging
                bpm, key = extract_bpm_key(full_path)
                print(f"[TAGGED] {filename} as {mood} (BPM={bpm:.2f}, Key={key})")

            except Exception as e:
                print(f"[ERROR] Failed to process {filename}: {e}")

    return mood_tags

