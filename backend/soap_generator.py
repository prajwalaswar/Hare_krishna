# backend/soap_generator.py - SOAP note generation using AI
from groq import Groq
import os
from typing import List, Dict, Optional
from datetime import datetime
import logging
import sys

# Add shared models to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.models import ConversationMessage, SOAPNote

logger = logging.getLogger(__name__)

class SOAPGenerator:
    """Generates SOAP notes from doctor-patient conversations using AI"""
    
    def __init__(self, groq_api_key: str = None):
        """Initialize SOAP generator with Groq API"""
        # Use provided key or default (you should set this in environment)
        self.api_key = groq_api_key or ""
        
        try:
            self.groq_client = Groq(api_key=self.api_key)
            logger.info("Groq client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            self.groq_client = None
    
    def generate_soap_note(self, conversation: List[ConversationMessage], 
                          patient_name: str = "Unknown Patient") -> SOAPNote:
        """
        Generate SOAP note from conversation messages
        """
        try:
            # Format conversation for AI processing
            conversation_text = self._format_conversation(conversation)
            
            # Generate SOAP sections using AI
            soap_sections = self._generate_soap_sections(conversation_text)
            
            # Extract patient info from conversation
            patient_info = self._extract_patient_info(conversation_text)
            
            # Create SOAP note object
            soap_note = SOAPNote(
                patient_name=patient_info.get('name', patient_name),
                date=datetime.now().strftime("%d-%b-%Y"),
                age_gender=patient_info.get('age_gender'),
                reason_for_visit=patient_info.get('reason'),
                subjective=soap_sections['subjective'],
                objective=soap_sections['objective'],
                assessment=soap_sections['assessment'],
                plan=soap_sections['plan'],
                conversation_id=f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                generated_at=datetime.now(),
                confidence_score=soap_sections.get('confidence', 0.8)
            )
            
            return soap_note
            
        except Exception as e:
            logger.error(f"SOAP generation error: {e}")
            return self._create_fallback_soap_note(conversation, patient_name)
    
    def _format_conversation(self, conversation: List[ConversationMessage]) -> str:
        """Format conversation messages for AI processing"""
        formatted_lines = []
        
        for msg in conversation:
            timestamp = msg.timestamp
            speaker = msg.speaker
            text = msg.text
            formatted_lines.append(f"[{timestamp}] {speaker}: {text}")
        
        return "\n".join(formatted_lines)
    
    def _generate_soap_sections(self, conversation_text: str) -> Dict[str, str]:
        """Generate SOAP sections using Groq AI"""
        if not self.groq_client:
            return self._create_fallback_soap_sections(conversation_text)
        
        try:
            # System prompt for SOAP note generation
            system_prompt = """You are an expert medical assistant that generates SOAP notes from doctor-patient conversations.

SOAP Note Format:
- S (Subjective): What the patient reports - symptoms, concerns, history
- O (Objective): What the doctor observes - physical findings, vitals, test results  
- A (Assessment): Medical diagnosis or clinical impression
- P (Plan): Treatment plan, medications, follow-up, patient education

Analyze the conversation and extract information for each SOAP section. Be concise but thorough.
Focus on medical information and maintain professional medical language.
If information is missing for a section, note "Not documented in conversation"."""

            user_prompt = f"""Please generate a SOAP note from this doctor-patient conversation:

{conversation_text}

Return the response in this exact format:
SUBJECTIVE: [patient's reported symptoms and concerns]
OBJECTIVE: [doctor's observations and findings]  
ASSESSMENT: [medical diagnosis/impression]
PLAN: [treatment plan and recommendations]"""

            # Call Groq API
            response = self.groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            # Parse response
            soap_text = response.choices[0].message.content.strip()
            return self._parse_soap_response(soap_text)
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._create_fallback_soap_sections(conversation_text)
    
    def _parse_soap_response(self, soap_text: str) -> Dict[str, str]:
        """Parse AI response into SOAP sections"""
        sections = {
            'subjective': '',
            'objective': '',
            'assessment': '',
            'plan': '',
            'confidence': 0.8
        }
        
        try:
            lines = soap_text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('SUBJECTIVE:'):
                    current_section = 'subjective'
                    sections[current_section] = line.replace('SUBJECTIVE:', '').strip()
                elif line.startswith('OBJECTIVE:'):
                    current_section = 'objective'
                    sections[current_section] = line.replace('OBJECTIVE:', '').strip()
                elif line.startswith('ASSESSMENT:'):
                    current_section = 'assessment'
                    sections[current_section] = line.replace('ASSESSMENT:', '').strip()
                elif line.startswith('PLAN:'):
                    current_section = 'plan'
                    sections[current_section] = line.replace('PLAN:', '').strip()
                elif current_section and line:
                    sections[current_section] += ' ' + line
            
            return sections
            
        except Exception as e:
            logger.error(f"SOAP parsing error: {e}")
            return self._create_fallback_soap_sections("")
    
    def _extract_patient_info(self, conversation_text: str) -> Dict[str, str]:
        """Extract patient information from conversation"""
        info = {}
        
        # Simple extraction - in production, use NLP
        lines = conversation_text.lower()
        
        # Look for age mentions
        if 'year' in lines or 'age' in lines:
            # This is very basic - would need proper NLP
            info['age_gender'] = "Age/Gender mentioned in conversation"
        
        # Look for reason for visit
        if 'pain' in lines or 'problem' in lines or 'issue' in lines:
            info['reason'] = "Medical concern discussed"
        
        return info
    
    def _create_fallback_soap_sections(self, conversation_text: str) -> Dict[str, str]:
        """Create basic SOAP sections when AI is unavailable"""
        return {
            'subjective': "Patient reported symptoms and concerns during consultation. See conversation log for details.",
            'objective': "Clinical observations and examination findings to be documented.",
            'assessment': "Medical assessment based on patient consultation.",
            'plan': "Treatment plan and follow-up recommendations to be determined.",
            'confidence': 0.5
        }
    
    def _create_fallback_soap_note(self, conversation: List[ConversationMessage], 
                                  patient_name: str) -> SOAPNote:
        """Create fallback SOAP note when generation fails"""
        return SOAPNote(
            patient_name=patient_name,
            date=datetime.now().strftime("%d-%b-%Y"),
            subjective="Patient consultation completed. See conversation log.",
            objective="Clinical findings to be documented.",
            assessment="Medical assessment pending.",
            plan="Treatment plan to be determined.",
            conversation_id=f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now(),
            confidence_score=0.3
        )
