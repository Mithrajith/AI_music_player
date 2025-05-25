# BPM/key extraction (if needed)
# ...to be implemented...
import librosa

def extract_bpm_key(filepath):
    y, sr = librosa.load(filepath)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)
    if chroma_mean.argmax() in [0, 5, 7]:
        key = "major"
    else:
        key = "minor"
    return round(tempo), key
