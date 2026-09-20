"""Enhanced Pygame sound effects for Tetris."""

import array
import math
import random

try:
    import pygame
except ImportError:
    pygame = None

from config import SOUND_ENABLED, SOUND_PREFERENCES

class SoundManager:
    """Generate and play enhanced tones through Pygame's mixer."""

    def __init__(self):
        self.enabled = SOUND_ENABLED and pygame is not None
        self.sounds = {}
        self.volume = 0.3
        
        if self.enabled:
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                self._create_sounds()
                self.set_volume(self.volume)
            except pygame.error:
                self.enabled = False
    
    def set_volume(self, vol):
        """Set sound volume (0.0 to 1.0)."""
        self.volume = max(0, min(1, vol))
        if self.enabled:
            for sound in self.sounds.values():
                if isinstance(sound, list):
                    for s in sound:
                        s.set_volume(self.volume)
                else:
                    sound.set_volume(self.volume)
    
    def _tone(self, frequency, duration, sample_rate=44100, wave_type="sine"):
        """Generate a tone with specified waveform."""
        samples = int(duration * sample_rate)
        data = array.array("h")
        
        for index in range(samples):
            t = index / sample_rate
            if wave_type == "sine":
                value = math.sin(2 * math.pi * frequency * t)
            elif wave_type == "square":
                value = 1.0 if (frequency * 2 * t) % 1 < 0.5 else -1.0
            elif wave_type == "triangle":
                value = 2 * abs(2 * ((frequency * t) % 1) - 1) - 1
            elif wave_type == "sawtooth":
                value = 2 * ((frequency * t) % 1) - 1
            else:  # default to sine
                value = math.sin(2 * math.pi * frequency * t)
            
            # Envelope for smoother sound
            envelope = 1.0
            if index < sample_rate * 0.01:  # Attack
                envelope = index / (sample_rate * 0.01)
            elif index > samples - sample_rate * 0.01:  # Release
                envelope = (samples - index) / (sample_rate * 0.01)
            
            data.append(int(32767 * 0.3 * value * envelope))
        
        return pygame.mixer.Sound(buffer=data.tobytes())
    
    def _sequence(self, frequencies, duration, wave_type="sine"):
        """Create a sequence of tones."""
        return [self._tone(f, duration / len(frequencies), wave_type=wave_type) for f in frequencies]
    
    def _create_sounds(self):
        """Create all sound effects."""
        prefs = SOUND_PREFERENCES
        
        self.sounds["rotate"] = self._tone(
            prefs["rotate"]["frequency"],
            prefs["rotate"]["duration"],
            wave_type="triangle"
        )
        
        self.sounds["move"] = self._tone(
            prefs["move"]["frequency"],
            prefs["move"]["duration"],
            wave_type="sine"
        )
        
        self.sounds["drop"] = self._tone(
            prefs["drop"]["frequency"],
            prefs["drop"]["duration"],
            wave_type="square"
        )
        
        self.sounds["hard_drop"] = self._tone(
            prefs["hard_drop"]["frequency"],
            prefs["hard_drop"]["duration"],
            wave_type="square"
        )
        
        self.sounds["line_clear"] = self._sequence(
            prefs["line_clear"]["frequencies"],
            prefs["line_clear"]["duration"],
            wave_type="triangle"
        )
        
        self.sounds["combo"] = self._sequence(
            prefs["combo"]["frequencies"],
            prefs["combo"]["duration"],
            wave_type="sine"
        )
        
        self.sounds["game_over"] = self._sequence(
            prefs["game_over"]["frequencies"],
            prefs["game_over"]["duration"],
            wave_type="sawtooth"
        )
        
        self.sounds["level_up"] = self._sequence(
            prefs["level_up"]["frequencies"],
            prefs["level_up"]["duration"],
            wave_type="triangle"
        )
    
    def _play(self, name):
        """Play a sound by name."""
        if not self.enabled:
            return
        
        sound = self.sounds.get(name)
        if sound is None:
            return
        
        try:
            if isinstance(sound, list):
                for s in sound:
                    s.play()
            else:
                sound.play()
        except pygame.error:
            pass
    
    def play_rotate(self):
        self._play("rotate")
    
    def play_move(self):
        self._play("move")
    
    def play_drop(self):
        self._play("drop")
    
    def play_hard_drop(self):
        self._play("hard_drop")
    
    def play_line_clear(self):
        self._play("line_clear")
    
    def play_combo(self):
        self._play("combo")
    
    def play_game_over(self):
        self._play("game_over")
    
    def play_level_up(self):
        self._play("level_up")
    
    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled
    
    def set_preference(self, sound_type, **kwargs):
        """Update sound preferences and recreate sounds."""
        if sound_type in SOUND_PREFERENCES:
            SOUND_PREFERENCES[sound_type].update(kwargs)
            self._create_sounds()
