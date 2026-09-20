"""Procedural chiptune music and punchy SFX for Neon Tetris."""

from __future__ import annotations

import array
import math
import random

try:
    import pygame
except ImportError:
    pygame = None

from config import MUSIC_ENABLED, SOUND_ENABLED


SAMPLE_RATE = 22050


class SoundManager:
    def __init__(self):
        self.enabled = SOUND_ENABLED and pygame is not None
        self.music_on = MUSIC_ENABLED
        self.sounds = {}
        self.music = None
        self.volume = 0.32
        self.music_volume = 0.16
        self._music_channel = None
        if self.enabled:
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
                    pygame.mixer.set_num_channels(16)
                self._create_sounds()
                self._create_music()
                self.set_volume(self.volume)
            except pygame.error:
                self.enabled = False

    def set_volume(self, vol):
        self.volume = max(0.0, min(1.0, vol))
        if not self.enabled:
            return
        for sound in self.sounds.values():
            if isinstance(sound, list):
                for s in sound:
                    s.set_volume(self.volume)
            else:
                sound.set_volume(self.volume)
        if self.music:
            self.music.set_volume(self.music_volume)

    def _tone_samples(self, frequency, duration, wave="sine", volume=0.35):
        n = max(1, int(duration * SAMPLE_RATE))
        data = array.array("h")
        attack = max(1, int(0.008 * SAMPLE_RATE))
        release = max(1, int(0.04 * SAMPLE_RATE))
        for i in range(n):
            t = i / SAMPLE_RATE
            if wave == "square":
                v = 1.0 if math.sin(2 * math.pi * frequency * t) >= 0 else -1.0
            elif wave == "triangle":
                v = 2 * abs(2 * ((frequency * t) % 1) - 1) - 1
            elif wave == "saw":
                v = 2 * ((frequency * t) % 1) - 1
            elif wave == "noise":
                v = random.uniform(-1, 1)
            else:
                v = math.sin(2 * math.pi * frequency * t)
            if i < attack:
                env = i / attack
            elif i > n - release:
                env = max(0.0, (n - i) / release)
            else:
                env = 1.0
            # light pitch-down click killer
            data.append(int(32767 * volume * v * env))
        return data

    def _sound_from(self, samples):
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _tone(self, frequency, duration, wave="sine", volume=0.35):
        return self._sound_from(self._tone_samples(frequency, duration, wave, volume))

    def _sweep(self, f0, f1, duration, wave="square", volume=0.3):
        n = max(1, int(duration * SAMPLE_RATE))
        data = array.array("h")
        for i in range(n):
            t = i / n
            freq = f0 + (f1 - f0) * t
            env = math.sin(math.pi * min(1.0, t * 1.15)) ** 0.6
            ph = 2 * math.pi * freq * (i / SAMPLE_RATE)
            if wave == "square":
                v = 1.0 if math.sin(ph) >= 0 else -1.0
            else:
                v = math.sin(ph)
            data.append(int(32767 * volume * v * env))
        return self._sound_from(data)

    def _chord(self, freqs, duration, wave="triangle", volume=0.22):
        n = max(1, int(duration * SAMPLE_RATE))
        acc = [0.0] * n
        for f in freqs:
            samples = self._tone_samples(f, duration, wave, volume=1.0)
            for i, s in enumerate(samples):
                acc[i] += s / 32767.0
        data = array.array("h")
        peak = max(1e-6, max(abs(x) for x in acc))
        for x in acc:
            data.append(int(32767 * volume * (x / peak)))
        return self._sound_from(data)

    def _create_sounds(self):
        self.sounds["rotate"] = self._tone(880, 0.045, "triangle", 0.22)
        self.sounds["move"] = self._tone(420, 0.025, "sine", 0.16)
        self.sounds["lock"] = self._tone(160, 0.06, "square", 0.2)
        self.sounds["hard_drop"] = self._sweep(220, 70, 0.11, "square", 0.28)
        self.sounds["hold"] = self._tone(660, 0.07, "sine", 0.2)
        self.sounds["line_clear"] = self._chord([523, 659, 784], 0.18, "triangle", 0.28)
        self.sounds["tetris"] = self._chord([523, 784, 1047, 1319], 0.42, "triangle", 0.34)
        self.sounds["tspin"] = self._chord([370, 554, 740, 1108], 0.28, "saw", 0.26)
        self.sounds["combo"] = self._sweep(440, 1320, 0.16, "sine", 0.24)
        self.sounds["level_up"] = self._chord([523, 659, 784, 1047, 1319], 0.45, "triangle", 0.3)
        self.sounds["game_over"] = self._sweep(420, 90, 0.7, "saw", 0.28)
        self.sounds["select"] = self._tone(1047, 0.05, "square", 0.18)
        self.sounds["back_to_back"] = self._chord([880, 1320, 1760], 0.22, "triangle", 0.26)

    def _create_music(self):
        # Original neon arpeggio in A minor, ~8s loop. Not Korobeiniki.
        bpm = 132
        beat = 60.0 / bpm
        melody = [
            (220.00, 1), (261.63, 1), (329.63, 1), (440.00, 1),
            (392.00, 1), (329.63, 1), (293.66, 1), (261.63, 1),
            (246.94, 1), (261.63, 1), (329.63, 1), (392.00, 1),
            (440.00, 2), (392.00, 1), (329.63, 1),
            (349.23, 1), (329.63, 1), (293.66, 1), (261.63, 1),
            (246.94, 1), (220.00, 1), (196.00, 1), (220.00, 1),
            (261.63, 2), (246.94, 1), (220.00, 1),
            (207.65, 2), (220.00, 2),
        ]
        bass = [
            (110.00, 4), (130.81, 4), (146.83, 4), (110.00, 4),
            (87.31, 4), (98.00, 4), (110.00, 4), (103.83, 4),
        ]
        total = sum(d for _, d in melody) * beat * 0.5
        n = int(total * SAMPLE_RATE)
        mix = [0.0] * n

        def add_note(freq, start_s, dur_s, vol, wave):
            start = int(start_s * SAMPLE_RATE)
            length = int(dur_s * SAMPLE_RATE)
            for i in range(length):
                idx = start + i
                if idx >= n:
                    break
                t = i / SAMPLE_RATE
                env = 1.0
                a = 0.01
                rel = 0.08
                if t < a:
                    env = t / a
                remain = dur_s - t
                if remain < rel:
                    env *= max(0.0, remain / rel)
                if wave == "square":
                    v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
                    v *= 0.55
                elif wave == "triangle":
                    v = 2 * abs(2 * ((freq * t) % 1) - 1) - 1
                else:
                    v = math.sin(2 * math.pi * freq * t)
                mix[idx] += vol * v * env

        t = 0.0
        for freq, dur in melody:
            add_note(freq, t, dur * beat * 0.5 * 0.92, 0.22, "triangle")
            add_note(freq * 2, t, dur * beat * 0.5 * 0.7, 0.07, "sine")
            t += dur * beat * 0.5
        t = 0.0
        for freq, dur in bass:
            add_note(freq, t, dur * beat * 0.5 * 0.95, 0.18, "square")
            t += dur * beat * 0.5

        # hat on eighths
        hat_step = beat * 0.5
        t = 0.0
        while t < total:
            add_note(8000, t, 0.03, 0.035, "sine")
            t += hat_step

        peak = max(1e-6, max(abs(x) for x in mix))
        data = array.array("h")
        for x in mix:
            data.append(int(32767 * 0.85 * (x / peak)))
        self.music = self._sound_from(data)
        self.music.set_volume(self.music_volume)

    def _play(self, name):
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound is None:
            return
        try:
            sound.play()
        except pygame.error:
            pass

    def play_rotate(self):
        self._play("rotate")

    def play_move(self):
        self._play("move")

    def play_drop(self):
        pass  # gravity ticks should be silent

    def play_lock(self):
        self._play("lock")

    def play_hard_drop(self):
        self._play("hard_drop")

    def play_hold(self):
        self._play("hold")

    def play_line_clear(self):
        self._play("line_clear")

    def play_tetris(self):
        self._play("tetris")

    def play_tspin(self):
        self._play("tspin")

    def play_combo(self):
        self._play("combo")

    def play_game_over(self):
        self._play("game_over")
        self.stop_music()

    def play_level_up(self):
        self._play("level_up")

    def play_select(self):
        self._play("select")

    def play_back_to_back(self):
        self._play("back_to_back")

    def start_music(self):
        if not self.enabled or not self.music_on or not self.music:
            return
        try:
            self.music.play(loops=-1)
        except pygame.error:
            pass

    def stop_music(self):
        if self.music:
            try:
                self.music.stop()
            except pygame.error:
                pass

    def toggle_music(self):
        self.music_on = not self.music_on
        if self.music_on:
            self.start_music()
        else:
            self.stop_music()
        return self.music_on

    def toggle(self):
        self.enabled = not self.enabled
        if not self.enabled:
            self.stop_music()
        return self.enabled
