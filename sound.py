"""Optional Pygame sound effects for Tetris."""

import array
import math

try:
    import pygame
except ImportError:
    pygame = None

from config import SOUND_ENABLED, SOUND_PREFERENCES


class SoundManager:
    """Generate and play simple tones through Pygame's mixer."""

    def __init__(self):
        self.enabled = SOUND_ENABLED and pygame is not None
        self.sounds = {}
        if self.enabled:
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                self._create_sounds()
            except pygame.error:
                self.enabled = False

    def _tone(self, frequency, duration, sample_rate=44100):
        samples = int(duration * sample_rate)
        data = array.array("h")
        for index in range(samples):
            value = int(32767 * 0.25 * math.sin(2 * math.pi * frequency * index / sample_rate))
            data.append(value)
        return pygame.mixer.Sound(buffer=data.tobytes())

    def _sequence(self, frequencies, duration):
        return [self._tone(frequency, duration / len(frequencies)) for frequency in frequencies]

    def _create_sounds(self):
        self.sounds["rotate"] = self._tone(
            SOUND_PREFERENCES["rotation"]["frequency"],
            SOUND_PREFERENCES["rotation"]["duration"],
        )
        self.sounds["move"] = self._tone(
            SOUND_PREFERENCES["move"]["frequency"],
            SOUND_PREFERENCES["move"]["duration"],
        )
        self.sounds["drop"] = self._tone(
            SOUND_PREFERENCES["drop"]["frequency"],
            SOUND_PREFERENCES["drop"]["duration"],
        )
        self.sounds["line_clear"] = self._sequence(
            SOUND_PREFERENCES["line_clear"]["frequencies"],
            SOUND_PREFERENCES["line_clear"]["duration"],
        )
        self.sounds["game_over"] = self._sequence(
            SOUND_PREFERENCES["game_over"]["frequencies"],
            SOUND_PREFERENCES["game_over"]["duration"],
        )

    def _play(self, name):
        if not self.enabled:
            return
        sound = self.sounds[name]
        if isinstance(sound, list):
            for item in sound:
                item.play()
        else:
            sound.play()

    def play_rotate(self):
        self._play("rotate")

    def play_move(self):
        self._play("move")

    def play_drop(self):
        self._play("drop")

    def play_line_clear(self):
        self._play("line_clear")

    def play_game_over(self):
        self._play("game_over")

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled

    def set_preference(self, sound_type, **kwargs):
        if sound_type in SOUND_PREFERENCES:
            SOUND_PREFERENCES[sound_type].update(kwargs)
