"""Pipecat-inspired patient intake voice bot, written from scratch."""
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow CORS for local Gradio frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Simple in-memory session store (for demo purposes)
sessions: Dict[str, Dict[str, Any]] = {}

class UserMessage(BaseModel):
    session_id: str
    message: str

# Minimal function schema for OpenAI function calling
function_schemas = [
    {
        "name": "verify_birthday",
        "description": "Verify the user's birthday.",
        "parameters": {
            "type": "object",
            "properties": {
                "birthday": {"type": "string", "description": "The user's birthday in YYYY-MM-DD format."}
            },
            "required": ["birthday"]
        }
    },
    {
        "name": "list_prescriptions",
        "description": "Collect the user's current prescriptions.",
        "parameters": {
            "type": "object",
            "properties": {
                "prescriptions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "medication": {"type": "string"},
                            "dosage": {"type": "string"}
                        },
                        "required": ["medication", "dosage"]
                    }
                }
            },
            "required": ["prescriptions"]
        }
    },
    {
        "name": "list_allergies",
        "description": "Collect the user's allergies.",
        "parameters": {
            "type": "object",
            "properties": {
                "allergies": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["allergies"]
        }
    },
    {
        "name": "list_conditions",
        "description": "Collect the user's medical conditions.",
        "parameters": {
            "type": "object",
            "properties": {
                "conditions": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["conditions"]
        }
    },
    {
        "name": "list_visit_reasons",
        "description": "Collect the user's reasons for visiting the doctor.",
        "parameters": {
            "type": "object",
            "properties": {
                "visit_reasons": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["visit_reasons"]
        }
    }
]

# IntakeProcessor using OpenAI function calling
class IntakeProcessor:
    def __init__(self, session: Dict[str, Any]):
        self.session = session
        if "messages" not in self.session:
            self.session["messages"] = [
                {"role": "system", "content": (
                    "You are Jessica, an agent for Tsidi Health Services. "
                    "Your job is to collect all important information from the user before their doctor visit. "
                    "You're talking to Patrick Remerscheid. Address the user by their first name, be polite and professional. "
                    "You're not a medical professional, so you shouldn't provide any advice. Keep your responses short. "
                    "Collect all information needed for a doctor: birthday, prescriptions (with dosage), allergies, medical conditions, and reason for visit. "
                    "Ask for clarification if a user response is ambiguous. When you have all the information, confirm and end the intake. "
                    "Use function calls to store each piece of information as you collect it."
                )}
            ]
        if "data" not in self.session:
            self.session["data"] = {}

    def handle_function_call(self, function_call):
        name = function_call["name"]
        arguments = function_call.get("arguments", {})
        # Store the data in session["data"]
        if name == "verify_birthday":
            self.session["data"]["birthday"] = arguments.get("birthday")
        elif name == "list_prescriptions":
            self.session["data"]["prescriptions"] = arguments.get("prescriptions")
        elif name == "list_allergies":
            self.session["data"]["allergies"] = arguments.get("allergies")
        elif name == "list_conditions":
            self.session["data"]["conditions"] = arguments.get("conditions")
        elif name == "list_visit_reasons":
            self.session["data"]["visit_reasons"] = arguments.get("visit_reasons")

    def next_prompt(self, user_message: Optional[str] = None) -> str:
        if user_message:
            self.session["messages"].append({"role": "user", "content": user_message})

        # Call OpenAI with function calling (v1+ API)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=self.session["messages"],
            functions=function_schemas,
            function_call="auto",
            max_tokens=200,
            temperature=0.3,
        )
        message = response.choices[0].message
        self.session["messages"].append(message.model_dump(exclude_unset=True))

        # If the LLM wants to call a function, handle it and re-prompt
        if message.function_call:
            import json
            function_call = message.function_call.model_dump()
            # Parse arguments (OpenAI returns as JSON string)
            arguments = json.loads(function_call["arguments"])
            function_call["arguments"] = arguments
            self.handle_function_call(function_call)
            # Add function response to messages (empty, just to advance)
            self.session["messages"].append({
                "role": "function",
                "name": function_call["name"],
                "content": "OK"
            })
            # Recurse to let LLM continue
            return self.next_prompt(None)
        else:
            return message.content

    def get_history(self) -> List[Dict[str, str]]:
        return self.session.get("messages", [])

    def get_data(self) -> Dict[str, Any]:
        return self.session.get("data", {})

@app.post("/chat")
async def chat(user_message: UserMessage):
    # Get or create session
    session = sessions.setdefault(user_message.session_id, {})
    processor = IntakeProcessor(session)
    reply = processor.next_prompt(user_message.message)
    return {"reply": reply, "history": processor.get_history(), "data": processor.get_data()}

@app.get("/")
def root():
    return {"message": "SIVA Intake API is running."}
