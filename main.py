"""Pipecat-inspired patient intake voice bot, written from scratch."""
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from cartesia import AsyncCartesia

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

SONIC_MODEL_ID = "sonic-2"
VOICE_ID = "5c43e078-5ba4-4e1f-9639-8d85a403f76a"  # Replace with your preferred voice id

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

@app.websocket("/ws/tts")
async def websocket_tts(websocket: WebSocket):
    print("TTS WebSocket connection received")
    await websocket.accept()
    print("TTS WebSocket accepted")
    client = AsyncCartesia(api_key=os.getenv("CARTESIA_API_KEY"))
    print("Cartesia client created")
    try:
        print("Waiting for text message...")
        data = await websocket.receive_text()
        print(f"Received text: {data[:50]}...")

        print("Creating Cartesia WebSocket...")
        ws = await client.tts.websocket()
        print("Cartesia WebSocket created, sending request...")

        output_generate = await ws.send(
            model_id=SONIC_MODEL_ID,
            transcript=data,
            voice={"id": VOICE_ID},
            output_format={
                "container": "raw",
                "encoding": "pcm_f32le",
                "sample_rate": 44100
            },
            stream=True
        )
        print("TTS request sent, processing audio chunks...")

        chunk_count = 0
        async for out in output_generate:
            if out.audio is not None:
                chunk_count += 1
                print(f"Sending chunk {chunk_count}: {len(out.audio)} bytes")
                await websocket.send_bytes(out.audio)

        print(f"Finished sending {chunk_count} chunks")
        await ws.close()
        print("Cartesia WebSocket closed")
        
        # Close the WebSocket connection gracefully
        await websocket.close()
        print("Frontend WebSocket closed")
        
    except Exception as e:
        print(f"TTS WebSocket error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.close()
        except:
            pass
    finally:
        await client.close()
        print("Cartesia client closed")

@app.websocket("/ws/stt")
async def websocket_stt(websocket: WebSocket):
    print("STT WebSocket connection received")
    await websocket.accept()
    print("STT WebSocket accepted")
    client = AsyncCartesia(api_key=os.getenv("CARTESIA_API_KEY"))
    print("Cartesia STT client created")
    try:
        ws = await client.stt.websocket(model="ink-whisper", language="en")
        print("Cartesia STT WebSocket created")
        
        # Collect all audio data first
        audio_data = b""
        try:
            while True:
                audio_chunk = await websocket.receive_bytes()
                if not audio_chunk:  # End of stream
                    break
                audio_data += audio_chunk
                print(f"Received audio chunk: {len(audio_chunk)} bytes")
        except Exception as e:
            print(f"Finished receiving audio: {e}")
        
        print(f"Total audio received: {len(audio_data)} bytes")
        
        # Send audio to Cartesia
        await ws.send(audio_data)
        print("Audio sent to Cartesia")
        
        # Collect transcript
        transcript = ""
        async for result in ws:
            transcript += result.text
            print(f"Received transcript: {result.text}")
        
        print(f"Final transcript: {transcript}")
        await websocket.send_text(transcript)
        
        await ws.close()
        await websocket.close()
        print("STT WebSocket closed")
        
    except Exception as e:
        print(f"STT WebSocket error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.close()
        except:
            pass
    finally:
        await client.close()
        print("STT client closed")
