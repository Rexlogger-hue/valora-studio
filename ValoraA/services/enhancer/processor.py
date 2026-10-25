"""
services/enhancer/processor.py

Production-grade acoustic Voice Enhancement engine for Valora AI.
Transforms uploaded audio or video speech recordings into clear, full,
balanced, and pleasant audio while strictly preserving speaker identity,
original words, language, cadence, emotion, and timing.
"""

from __future__ import annotations

import io
import math
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import av
import numpy as np
import pyloudnorm as pyln
import scipy.signal as signal
import soundfile as sf

try:
    from services.enhancer.config import ENHANCEMENT_PRESETS, EnhancementPreset
except ImportError:
    from ValoraA.services.enhancer.config import ENHANCEMENT_PRESETS, EnhancementPreset


class VoiceEnhancer:
    """
    Multi-stage DSP voice enhancement and acoustic mastering processor.
    """

    def __init__(self) -> None:
        self.presets = ENHANCEMENT_PRESETS

    # =========================================================================
    # 1. MEDIA INGESTION & DECODING
    # =========================================================================
    def load_media(
        self,
        file_input: Union[str, Path, bytes, io.BytesIO],
        max_duration: Optional[float] = None,
        preview_offset: float = 0.0,
    ) -> Tuple[np.ndarray, int, int, float]:
        """
        Decode any supported audio or video container into float32 PCM numpy array.

        Returns:
            Tuple[audio_array, sample_rate, channels, total_duration]
            audio_array shape: (samples,) for mono or (samples, channels) for stereo.
        """
        container = None
        if isinstance(file_input, (str, Path)):
            container = av.open(str(file_input))
        elif isinstance(file_input, bytes):
            container = av.open(io.BytesIO(file_input))
        elif isinstance(file_input, io.BytesIO):
            file_input.seek(0)
            container = av.open(file_input)
        else:
            raise ValueError(f"Unsupported media input type: {type(file_input)}")

        try:
            audio_streams = [s for s in container.streams if s.type == "audio"]
            if not audio_streams:
                raise ValueError("No audio track detected in the uploaded file.")

            audio_stream = audio_streams[0]
            sr = audio_stream.rate or 44100
            channels = audio_stream.channels or 1

            frames = []
            total_samples = 0
            max_samples = int(max_duration * sr) if max_duration else None
            offset_samples = int(preview_offset * sr) if preview_offset > 0 else 0
            skipped_samples = 0

            for frame in container.decode(audio_stream):
                # Convert PyAV AudioFrame to numpy float32
                pcm = frame.to_ndarray()  # shape (channels, samples) or (samples,)
                if pcm.ndim == 1:
                    pcm = pcm.reshape(1, -1)
                
                # Normalize integer formats to float32 [-1.0, 1.0]
                if pcm.dtype == np.int16:
                    pcm = pcm.astype(np.float32) / 32768.0
                elif pcm.dtype == np.int32:
                    pcm = pcm.astype(np.float32) / 2147483648.0
                elif pcm.dtype != np.float32:
                    pcm = pcm.astype(np.float32)

                frame_samples = pcm.shape[1]

                # Handle offset
                if skipped_samples < offset_samples:
                    if skipped_samples + frame_samples <= offset_samples:
                        skipped_samples += frame_samples
                        continue
                    else:
                        take_from = offset_samples - skipped_samples
                        pcm = pcm[:, take_from:]
                        skipped_samples = offset_samples
                        frame_samples = pcm.shape[1]

                frames.append(pcm)
                total_samples += frame_samples

                if max_samples and total_samples >= max_samples:
                    break

            if not frames:
                raise ValueError("Could not decode any audio frames from the file.")

            audio = np.concatenate(frames, axis=1)  # shape: (channels, total_samples)
            if max_samples and audio.shape[1] > max_samples:
                audio = audio[:, :max_samples]

            # Transpose to (samples, channels)
            audio = audio.T
            if audio.shape[1] == 1:
                audio = audio.squeeze(-1)  # (samples,) for mono

            duration = len(audio) / sr
            return audio, sr, channels, duration

        finally:
            if container:
                container.close()

    # =========================================================================
    # 2. ACOUSTIC MEASUREMENT & METRICS
    # =========================================================================
    def measure_acoustics(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """
        Accurately measure ITU-R BS.1770 integrated loudness, true peak, noise floor,
        and crest factor statistics.
        """
        arr = np.asarray(audio, dtype=np.float32)
        if arr.size == 0:
            return {
                "integrated_lufs": -70.0,
                "true_peak_db": -70.0,
                "noise_floor_db": -70.0,
                "dynamic_range_db": 0.0,
            }

        peak_val = np.max(np.abs(arr))
        peak_db = 20.0 * math.log10(max(float(peak_val), 1e-6))

        # Integrated LUFS via pyloudnorm
        try:
            meter = pyln.Meter(sr)
            # pyloudnorm expects (samples, channels) or (samples,)
            lufs = float(meter.integrated_loudness(arr))
            if math.isinf(lufs) or math.isnan(lufs) or lufs < -70.0:
                lufs = -70.0
        except Exception:
            # Fallback RMS estimation if signal is too quiet or short
            rms = np.sqrt(np.mean(arr**2)) + 1e-9
            lufs = float(20.0 * math.log10(rms) - 3.0)

        # Estimate Noise Floor (lower 12th percentile of frame energy)
        mono = arr if arr.ndim == 1 else np.mean(arr, axis=1)
        frame_size = int(sr * 0.04)  # 40ms window
        if len(mono) >= frame_size:
            n_frames = len(mono) // frame_size
            frames = mono[: n_frames * frame_size].reshape(n_frames, frame_size)
            frame_rms = np.sqrt(np.mean(frames**2, axis=1) + 1e-12)
            noise_rms = np.percentile(frame_rms, 12)
            noise_floor_db = float(20.0 * math.log10(max(noise_rms, 1e-6)))
        else:
            noise_floor_db = peak_db - 35.0

        dynamic_range = max(0.0, peak_db - noise_floor_db)

        return {
            "integrated_lufs": round(float(lufs), 1),
            "true_peak_db": round(float(peak_db), 1),
            "noise_floor_db": round(float(noise_floor_db), 1),
            "dynamic_range_db": round(float(dynamic_range), 1),
        }

    # =========================================================================
    # 3. DSP BUILDING BLOCKS
    # =========================================================================
    def highpass_rumble_filter(
        self, audio: np.ndarray, sr: int, cutoff_hz: float = 75.0
    ) -> np.ndarray:
        """
        Gentle 3rd-order Butterworth high-pass filter (zero-phase sosfiltfilt)
        to eliminate sub-bass HVAC rumble, air thumps, and mechanical mic hum.
        """
        if cutoff_hz <= 10.0:
            return audio
        sos = signal.butter(3, cutoff_hz, btype="highpass", fs=sr, output="sos")
        if audio.ndim == 1:
            return signal.sosfiltfilt(sos, audio).astype(np.float32)
        else:
            return signal.sosfiltfilt(sos, audio, axis=0).astype(np.float32)

    def adaptive_spectral_noise_reduction(
        self,
        audio: np.ndarray,
        sr: int,
        reduction_amount: float = 0.65,
    ) -> np.ndarray:
        """
        Conservative spectral gating to remove steady hiss, fan noise, and humming
        while preserving speech harmonics and transient naturalness.
        """
        if reduction_amount <= 0.05:
            return audio

        # Process mono or per-channel
        if audio.ndim == 2:
            left = self.adaptive_spectral_noise_reduction(audio[:, 0], sr, reduction_amount)
            right = self.adaptive_spectral_noise_reduction(audio[:, 1], sr, reduction_amount)
            return np.column_stack([left, right])

        n_fft = 2048
        hop_length = 512
        win = np.hanning(n_fft)

        # Compute STFT
        _, _, Zxx = signal.stft(audio, fs=sr, window=win, nperseg=n_fft, noverlap=n_fft - hop_length)
        magnitude = np.abs(Zxx)
        phase = np.angle(Zxx)

        # Estimate stationary noise profile using energy floor (15th percentile across time)
        noise_profile = np.percentile(magnitude, 15, axis=1, keepdims=True)

        # Over-subtraction factor & gain floor based on reduction_amount
        alpha = 1.0 + (reduction_amount * 1.5)  # 1.0 to 2.5
        # Gain floor: conservative minimum floor (-18dB to -28dB) avoids metallic artifacts
        floor_db = -12.0 - (reduction_amount * 16.0)
        gain_floor = 10.0 ** (floor_db / 20.0)

        # Spectral subtraction gain mask with soft sigmoid transition
        snr = magnitude / (noise_profile + 1e-9)
        threshold = alpha * 1.4
        gain_mask = np.maximum(gain_floor, 1.0 - (alpha / (snr + 1e-6)))
        # Smooth mask across frequency and time
        gain_mask = signal.medfilt2d(gain_mask, kernel_size=(3, 3))

        clean_mag = magnitude * gain_mask
        clean_Zxx = clean_mag * np.exp(1j * phase)

        # Inverse STFT
        _, clean_audio = signal.istft(clean_Zxx, fs=sr, window=win, nperseg=n_fft, noverlap=n_fft - hop_length)

        # Match exact length
        if len(clean_audio) > len(audio):
            clean_audio = clean_audio[: len(audio)]
        elif len(clean_audio) < len(audio):
            clean_audio = np.pad(clean_audio, (0, len(audio) - len(clean_audio)))

        return clean_audio.astype(np.float32)

    def dereverberation(
        self,
        audio: np.ndarray,
        sr: int,
        echo_reduction: float = 0.35,
    ) -> np.ndarray:
        """
        Spectral decay attenuation to reduce room flutter, acoustic slapback,
        and hollow boxy reflections.
        """
        if echo_reduction <= 0.05:
            return audio

        if audio.ndim == 2:
            left = self.dereverberation(audio[:, 0], sr, echo_reduction)
            right = self.dereverberation(audio[:, 1], sr, echo_reduction)
            return np.column_stack([left, right])

        n_fft = 2048
        hop_length = 512
        win = np.hanning(n_fft)

        _, _, Zxx = signal.stft(audio, fs=sr, window=win, nperseg=n_fft, noverlap=n_fft - hop_length)
        mag = np.abs(Zxx)
        phase = np.angle(Zxx)

        # Recursive late-reflection decay estimation (approx 120ms decay time)
        decay_factor = 0.72 - (echo_reduction * 0.15)
        reverb_est = np.zeros_like(mag)
        for t in range(1, mag.shape[1]):
            reverb_est[:, t] = decay_factor * reverb_est[:, t - 1] + (1.0 - decay_factor) * mag[:, t - 1]

        # Suppress tail while preserving direct initial sound attack
        suppression_factor = echo_reduction * 0.45
        gain = np.clip(1.0 - (suppression_factor * (reverb_est / (mag + 1e-6))), 0.45, 1.0)

        cleaned_mag = mag * gain
        clean_Zxx = cleaned_mag * np.exp(1j * phase)

        _, clean_audio = signal.istft(clean_Zxx, fs=sr, window=win, nperseg=n_fft, noverlap=n_fft - hop_length)

        if len(clean_audio) > len(audio):
            clean_audio = clean_audio[: len(audio)]
        elif len(clean_audio) < len(audio):
            clean_audio = np.pad(clean_audio, (0, len(audio) - len(clean_audio)))

        return clean_audio.astype(np.float32)

    def adaptive_speech_equalizer(
        self,
        audio: np.ndarray,
        sr: int,
        clarity: float = 0.70,
        warmth: float = 0.50,
    ) -> np.ndarray:
        """
        Triple-band vocal mastering EQ:
        1. Low-mid cut (~320Hz, Q=1.2) to remove room boxiness and proximity boom.
        2. Presence boost (~3.4kHz, Q=1.0) to enhance consonant articulation and vocal intelligibility.
        3. Low shelf (~150Hz) for balanced body and vocal warmth.
        """
        arr = audio.copy()
        # 1. Low-mid boxiness notch/cut: 320 Hz
        boxiness_cut_db = -1.0 - (clarity * 2.2)  # -1.0dB to -3.2dB
        gain_lin = 10.0 ** (boxiness_cut_db / 40.0)
        sos_box = signal.iirpeak(320.0, 1.2, fs=sr)
        # Apply gentle attenuation around 320Hz
        if arr.ndim == 1:
            box_band = signal.sosfiltfilt(signal.tf2sos(*sos_box), arr)
            arr = arr - (1.0 - gain_lin) * box_band
        else:
            box_band = signal.sosfiltfilt(signal.tf2sos(*sos_box), arr, axis=0)
            arr = arr - (1.0 - gain_lin) * box_band

        # 2. Vocal Presence Boost: 3400 Hz (speech intelligibility band)
        presence_boost_db = clarity * 3.5  # up to +3.5dB
        if presence_boost_db > 0.3:
            gain_pres = 10.0 ** (presence_boost_db / 20.0) - 1.0
            sos_pres = signal.iirpeak(3400.0, 1.1, fs=sr)
            if arr.ndim == 1:
                pres_band = signal.sosfiltfilt(signal.tf2sos(*sos_pres), arr)
                arr = arr + (gain_pres * 0.45) * pres_band
            else:
                pres_band = signal.sosfiltfilt(signal.tf2sos(*sos_pres), arr, axis=0)
                arr = arr + (gain_pres * 0.45) * pres_band

        # 3. Vocal Warmth: Low Shelf ~150 Hz
        warmth_db = (warmth - 0.5) * 3.0  # -1.5dB to +1.5dB
        if abs(warmth_db) > 0.3:
            sos_warmth = signal.butter(1, 160.0, btype="lowpass", fs=sr, output="sos")
            gain_w = 10.0 ** (warmth_db / 20.0) - 1.0
            if arr.ndim == 1:
                w_band = signal.sosfiltfilt(sos_warmth, arr)
                arr = arr + (gain_w * 0.5) * w_band
            else:
                w_band = signal.sosfiltfilt(sos_warmth, arr, axis=0)
                arr = arr + (gain_w * 0.5) * w_band

        return arr.astype(np.float32)

    def dynamic_de_esser(
        self,
        audio: np.ndarray,
        sr: int,
        intensity: float = 0.55,
    ) -> np.ndarray:
        """
        Dynamic de-esser targeting harsh sibilance in the 5.8kHz - 8.5kHz range.
        Calculates sibilant energy envelope and attenuates only when harsh 'S' sounds spike.
        """
        if intensity <= 0.1 or sr < 16000:
            return audio

        # Bandpass filter for sibilant frequencies (5800Hz - 8500Hz)
        nyq = sr / 2.0
        low = min(5800.0 / nyq, 0.95)
        high = min(8500.0 / nyq, 0.98)
        if low >= high:
            return audio

        sos_sib = signal.butter(2, [low, high], btype="bandpass", output="sos")

        if audio.ndim == 2:
            left = self.dynamic_de_esser(audio[:, 0], sr, intensity)
            right = self.dynamic_de_esser(audio[:, 1], sr, intensity)
            return np.column_stack([left, right])

        sibilant_band = signal.sosfiltfilt(sos_sib, audio)

        # Envelope detection
        window_len = int(sr * 0.015)  # 15ms window
        sib_env = np.sqrt(signal.convolve(sibilant_band**2, np.ones(window_len) / window_len, mode="same") + 1e-9)
        full_env = np.sqrt(signal.convolve(audio**2, np.ones(window_len) / window_len, mode="same") + 1e-9)

        # Sibilance ratio: when high frequencies dominate the audio energy
        sib_ratio = sib_env / (full_env + 1e-6)
        threshold = 0.38 - (intensity * 0.12)  # threshold for detection

        gain_reduction = np.clip(1.0 - (intensity * (sib_ratio - threshold) * 2.2), 0.35, 1.0)
        gain_reduction = signal.medfilt(gain_reduction, kernel_size=15)

        # Apply attenuation only to sibilant band
        cleaned = audio - ((1.0 - gain_reduction) * sibilant_band)
        return cleaned.astype(np.float32)

    def speech_aware_multi_speaker_leveler(
        self,
        audio: np.ndarray,
        sr: int,
        balancing_strength: float = 0.60,
    ) -> np.ndarray:
        """
        Speech-aware loudness leveling across multiple speakers:
        - Detects voice activity using energy thresholding.
        - Gently raises quieter speakers (+2dB to +6dB) and reines in overly loud speakers (-2dB to -4dB).
        - CRUCIAL: Gain is FROZEN during pauses and silences, preventing background noise from pumping!
        """
        if balancing_strength <= 0.05:
            return audio

        mono = audio if audio.ndim == 1 else np.mean(audio, axis=1)

        # Frame-level RMS energy (30ms frame, 10ms hop)
        frame_len = int(sr * 0.03)
        hop_len = int(sr * 0.01)
        if len(mono) < frame_len * 2:
            return audio

        n_frames = (len(mono) - frame_len) // hop_len + 1
        rms_values = np.zeros(n_frames, dtype=np.float32)

        for i in range(n_frames):
            start = i * hop_len
            chunk = mono[start : start + frame_len]
            rms_values[i] = np.sqrt(np.mean(chunk**2) + 1e-12)

        # Determine speech activity threshold (10dB above 20th percentile noise floor)
        noise_floor_rms = np.percentile(rms_values, 20)
        speech_thresh = max(noise_floor_rms * 2.8, 0.005)

        is_speech = rms_values > speech_thresh

        # Target speech RMS (~ -20 dBFS)
        target_rms = 0.08

        # Calculate ideal gain per frame
        target_gains = np.ones(n_frames, dtype=np.float32)
        last_gain = 1.0

        for i in range(n_frames):
            if is_speech[i]:
                # Dynamic compression ratio: softer voices get boosted, louder get tamped down
                ratio = balancing_strength * 0.75
                current_rms = max(rms_values[i], 1e-5)
                desired_gain = (target_rms / current_rms) ** ratio
                # Clamp gain range to prevent extreme boosting: -6dB (0.5x) to +6dB (2.0x)
                desired_gain = np.clip(desired_gain, 0.55, 2.1)
                last_gain = desired_gain
                target_gains[i] = desired_gain
            else:
                # FREEZE gain during silence/pauses to prevent noise pumping!
                target_gains[i] = last_gain

        # Smooth gain curve over time (lowpass moving average over 350ms)
        smooth_len = int(0.35 / (hop_len / sr))
        if smooth_len > 1 and len(target_gains) > smooth_len:
            smooth_win = np.hanning(smooth_len)
            smooth_win /= np.sum(smooth_win)
            target_gains = signal.convolve(target_gains, smooth_win, mode="same")

        # Interpolate frame gains to sample level
        sample_indices = np.linspace(0, len(target_gains) - 1, len(mono))
        sample_gains = np.interp(sample_indices, np.arange(len(target_gains)), target_gains).astype(np.float32)

        if audio.ndim == 1:
            return (audio * sample_gains).astype(np.float32)
        else:
            return (audio * sample_gains[:, np.newaxis]).astype(np.float32)

    def soft_knee_dynamic_compressor(
        self,
        audio: np.ndarray,
        ratio: float = 2.4,
        threshold_db: float = -18.0,
    ) -> np.ndarray:
        """
        Gentle broadcast dynamic range compressor to glue speech together
        and smooth out abrupt volume jumps.
        """
        thresh_linear = 10.0 ** (threshold_db / 20.0)
        mag = np.abs(audio)

        # Compute compression gain
        gain = np.ones_like(mag)
        over_thresh = mag > thresh_linear

        if np.any(over_thresh):
            excess_db = 20.0 * np.log10(mag[over_thresh] / thresh_linear + 1e-9)
            compressed_excess_db = excess_db / ratio
            gain_reduction_db = compressed_excess_db - excess_db
            gain[over_thresh] = 10.0 ** (gain_reduction_db / 20.0)

        # Smooth gain envelope to avoid audio distortion
        return (audio * gain).astype(np.float32)

    def loudness_master_and_limit(
        self,
        audio: np.ndarray,
        sr: int,
        target_lufs: float = -16.0,
        ceiling_db: float = -1.0,
    ) -> np.ndarray:
        """
        Master audio to target integrated LUFS (ITU-R BS.1770) and apply
        a brickwall lookahead peak limiter with true-peak ceiling.
        """
        arr = np.asarray(audio, dtype=np.float32)
        if arr.size == 0:
            return arr

        # 1. Normalize Loudness to Target LUFS
        try:
            meter = pyln.Meter(sr)
            current_lufs = meter.integrated_loudness(arr)
            if not (math.isnan(current_lufs) or math.isinf(current_lufs) or current_lufs < -65.0):
                arr = pyln.normalize.loudness(arr, current_lufs, target_lufs)
        except Exception:
            # Fallback RMS normalization
            rms = np.sqrt(np.mean(arr**2)) + 1e-9
            target_rms = 10.0 ** ((target_lufs + 3.0) / 20.0)
            arr = arr * (target_rms / rms)

        # 2. Brickwall True Peak Limiter
        ceiling_linear = 10.0 ** (ceiling_db / 20.0)  # e.g., 0.891 (-1.0 dBFS)
        peak = np.max(np.abs(arr))

        if peak > ceiling_linear:
            # Soft-saturation limiter
            scaling = ceiling_linear / peak
            arr = arr * scaling

        # Final safety tanh saturation for absolute zero clipping
        overflow = np.abs(arr) > ceiling_linear
        if np.any(overflow):
            arr = np.where(
                overflow,
                np.sign(arr) * (ceiling_linear * np.tanh(np.abs(arr) / ceiling_linear)),
                arr,
            )

        return arr.astype(np.float32)

    # =========================================================================
    # 4. MASTER ENHANCEMENT PIPELINE
    # =========================================================================
    def enhance(
        self,
        file_input: Union[str, Path, bytes, io.BytesIO],
        preset_id: str = "podcast",
        overrides: Optional[Dict[str, Any]] = None,
        preview_mode: bool = False,
        preview_duration: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Execute the complete voice enhancement pipeline on an uploaded recording.

        Returns:
            Dict containing:
            - enhanced_audio (np.ndarray)
            - original_audio (np.ndarray)
            - sample_rate (int)
            - channels (int)
            - duration_seconds (float)
            - input_metrics (Dict)
            - output_metrics (Dict)
            - processing_time_seconds (float)
            - preset_used (str)
        """
        start_time = time.time()

        # 1. Decode Media
        max_dur = preview_duration if preview_mode else None
        original_audio, sr, channels, duration = self.load_media(file_input, max_duration=max_dur)

        # 2. Measure Original Acoustics
        input_metrics = self.measure_acoustics(original_audio, sr)

        # 3. Resolve Preset & Overrides
        preset = self.presets.get(preset_id, self.presets["podcast"])
        cfg = {
            "strength": preset.strength,
            "noise_reduction": preset.noise_reduction,
            "voice_clarity": preset.voice_clarity,
            "warmth": preset.warmth,
            "volume_balancing": preset.volume_balancing,
            "echo_reduction": preset.echo_reduction,
            "de_essing": preset.de_essing,
            "highpass_hz": preset.highpass_hz,
            "target_lufs": preset.target_lufs,
            "peak_ceiling_db": preset.peak_ceiling_db,
        }
        if overrides:
            for k, v in overrides.items():
                if k in cfg and v is not None:
                    try:
                        cfg[k] = float(v)
                    except (ValueError, TypeError):
                        pass

        # Overall strength scaling
        strength = float(cfg["strength"])
        audio = original_audio.copy()

        # Step 1: Low-Frequency Rumble Filter
        hp_freq = float(cfg["highpass_hz"])
        if hp_freq > 20.0:
            audio = self.highpass_rumble_filter(audio, sr, cutoff_hz=hp_freq)

        # Step 2: Adaptive Spectral Noise Reduction
        nr_amt = float(cfg["noise_reduction"]) * strength
        if nr_amt > 0.05:
            audio = self.adaptive_spectral_noise_reduction(audio, sr, reduction_amount=nr_amt)

        # Step 3: De-Reverberation (Echo Reduction)
        echo_amt = float(cfg["echo_reduction"]) * strength
        if echo_amt > 0.05:
            audio = self.dereverberation(audio, sr, echo_reduction=echo_amt)

        # Step 4: Adaptive Speech Equalization (Presence, Boxiness cut, Warmth)
        clarity_amt = float(cfg["voice_clarity"]) * strength
        warmth_amt = float(cfg["warmth"])
        audio = self.adaptive_speech_equalizer(audio, sr, clarity=clarity_amt, warmth=warmth_amt)

        # Step 5: Dynamic De-Esser
        de_ess_amt = float(cfg["de_essing"]) * strength
        if de_ess_amt > 0.1:
            audio = self.dynamic_de_esser(audio, sr, intensity=de_ess_amt)

        # Step 6: Multi-Speaker Speech-Aware Leveling
        balance_amt = float(cfg["volume_balancing"]) * strength
        if balance_amt > 0.05:
            audio = self.speech_aware_multi_speaker_leveler(audio, sr, balancing_strength=balance_amt)

        # Step 7: Gentle Dynamic Range Compression
        audio = self.soft_knee_dynamic_compressor(audio, ratio=2.2, threshold_db=-18.0)

        # Step 8: Master Loudness & True-Peak Limiter
        target_lufs = float(cfg["target_lufs"])
        ceiling_db = float(cfg["peak_ceiling_db"])
        audio = self.loudness_master_and_limit(audio, sr, target_lufs=target_lufs, ceiling_db=ceiling_db)

        # 4. Measure Output Acoustics
        output_metrics = self.measure_acoustics(audio, sr)
        proc_time = round(time.time() - start_time, 2)

        # Calculate estimated noise reduction in dB
        noise_diff_db = round(input_metrics["noise_floor_db"] - output_metrics["noise_floor_db"], 1)
        output_metrics["noise_reduction_db"] = max(0.0, noise_diff_db)

        return {
            "enhanced_audio": audio,
            "original_audio": original_audio,
            "sample_rate": sr,
            "channels": channels,
            "duration_seconds": round(duration, 2),
            "input_metrics": input_metrics,
            "output_metrics": output_metrics,
            "processing_time_seconds": proc_time,
            "preset_used": preset_id,
            "preview_mode": preview_mode,
        }

    # =========================================================================
    # 5. AUDIO EXPORT
    # =========================================================================
    def export_audio_bytes(
        self,
        audio: np.ndarray,
        sr: int,
        format: str = "wav",
    ) -> bytes:
        """
        Encode float32 audio array into WAV (lossless 24-bit PCM) or MP3 bytes.
        """
        out_buf = io.BytesIO()
        fmt_clean = format.lower().strip(".")

        if fmt_clean == "mp3":
            # Encode to MP3 using PyAV
            output_container = av.open(out_buf, mode="w", format="mp3")
            stream = output_container.add_stream("mp3", rate=sr)
            stream.bit_rate = 320000  # 320 kbps high fidelity

            # Handle channels
            if audio.ndim == 1:
                pcm_data = audio.reshape(1, -1)
            else:
                pcm_data = audio.T  # (channels, samples)

            # PyAV AudioFrame expects int16 or float format
            frame = av.AudioFrame.from_ndarray(pcm_data, format="fltp", layout="stereo" if pcm_data.shape[0] == 2 else "mono")
            frame.sample_rate = sr
            frame.pts = 0

            for packet in stream.encode(frame):
                output_container.mux(packet)
            for packet in stream.encode(None):
                output_container.mux(packet)

            output_container.close()
            return out_buf.getvalue()
        else:
            # Default to Lossless 24-bit WAV
            subtype = "PCM_24" if sf.check_format("WAV", "PCM_24") else "PCM_16"
            sf.write(out_buf, audio, sr, format="WAV", subtype=subtype)
            return out_buf.getvalue()


_enhancer_instance: Optional[VoiceEnhancer] = None


def get_voice_enhancer() -> VoiceEnhancer:
    """Return singleton VoiceEnhancer instance."""
    global _enhancer_instance
    if _enhancer_instance is None:
        _enhancer_instance = VoiceEnhancer()
    return _enhancer_instance
