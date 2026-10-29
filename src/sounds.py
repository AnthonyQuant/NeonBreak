"""In-memory procedural sound effect generator with background music streaming, master volume controls, and mute toggling."""

import io
import math
import os
import random
import struct
import pygame
from src.config import ASSETS_DIR


class SoundManager:
    def __init__(self):
        self.enabled = False
        self.volume = 1.0
        self.music_volume = 0.6
        self.muted = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}

        try:
            if hasattr(pygame, "mixer") and pygame.mixer is not None:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                self.enabled = True
        except Exception:
            self.enabled = False

        if self.enabled:
            try:
                self._generate_synth_sounds()
                self.set_volume(self.volume)
            except Exception as e:
                print(f"Warning: Failed to generate synth sounds ({e}). Disabling audio engine.")
                self.enabled = False

    def _generate_wav_bytes(self, samples: list[float], sample_rate: int = 22050) -> bytes:
        """Encodes raw float audio samples (-1.0 to 1.0) into 16-bit mono WAV binary data."""
        buf = io.BytesIO()
        num_samples = len(samples)
        data_size = num_samples * 2

        buf.write(b"RIFF")
        buf.write(struct.pack("<I", 36 + data_size))
        buf.write(b"WAVEfmt ")
        buf.write(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
        buf.write(b"data")
        buf.write(struct.pack("<I", data_size))

        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            val = int(clamped * 32767)
            buf.write(struct.pack("<h", val))

        return buf.getvalue()

    def _generate_synth_sounds(self):
        sr = 22050

        # 1. Paddle Bounce Tone (380 Hz blip)
        t_samples = int(sr * 0.06)
        p_samples = [math.sin(math.tau * 380 * (i / sr)) * (1.0 - i / t_samples) for i in range(t_samples)]
        self.sounds["paddle"] = pygame.mixer.Sound(io.BytesIO(self._generate_wav_bytes(p_samples)))

        # 2. Brick Hit Tone (600 Hz pop)
        t_samples = int(sr * 0.05)
        b_samples = [math.sin(math.tau * 600 * (i / sr)) * (1.0 - i / t_samples) for i in range(t_samples)]
        self.sounds["brick"] = pygame.mixer.Sound(io.BytesIO(self._generate_wav_bytes(b_samples)))

        # 3. Laser Shot Zap (Descending sweep)
        t_samples = int(sr * 0.08)
        l_samples = [
            math.sin(math.tau * (850 - 450 * (i / t_samples)) * (i / sr)) * (1.0 - i / t_samples)
            for i in range(t_samples)
        ]
        self.sounds["laser"] = pygame.mixer.Sound(io.BytesIO(self._generate_wav_bytes(l_samples)))

        # 4. Explosion Noise Rumble
        t_samples = int(sr * 0.22)
        e_samples = [random.uniform(-0.85, 0.85) * (1.0 - i / t_samples) for i in range(t_samples)]
        self.sounds["explosion"] = pygame.mixer.Sound(io.BytesIO(self._generate_wav_bytes(e_samples)))

        # 5. Wide Paddle Power-Up (W) - Warm low-to-mid swell
        t_samples = int(sr * 0.14)
        w_samples = [
            math.sin(math.tau * (260 + 240 * (i / t_samples)) * (i / sr)) * (1.0 - i / t_samples)
            for i in range(t_samples)
        ]
        self.sounds["powerup_wide"] = pygame.mixer.Sound(io.BytesIO(self._generate_wav_bytes(w_samples)))

        # 6. Slow Motion Power-Up (S) - Descending warp tone
        t_samples = int(sr * 0.16)
        s_samples = [
            math.sin(math.tau * (650 - 380 * (i / t_samples)) * (i / sr)) * (1.0 - i / t_samples)
            for i in range(t_samples)
        ]
        self.sounds["powerup_slow"] = pygame.mixer.Sound(io.BytesIO(self._generate_wav_bytes(s_samples)))

        # 7. Multiball Power-Up (M) - Rapid tri-tone arpeggio (C5-E5-G5)
        m_samples = []
        for freq in [523.25, 659.25, 784.00]:
            sub_len = int(sr * 0.05)
            m_samples.extend([math.sin(math.tau * freq * (i / sr)) * (1.0 - i / sub_len) for i in range(sub_len)])
        self.sounds["powerup_multi"] = pygame.mixer.Sound(io.BytesIO(self._generate_wav_bytes(m_samples)))

        # 8. Laser Paddle Power-Up (L) - High-tech charge chirp
        t_samples = int(sr * 0.12)
        lp_samples = [
            math.sin(math.tau * (400 + 800 * (i / t_samples)**2) * (i / sr)) * (1.0 - i / t_samples)
            for i in range(t_samples)
        ]
        self.sounds["powerup_laser"] = pygame.mixer.Sound(io.BytesIO(self._generate_wav_bytes(lp_samples)))

        # 9. Life Lost Thud - Low pitch thud
        t_samples = int(sr * 0.25)
        ll_samples = [
            (math.sin(math.tau * (220 - 150 * (i / t_samples)) * (i / sr)) + random.uniform(-0.2, 0.2))
            * (1.0 - i / t_samples)
            for i in range(t_samples)
        ]
        self.sounds["life_lost"] = pygame.mixer.Sound(io.BytesIO(self._generate_wav_bytes(ll_samples)))

        # 10. Stage Clear Jingle - Bright 3-note victory rise (D5-F#5-A5)
        sc_samples = []
        for freq in [587.33, 739.99, 880.00]:
            sub_len = int(sr * 0.09)
            sc_samples.extend([math.sin(math.tau * freq * (i / sr)) * (1.0 - i / sub_len) for i in range(sub_len)])
        self.sounds["level_clear"] = pygame.mixer.Sound(io.BytesIO(self._generate_wav_bytes(sc_samples)))

        # 11. All Stages Complete Fanfare (C5-E5-G5-C6)
        gc_samples = []
        for freq in [523.25, 659.25, 784.00, 1046.50]:
            sub_len = int(sr * 0.12)
            gc_samples.extend([math.sin(math.tau * freq * (i / sr)) * (1.0 - i / sub_len) for i in range(sub_len)])
        self.sounds["game_complete"] = pygame.mixer.Sound(io.BytesIO(self._generate_wav_bytes(gc_samples)))

        # 12. Game Over - Minor descending arpeggio (A4-F4-D4-A3)
        go_samples = []
        for freq in [440.00, 349.23, 293.66, 220.00]:
            sub_len = int(sr * 0.11)
            go_samples.extend([math.sin(math.tau * freq * (i / sr)) * (1.0 - i / sub_len) for i in range(sub_len)])
        self.sounds["game_over"] = pygame.mixer.Sound(io.BytesIO(self._generate_wav_bytes(go_samples)))

    def set_volume(self, val: float):
        """Sets global sound effect and background music volume (0.0 to 1.0) with safe fallback."""
        try:
            self.volume = max(0.0, min(1.0, float(val)))
        except (ValueError, TypeError):
            self.volume = 1.0

        if not self.enabled:
            return

        eff_vol = 0.0 if self.muted else self.volume

        for snd in self.sounds.values():
            try:
                snd.set_volume(eff_vol)
            except Exception:
                pass

        try:
            if hasattr(pygame, "mixer") and pygame.mixer is not None and pygame.mixer.get_init():
                pygame.mixer.music.set_volume(eff_vol * self.music_volume)
        except Exception:
            pass

    def toggle_mute(self):
        """Toggles audio mute state across both sound effects and music."""
        self.muted = not self.muted
        self.set_volume(self.volume)

    def play_music(self, filename: str = "bgm.ogg"):
        """Loads and loops background music track from assets/audio/ if present."""
        if not self.enabled:
            return

        music_path = os.path.join(ASSETS_DIR, "audio", filename)
        if os.path.exists(music_path):
            try:
                if hasattr(pygame, "mixer") and pygame.mixer is not None and pygame.mixer.get_init():
                    pygame.mixer.music.load(music_path)
                    pygame.mixer.music.set_volume(0.0 if self.muted else self.volume * self.music_volume)
                    pygame.mixer.music.play(-1)
            except Exception as e:
                print(f"Warning: Could not play background music ({e})")

    def play(self, name: str):
        """Triggers audio playback for registered sound key safely."""
        if self.enabled and not self.muted and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass