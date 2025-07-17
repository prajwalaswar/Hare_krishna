# backend/voice_processor.py - Voice processing and speaker detection
import speech_recognition as sr
import numpy as np
import librosa
import soundfile as sf
import tempfile
import os
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class VoiceProcessor:
    """Handles voice recording, transcription, and speaker detection"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Calibrate microphone
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("Microphone calibrated successfully")
        except Exception as e:
            logger.error(f"Microphone calibration failed: {e}")
    
    def transcribe_audio(self, audio_file_path: str) -> Tuple[str, float]:
        """
        Transcribe audio file to text
        Returns: (transcribed_text, confidence_score)
        """
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data, language='en-US')
                
                # Simple confidence estimation based on text length and clarity
                confidence = min(0.95, len(text.split()) / 10.0 + 0.5)
                
                return text, confidence
                
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return "", 0.0
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return "", 0.0
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return "", 0.0
    
    def detect_speaker(self, audio_file_path: str) -> Tuple[str, float]:
        """
        Detect if speaker is doctor or patient based on audio characteristics
        Returns: (speaker_type, confidence)
        """
        try:
            # Load audio file
            y, sr_rate = librosa.load(audio_file_path, sr=None)
            
            # Extract audio features
            features = self._extract_audio_features(y, sr_rate)
            
            # Simple rule-based speaker detection
            # This is a basic implementation - in production, you'd use ML models
            speaker, confidence = self._classify_speaker(features)
            
            return speaker, confidence
            
        except Exception as e:
            logger.error(f"Speaker detection error: {e}")
            # Default fallback
            return "Patient", 0.5
    
    def _extract_audio_features(self, audio_data: np.ndarray, sample_rate: int) -> dict:
        """Extract audio features for speaker classification"""
        try:
            # Fundamental frequency (pitch)
            pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sample_rate)
            pitch_mean = np.mean(pitches[pitches > 0]) if len(pitches[pitches > 0]) > 0 else 0
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]
            spectral_mean = np.mean(spectral_centroids)
            
            # Energy/volume
            rms = librosa.feature.rms(y=audio_data)[0]
            energy_mean = np.mean(rms)
            
            # Speaking rate (rough estimation)
            tempo, _ = librosa.beat.beat_track(y=audio_data, sr=sample_rate)
            
            return {
                'pitch_mean': pitch_mean,
                'spectral_centroid': spectral_mean,
                'energy': energy_mean,
                'tempo': tempo,
                'duration': len(audio_data) / sample_rate
            }
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return {
                'pitch_mean': 0,
                'spectral_centroid': 0,
                'energy': 0,
                'tempo': 0,
                'duration': 0
            }
    
    def _classify_speaker(self, features: dict) -> Tuple[str, float]:
        """
        Classify speaker based on audio features
        Simple rule-based approach - replace with ML model for better accuracy
        """
        try:
            pitch = features.get('pitch_mean', 0)
            energy = features.get('energy', 0)
            spectral = features.get('spectral_centroid', 0)
            
            # Simple heuristics (these would be learned from training data in real system)
            doctor_score = 0.0
            patient_score = 0.0
            
            # Doctors often speak with more authority (higher energy, lower pitch variation)
            if energy > 0.02:  # Higher energy
                doctor_score += 0.3
            else:
                patient_score += 0.3
                
            # Professional speaking patterns (this is very simplified)
            if spectral > 2000:  # Clearer articulation
                doctor_score += 0.2
            else:
                patient_score += 0.2
                
            # Default slight bias toward patient (since they usually speak more)
            patient_score += 0.1
            
            # Determine speaker
            if doctor_score > patient_score:
                confidence = min(0.8, doctor_score)
                return "Doctor", confidence
            else:
                confidence = min(0.8, patient_score)
                return "Patient", confidence
                
        except Exception as e:
            logger.error(f"Speaker classification error: {e}")
            return "Patient", 0.5
    
    def process_audio_chunk(self, audio_bytes: bytes) -> Tuple[str, str, float]:
        """
        Process audio chunk and return transcription with speaker detection
        Returns: (transcribed_text, speaker, confidence)
        """
        try:
            # Save audio bytes to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            # Transcribe audio
            text, trans_confidence = self.transcribe_audio(temp_file_path)
            
            # Detect speaker
            speaker, speaker_confidence = self.detect_speaker(temp_file_path)
            
            # Combined confidence
            combined_confidence = (trans_confidence + speaker_confidence) / 2
            
            # Clean up
            os.unlink(temp_file_path)
            
            return text, speaker, combined_confidence
            
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            if 'temp_file_path' in locals():
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            return "", "Patient", 0.0
