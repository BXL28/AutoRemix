import os
import librosa
import soundfile as sf
import numpy as np
from pedalboard import Pedalboard, Chorus, Reverb, Compressor, HighpassFilter

def match_tempo(audio_path, target_bpm, original_bpm=None):
    """
    Time-stretches the audio to match a target BPM using librosa.
    """
    y, sr = librosa.load(audio_path, sr=44100)
    
    if not original_bpm:
        # Estimate the BPM if not provided
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        original_bpm = tempo[0] if isinstance(tempo, np.ndarray) else tempo
        print(f"Estimated original BPM for {audio_path}: {original_bpm:.2f}")

    if original_bpm == 0 or target_bpm == 0:
        return y, sr

    # Calculate ratio for time-stretching
    rate = target_bpm / original_bpm
    print(f"Stretching {audio_path} from {original_bpm:.2f} BPM to {target_bpm} BPM (Ratio: {rate:.2f})")
    
    # Time stretch
    y_stretched = librosa.effects.time_stretch(y, rate=rate)
    return y_stretched, sr

def create_remix(base_track_path: str, secondary_track_path: str, output_path: str, target_bpm: int):
    """
    Matches the tempo of both tracks, applies pedalboard effects, and mixes them together.
    """
    print(f"Starting remix process... Target BPM: {target_bpm}")
    
    # 1. Match tempos
    y_base, sr = match_tempo(base_track_path, target_bpm)
    y_sec, _ = match_tempo(secondary_track_path, target_bpm)
    
    # Ensure they are the same length by trimming to the shortest one
    min_len = min(len(y_base), len(y_sec))
    y_base = y_base[:min_len]
    y_sec = y_sec[:min_len]

    # 2. Process Secondary Track (The one we are mixing in)
    # We will high-pass it so the basslines don't clash, and add some chorus/reverb to sit in the background
    print("Applying Pedalboard effects to secondary track...")
    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=300), # Cut the bass
        Chorus(rate_hz=1.0, depth=0.25, centre_delay_ms=7.0, feedback=0.0, mix=0.5),
        Reverb(room_size=0.6, damping=0.5, wet_level=0.33, dry_level=0.4),
        Compressor(threshold_db=-20, ratio=4.0)
    ])
    
    # Pedalboard expects shape (channels, samples). Librosa loads as (samples,) for mono.
    # Convert to standard stereo shape (2, N) for pedalboard processing
    if y_sec.ndim == 1:
        y_sec_stereo = np.vstack((y_sec, y_sec))
    else:
        y_sec_stereo = y_sec
        
    processed_sec = board(y_sec_stereo, sr, reset=False)
    
    # Convert back to mono if we started with mono
    if y_sec.ndim == 1:
        processed_sec_mono = np.mean(processed_sec, axis=0)
    else:
        processed_sec_mono = processed_sec

    # 3. Mix Tracks Together
    # 70% Base track volume, 50% Processed secondary track volume
    print("Mixing tracks...")
    mixed = (y_base * 0.7) + (processed_sec_mono * 0.5)
    
    # Normalize to prevent clipping
    max_val = np.max(np.abs(mixed))
    if max_val > 0:
        mixed = mixed / max_val * 0.9

    # 4. Export
    print(f"Exporting remixed track to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sf.write(output_path, mixed, sr)
    print("Remix complete!")
    return output_path

if __name__ == "__main__":
    print("Pedalboard Audio Processor Initialized.")
    # Tests would require valid local mp3 files.
