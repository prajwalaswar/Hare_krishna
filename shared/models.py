# shared/models.py - Shared data models for SOAP Note App
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ConversationMessage(BaseModel):
    """Single message in conversation"""
    speaker: str  # "Doctor" or "Patient"
    text: str
    timestamp: str
    confidence: Optional[float] = None  # Speaker detection confidence

class ConversationSession(BaseModel):
    """Complete conversation session"""
    session_id: str
    messages: List[ConversationMessage]
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "active"  # active, completed, analyzing

class SOAPNote(BaseModel):
    """SOAP Note structure"""
    patient_name: Optional[str] = "Unknown Patient"
    date: str
    age_gender: Optional[str] = None
    reason_for_visit: Optional[str] = None
    
    # SOAP sections
    subjective: str
    objective: str
    assessment: str
    plan: str
    
    # Metadata
    conversation_id: str
    generated_at: datetime
    confidence_score: Optional[float] = None

class AudioTranscription(BaseModel):
    """Audio transcription result"""
    text: str
    speaker: str
    confidence: float
    duration: float

class APIResponse(BaseModel):
    """Standard API response"""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None
