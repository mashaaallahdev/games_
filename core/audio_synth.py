import wave
import struct
import numpy as np
from pathlib import Path
from core.config import SAMPLE_RATE

class ProceduralAudioEngine:
    """
    Synthesizes custom procedural audio for game events.
    100% free, zero copyright issues, perfectly synced to bounce timestamps.
    """
    def __init__(self, duration_sec: float, sample_rate: int = SAMPLE_RATE):
        self.duration = duration_sec
        self.sample_rate = sample_rate
        self.total_samples = int(duration_sec * sample_rate)
        # Stereo audio buffer: shape (total_samples, 2)
        self.buffer = np.zeros((self.total_samples, 2), dtype=np.float32)

    def add_tone(self, start_time: float, freq: float, duration: float = 0.25, volume: float = 0.6, decay: float = 8.0, pan: float = 0.0):
        """
        Adds a musical bell/xylophone chime at a specific timestamp.
        pan: -1.0 (full left) to +1.0 (full right)
        """
        start_idx = int(start_time * self.sample_rate)
        length = int(duration * self.sample_rate)
        if start_idx >= self.total_samples:
            return

        end_idx = min(start_idx + length, self.total_samples)
        actual_len = end_idx - start_idx
        if actual_len <= 0:
            return

        t = np.linspace(0, actual_len / self.sample_rate, actual_len, endpoint=False)

        # Primary fundamental tone + subtle pleasant harmonics (bell / marimba style)
        fundamental = np.sin(2 * np.pi * freq * t)
        harmonic2 = 0.4 * np.sin(2 * np.pi * (freq * 2.0) * t)
        harmonic3 = 0.2 * np.sin(2 * np.pi * (freq * 3.0) * t)
        harmonic4 = 0.1 * np.sin(2 * np.pi * (freq * 4.2) * t)

        signal = (fundamental + harmonic2 + harmonic3 + harmonic4)
        envelope = np.exp(-decay * t)
        sound = signal * envelope * volume

        # Stereo panning
        left_vol = np.clip(0.5 * (1.0 - pan), 0.0, 1.0)
        right_vol = np.clip(0.5 * (1.0 + pan), 0.0, 1.0)

        self.buffer[start_idx:end_idx, 0] += sound * left_vol
        self.buffer[start_idx:end_idx, 1] += sound * right_vol

    def add_explosion(self, start_time: float, volume: float = 0.7, duration: float = 0.4):
        """Adds a satisfying low impact burst sound for breakouts/eliminations."""
        start_idx = int(start_time * self.sample_rate)
        length = int(duration * self.sample_rate)
        if start_idx >= self.total_samples:
            return

        end_idx = min(start_idx + length, self.total_samples)
        actual_len = end_idx - start_idx
        t = np.linspace(0, actual_len / self.sample_rate, actual_len, endpoint=False)

        # White noise + low-frequency sine sweep
        noise = (np.random.rand(actual_len) * 2 - 1) * 0.3
        sweep = np.sin(2 * np.pi * np.linspace(150, 40, actual_len) * t)
        sound = (noise + sweep) * np.exp(-6.0 * t) * volume

        self.buffer[start_idx:end_idx, 0] += sound * 0.5
        self.buffer[start_idx:end_idx, 1] += sound * 0.5

    def add_subtle_background_pulse(self, bpm: float = 120.0, volume: float = 0.15):
        """Adds a gentle rhythmic 4-on-the-floor sub-bass beat to drive energy."""
        beat_interval = 60.0 / bpm
        current_time = 0.0
        while current_time < self.duration:
            start_idx = int(current_time * self.sample_rate)
            length = int(0.12 * self.sample_rate)
            if start_idx + length < self.total_samples:
                t = np.linspace(0, 0.12, length, endpoint=False)
                # Sub bass kick (65Hz down to 35Hz)
                kick = np.sin(2 * np.pi * np.linspace(80, 40, length) * t) * np.exp(-15.0 * t) * volume
                self.buffer[start_idx:start_idx+length, 0] += kick
                self.buffer[start_idx:start_idx+length, 1] += kick
            current_time += beat_interval

    def export_wav(self, file_path: Path):
        """Normalizes and writes audio buffer to a standard 16-bit stereo WAV file."""
        # Normalize to avoid clipping
        max_val = np.max(np.abs(self.buffer))
        if max_val > 0.95:
            self.buffer = (self.buffer / max_val) * 0.95

        # Convert to 16-bit PCM
        pcm16 = (self.buffer * 32767).astype(np.int16)

        with wave.open(str(file_path), "w") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(pcm16.tobytes())
