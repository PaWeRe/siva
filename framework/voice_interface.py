"""
Voice Interface for SIVA Framework.

Handles speech-to-text, text-to-speech, and intent extraction.
"""

import os
from typing import Dict, Any, Optional
from openai import OpenAI
from .config import VoiceConfig


class VoiceInterface:
    """Universal voice processing interface for any domain."""

    def __init__(self, config: VoiceConfig):
        self.config = config
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("[VoiceInterface] Warning: OPENAI_API_KEY not found in environment")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)

    def process_voice_input(self, audio_stream: bytes) -> str:
        """Convert voice input to text."""
        try:
            # For now, assume audio_stream is already processed
            # In a real implementation, this would handle raw audio
            response = self.client.audio.transcriptions.create(
                model=self.config.stt_model,
                file=audio_stream,
                response_format="text"
            )
            return response
        except Exception as e:
            print(f"[VoiceInterface] Error processing voice input: {e}")
            return ""

    def extract_intent_and_data(self, text_input: str) -> Dict[str, Any]:
        """Extract intent and structured data from text input."""
        if not self.client:
            # Fallback when OpenAI client is not available
            return {
                "intent": "unknown",
                "data": {"text": text_input},
                "confidence": 0.0
            }
        
        # This is a simplified version - applications can override this
        system_prompt = f"""You are a {self.config.personality}. 
        Extract structured data from the user's input. Return a JSON object with:
        - intent: the user's main intent
        - data: relevant structured data
        - confidence: your confidence in the extraction (0-1)
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_input}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"[VoiceInterface] Error extracting intent: {e}")
            return {
                "intent": "unknown",
                "data": {"text": text_input},
                "confidence": 0.0
            }

    def generate_voice_response(self, text_response: str) -> bytes:
        """Convert text response to voice output."""
        try:
            # Use Cartesia TTS (like the original SIVA)
            from cartesia import AsyncCartesia
            import asyncio
            
            # This is a placeholder - in practice you'd implement async TTS
            # For now, just return empty bytes to avoid complexity
            print(f"[VoiceInterface] Would generate TTS for: {text_response[:50]}...")
            return b""
        except Exception as e:
            print(f"[VoiceInterface] Error generating voice response: {e}")
            return b""

    def get_system_prompt(self, domain: str = "general") -> str:
        """Get appropriate system prompt for the domain."""
        base_prompts = {
            "patient_intake": """You are a caring healthcare assistant helping with patient intake. 
            Collect patient information and assess symptoms for appropriate routing.""",
            
            "clinical_decision": """You are a clinical decision support assistant. 
            Help physicians with evidence-based recommendations and clinical reasoning.""",
            
            "general": f"""You are a {self.config.personality}. 
            Help users with their requests in a helpful and professional manner."""
        }
        
        return base_prompts.get(domain, base_prompts["general"])

    def format_response(self, decision: Any, domain_evidence: Dict[str, Any], 
                       should_escalate: bool = False) -> str:
        """Format a response based on decision and evidence."""
        if should_escalate:
            return "I'd like to have a human expert review this to ensure you get the best assistance."
        
        # Include domain evidence if available
        evidence_text = ""
        if domain_evidence and "citations" in domain_evidence:
            evidence_text = f" This recommendation is supported by {len(domain_evidence['citations'])} sources."
        
        return f"Based on the available evidence, I recommend: {decision}.{evidence_text}" 