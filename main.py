"""Pipecat-inspired patient intake voice bot, written from scratch."""
import os
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import openai

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")

# Simple in-memory session store (for demo purposes)
sessions: Dict[str, Dict[str, Any]] = {}

class UserMessage(BaseModel):
    session_id: str
    message: str

# IntakeProcessor logic, refactored for plain Python
class IntakeProcessor:
    def __init__(self, session: Dict[str, Any]):
        self.session = session
        if "messages" not in self.session:
            self.session["messages"] = []
            self.session["step"] = "intro"

    def next_prompt(self, user_message: Optional[str] = None) -> str:
        # Add user message to history if present
        if user_message:
            self.session["messages"].append({"role": "user", "content": user_message})

        step = self.session.get("step", "intro")
        if step == "intro":
            self.session["step"] = "verify_birthday"
            prompt = (
                "You are Jessica, an agent for a company called Tsidi Health Services. "
                "Your job is to collect important information from the user before their doctor visit. "
                "You're talking to Patrick Remerscheid. You should address the user by their first name and be polite and professional. "
                "You're not a medical professional, so you shouldn't provide any advice. Keep your responses short. "
                "Your job is to collect information to give to a doctor. Don't make assumptions about what values to plug into functions. "
                "Ask for clarification if a user response is ambiguous. Start by introducing yourself. "
                "Then, ask the user to confirm their identity by telling you their birthday, including the year."
            )
            self.session["messages"].append({"role": "system", "content": prompt})
            return prompt
        elif step == "verify_birthday":
            # For demo, expect '1983-01-01' as correct
            last_user = self.session["messages"][-1]["content"] if self.session["messages"] else ""
            if "1983-01-01" in last_user:
                self.session["step"] = "list_prescriptions"
                prompt = (
                    "Thank you for confirming your identity. Please list your current prescriptions. "
                    "Each prescription needs to have a medication name and a dosage. "
                    "Do not list any prescriptions with unknown dosages."
                )
                self.session["messages"].append({"role": "system", "content": prompt})
                return prompt
            else:
                prompt = (
                    "The birthday you provided is incorrect. Please try again and include the year (e.g., 1983-01-01)."
                )
                self.session["messages"].append({"role": "system", "content": prompt})
                return prompt
        elif step == "list_prescriptions":
            self.session["step"] = "list_allergies"
            prompt = (
                "Do you have any allergies? Please list them, or confirm if you have none."
            )
            self.session["messages"].append({"role": "system", "content": prompt})
            return prompt
        elif step == "list_allergies":
            self.session["step"] = "list_conditions"
            prompt = (
                "Do you have any medical conditions the doctor should know about? Please list them."
            )
            self.session["messages"].append({"role": "system", "content": prompt})
            return prompt
        elif step == "list_conditions":
            self.session["step"] = "list_visit_reasons"
            prompt = (
                "What is the reason for your doctor visit today?"
            )
            self.session["messages"].append({"role": "system", "content": prompt})
            return prompt
        elif step == "list_visit_reasons":
            self.session["step"] = "done"
            prompt = (
                "Thank you. The intake is complete. The doctor will see you soon."
            )
            self.session["messages"].append({"role": "system", "content": prompt})
            return prompt
        else:
            return "Intake is already complete."

    def get_history(self) -> List[Dict[str, str]]:
        return self.session.get("messages", [])

@app.post("/chat")
async def chat(user_message: UserMessage):
    # Get or create session
    session = sessions.setdefault(user_message.session_id, {})
    processor = IntakeProcessor(session)
    reply = processor.next_prompt(user_message.message)
    return {"reply": reply, "history": processor.get_history()}

@app.get("/")
def root():
    return {"message": "SIVA Intake API is running."}
