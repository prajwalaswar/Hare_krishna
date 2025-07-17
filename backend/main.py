# backend/main.py - FastAPI server for SOAP Note App
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys
import os
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional
import json

# Add shared models to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.models import ConversationMessage, ConversationSession, SOAPNote, APIResponse

# Import backend modules
try:
    from .voice_processor import VoiceProcessor
    from .soap_generator import SOAPGenerator
except ImportError:
    # Fallback for direct execution
    from voice_processor import VoiceProcessor
    from soap_generator import SOAPGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SOAP Note App API",
    description="Real-time voice processing and SOAP note generation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
voice_processor = VoiceProcessor()
soap_generator = SOAPGenerator()

# In-memory storage (use database in production)
active_sessions: Dict[str, ConversationSession] = {}
completed_sessions: Dict[str, ConversationSession] = {}

# WebSocket connections for real-time updates
active_connections: List[WebSocket] = []

class StartSessionRequest(BaseModel):
    session_name: Optional[str] = None

class StopSessionRequest(BaseModel):
    session_id: str

class GenerateSOAPRequest(BaseModel):
    session_id: str
    patient_name: Optional[str] = "Unknown Patient"

@app.get("/")
async def root():
    """Health check endpoint"""
    return APIResponse(
        success=True,
        message="SOAP Note App API is running!",
        data={"version": "1.0.0", "status": "healthy"}
    )

@app.post("/session/start")
async def start_session(request: StartSessionRequest):
    """Start a new conversation session"""
    try:
        session_id = str(uuid.uuid4())
        session = ConversationSession(
            session_id=session_id,
            messages=[],
            start_time=datetime.now(),
            status="active"
        )
        
        active_sessions[session_id] = session
        
        logger.info(f"Started new session: {session_id}")
        
        return APIResponse(
            success=True,
            message="Session started successfully",
            data={"session_id": session_id}
        )
        
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/stop")
async def stop_session(request: StopSessionRequest):
    """Stop an active conversation session"""
    try:
        session_id = request.session_id
        
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = active_sessions[session_id]
        session.end_time = datetime.now()
        session.status = "completed"
        
        # Move to completed sessions
        completed_sessions[session_id] = session
        del active_sessions[session_id]
        
        logger.info(f"Stopped session: {session_id}")
        
        return APIResponse(
            success=True,
            message="Session stopped successfully",
            data={"session_id": session_id, "message_count": len(session.messages)}
        )
        
    except Exception as e:
        logger.error(f"Failed to stop session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/process")
async def process_voice(session_id: str, audio: UploadFile = File(...)):
    """Process voice audio and add to conversation"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Active session not found")
        
        # Read audio data
        audio_bytes = await audio.read()
        
        # Process audio
        text, speaker, confidence = voice_processor.process_audio_chunk(audio_bytes)
        
        if not text.strip():
            return APIResponse(
                success=False,
                message="No speech detected in audio",
                data={"confidence": confidence}
            )
        
        # Create conversation message
        message = ConversationMessage(
            speaker=speaker,
            text=text,
            timestamp=datetime.now().strftime("%H:%M:%S"),
            confidence=confidence
        )
        
        # Add to session
        session = active_sessions[session_id]
        session.messages.append(message)
        
        # Broadcast to connected clients
        await broadcast_message(session_id, message)
        
        logger.info(f"Processed voice: {speaker} - {text[:50]}...")
        
        return APIResponse(
            success=True,
            message="Voice processed successfully",
            data={
                "speaker": speaker,
                "text": text,
                "confidence": confidence,
                "timestamp": message.timestamp
            }
        )
        
    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/conversation")
async def get_conversation(session_id: str):
    """Get conversation messages for a session"""
    try:
        # Check active sessions first
        if session_id in active_sessions:
            session = active_sessions[session_id]
        elif session_id in completed_sessions:
            session = completed_sessions[session_id]
        else:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return APIResponse(
            success=True,
            message="Conversation retrieved successfully",
            data={
                "session_id": session_id,
                "status": session.status,
                "messages": [msg.model_dump() for msg in session.messages],
                "message_count": len(session.messages)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/soap/generate")
async def generate_soap_note(request: GenerateSOAPRequest):
    """Generate SOAP note from conversation"""
    try:
        session_id = request.session_id
        
        # Get session (check both active and completed)
        if session_id in active_sessions:
            session = active_sessions[session_id]
        elif session_id in completed_sessions:
            session = completed_sessions[session_id]
        else:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not session.messages:
            raise HTTPException(status_code=400, detail="No conversation to analyze")
        
        # Generate SOAP note
        soap_note = soap_generator.generate_soap_note(
            conversation=session.messages,
            patient_name=request.patient_name
        )
        
        logger.info(f"Generated SOAP note for session: {session_id}")
        
        return APIResponse(
            success=True,
            message="SOAP note generated successfully",
            data=soap_note.model_dump()
        )
        
    except Exception as e:
        logger.error(f"SOAP generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/active")
async def get_active_sessions():
    """Get list of active sessions"""
    try:
        sessions_data = []
        for session_id, session in active_sessions.items():
            sessions_data.append({
                "session_id": session_id,
                "start_time": session.start_time.isoformat(),
                "message_count": len(session.messages),
                "status": session.status
            })
        
        return APIResponse(
            success=True,
            message="Active sessions retrieved",
            data={"sessions": sessions_data, "count": len(sessions_data)}
        )
        
    except Exception as e:
        logger.error(f"Failed to get active sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for real-time updates
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time conversation updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_message(session_id: str, message: ConversationMessage):
    """Broadcast new message to connected clients"""
    if active_connections:
        message_data = {
            "session_id": session_id,
            "message": message.model_dump()
        }
        
        # Remove disconnected connections
        disconnected = []
        for connection in active_connections:
            try:
                await connection.send_text(json.dumps(message_data))
            except:
                disconnected.append(connection)
        
        for conn in disconnected:
            active_connections.remove(conn)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002, reload=True)
