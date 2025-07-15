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
from vector_store import VectorStore
from llm_judge import LLMJudge
from data_manager import DataManager

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

# Configuration for routing system
RETRIEVAL_THRESHOLD = 3  # Need 3+ similar cases to route confidently
SIMILARITY_THRESHOLD = 0.75  # What counts as "similar"

# Initialize vector store, LLM judge, and data manager
vector_store = VectorStore(similarity_threshold=SIMILARITY_THRESHOLD)
llm_judge = LLMJudge()
data_manager = DataManager()

# Simple in-memory session store (for demo purposes)
sessions: Dict[str, Dict[str, Any]] = {}

SONIC_MODEL_ID = "sonic-2"
VOICE_ID = (
    "5c43e078-5ba4-4e1f-9639-8d85a403f76a"  # Replace with your preferred voice id
)


class UserMessage(BaseModel):
    session_id: str
    message: str


class EscalationFeedback(BaseModel):
    session_id: str
    agent_prediction: str
    human_label: str


# Minimal function schema for OpenAI function calling
function_schemas = [
    {
        "name": "verify_fullname",
        "description": "Collect the user's full name.",
        "parameters": {
            "type": "object",
            "properties": {
                "names": {
                    "type": "array",
                    "items": {
                        "properties": {
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                        },
                        "required": ["first_name", "last_name"],
                    },
                }
            },
            "required": ["names"],
        },
    },
    {
        "name": "verify_birthday",
        "description": "Verify the user's birthday.",
        "parameters": {
            "type": "object",
            "properties": {
                "birthday": {
                    "type": "string",
                    "description": "The user's birthday in YYYY-MM-DD format.",
                }
            },
            "required": ["birthday"],
        },
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
                            "dosage": {"type": "string"},
                        },
                        "required": ["medication", "dosage"],
                    },
                }
            },
            "required": ["prescriptions"],
        },
    },
    {
        "name": "list_allergies",
        "description": "Collect the user's allergies.",
        "parameters": {
            "type": "object",
            "properties": {"allergies": {"type": "array", "items": {"type": "string"}}},
            "required": ["allergies"],
        },
    },
    {
        "name": "list_conditions",
        "description": "Collect the user's medical conditions.",
        "parameters": {
            "type": "object",
            "properties": {
                "conditions": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["conditions"],
        },
    },
    {
        "name": "list_visit_reasons",
        "description": "Collect the user's reasons for visiting the doctor.",
        "parameters": {
            "type": "object",
            "properties": {
                "visit_reasons": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["visit_reasons"],
        },
    },
    {
        "name": "collect_detailed_symptoms",
        "description": "Collect detailed information about patient symptoms.",
        "parameters": {
            "type": "object",
            "properties": {
                "symptoms": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "symptom": {
                                "type": "string",
                                "description": "The symptom (e.g., chest pain, headache)",
                            },
                            "severity": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                                "description": "Pain/severity scale 1-10",
                            },
                            "duration": {
                                "type": "string",
                                "description": "How long (e.g., 2 hours, 3 days)",
                            },
                            "associated_symptoms": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Related symptoms",
                            },
                            "triggers": {
                                "type": "string",
                                "description": "What makes it better or worse",
                            },
                        },
                        "required": ["symptom", "severity", "duration"],
                    },
                },
            },
            "required": ["symptoms"],
        },
    },
    {
        "name": "determine_routing",
        "description": "Determine appropriate care routing based on patient information and similar cases.",
        "parameters": {
            "type": "object",
            "properties": {
                "route": {
                    "type": "string",
                    "enum": [
                        "emergency",
                        "urgent",
                        "routine",
                        "self_care",
                        "information",
                    ],
                    "description": "The recommended care route",
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief explanation for the routing decision",
                },
            },
            "required": ["route", "reasoning"],
        },
    },
]


# Enhanced IntakeProcessor with routing and escalation capabilities
class IntakeProcessor:
    def __init__(self, session: Dict[str, Any]):
        self.session = session
        self.vector_store = vector_store
        self.llm_judge = llm_judge

        # Initialize session with phase tracking
        if "phase" not in self.session:
            self.session["phase"] = (
                "basic_intake"  # basic_intake -> detailed_symptoms -> routing
            )

        if "messages" not in self.session:
            self.session["messages"] = [
                {"role": "system", "content": self._get_system_prompt()}
            ]
        if "data" not in self.session:
            self.session["data"] = {}
        if "escalation_data" not in self.session:
            self.session["escalation_data"] = {}

    def _get_system_prompt(self) -> str:
        """Get system prompt based on current phase."""
        phase = self.session.get("phase", "basic_intake")

        if phase == "basic_intake":
            return (
                "You are John, an agent for Tsidi Health Services. "
                "Your job is to collect basic information from the user before their doctor visit. "
                "Address the user by their first name, be polite and professional. "
                "You're not a medical professional, so you shouldn't provide any advice. Keep your responses short. "
                "IMPORTANT: Start by greeting the user warmly and introducing yourself. "
                "Collect basic information: full name, birthday, prescriptions, allergies, medical conditions, and reason for visit. "
                "Ask for clarification if a user response is ambiguous. "
                "NEVER assume or hallucinate information. Only store what the user actually provides. "
                "Use function calls to store each piece of information as you collect it. "
                "Once ALL basic information is collected, tell the user you need to ask some detailed questions about their symptoms."
            )
        elif phase == "detailed_symptoms":
            return (
                "You are John, continuing the intake process. "
                "Now collect DETAILED information about the patient's symptoms. "
                "For each symptom, ask about: severity (1-10 scale), duration, associated symptoms, and triggers. "
                "Be thorough but efficient. Use the collect_detailed_symptoms function to store this information. "
                "After collecting detailed symptoms, proceed to determine the appropriate care route."
            )
        elif phase == "routing":
            similar_cases = self.vector_store.retrieve_similar(self.session["messages"])
            examples = self.vector_store.get_few_shot_examples(similar_cases)

            if examples:
                return f"""You are John, making a routing decision based on patient information.
                
Here are similar cases for reference:
{examples}

Based on the patient's symptoms and these examples, determine the appropriate care route:
- emergency: Life-threatening (severe chest pain, stroke signs, difficulty breathing)
- urgent: Serious but not life-threatening (high fever, severe pain)  
- routine: Ongoing or non-urgent (mild symptoms, follow-ups)
- self_care: Minor issues (cold, mild headache)
- information: Questions about medication or prevention

Use the determine_routing function to make your decision."""
            else:
                return (
                    "You are John, making a routing decision. "
                    "Based on the patient's symptoms, determine appropriate care route. "
                    "Use the determine_routing function, but note this will likely be escalated "
                    "since we have limited similar cases for reference."
                )

    def handle_function_call(self, function_call):
        """Handle function calls and store data."""
        name = function_call["name"]
        arguments = function_call.get("arguments", {})

        # Store basic intake data
        if name == "verify_fullname":
            self.session["data"]["full_name"] = arguments.get("names")
        elif name == "verify_birthday":
            self.session["data"]["birthday"] = arguments.get("birthday")
        elif name == "list_prescriptions":
            self.session["data"]["prescriptions"] = arguments.get("prescriptions")
        elif name == "list_allergies":
            self.session["data"]["allergies"] = arguments.get("allergies")
        elif name == "list_conditions":
            self.session["data"]["conditions"] = arguments.get("conditions")
        elif name == "list_visit_reasons":
            self.session["data"]["visit_reasons"] = arguments.get("visit_reasons")

        # Store detailed symptoms
        elif name == "collect_detailed_symptoms":
            self.session["data"]["detailed_symptoms"] = arguments.get("symptoms")

        # Store routing decision
        elif name == "determine_routing":
            self.session["data"]["routing"] = {
                "route": arguments.get("route"),
                "reasoning": arguments.get("reasoning"),
            }

    def all_basic_info_collected(self) -> bool:
        """Check if all basic intake info is collected."""
        data = self.session.get("data", {})
        required = [
            "full_name",
            "birthday",
            "prescriptions",
            "allergies",
            "conditions",
            "visit_reasons",
        ]

        for key in required:
            if key not in data:
                return False
            value = data[key]
            if isinstance(value, list):
                continue  # Accept empty lists
            elif isinstance(value, str):
                if not value.strip():
                    return False
            elif value is None:
                return False
        return True

    def has_detailed_symptoms(self) -> bool:
        """Check if detailed symptoms are collected."""
        return "detailed_symptoms" in self.session.get("data", {})

    def has_routing_decision(self) -> bool:
        """Check if routing decision is made."""
        return "routing" in self.session.get("data", {})

    def should_escalate(self) -> bool:
        """Determine if case should be escalated based on retrieval threshold."""
        similar_count = self.vector_store.count_similar_cases(self.session["messages"])
        print(
            f"[IntakeProcessor] Found {similar_count} similar cases, threshold: {RETRIEVAL_THRESHOLD}"
        )
        return similar_count < RETRIEVAL_THRESHOLD

    def next_prompt(
        self, user_message: Optional[str] = None
    ) -> tuple[str, bool, Optional[Dict]]:
        """
        Process next step in conversation.
        Returns: (reply, end_call, escalation_info)
        """
        print(f"=== IntakeProcessor.next_prompt ===")
        print(f"Phase: {self.session.get('phase')}")
        print(f"User message: '{user_message}'")
        print(f"Current data: {self.session.get('data', {})}")

        if user_message:
            self.session["messages"].append({"role": "user", "content": user_message})

        # Call OpenAI with function calling
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=self.session["messages"],
            functions=function_schemas,
            function_call="auto",
            max_tokens=300,
            temperature=0.3,
        )

        message = response.choices[0].message
        print(f"LLM response: {message.content}")
        print(f"Function call: {message.function_call}")

        self.session["messages"].append(message.model_dump(exclude_unset=True))

        # Handle function calls
        if message.function_call:
            import json

            function_call = message.function_call.model_dump()
            arguments = json.loads(function_call["arguments"])
            function_call["arguments"] = arguments
            self.handle_function_call(function_call)

            # Add function response
            self.session["messages"].append(
                {"role": "function", "name": function_call["name"], "content": "OK"}
            )

            # Check for phase transitions
            if (
                self.session["phase"] == "basic_intake"
                and self.all_basic_info_collected()
            ):
                self.session["phase"] = "detailed_symptoms"
                self.session["messages"].append(
                    {"role": "system", "content": self._get_system_prompt()}
                )
            elif (
                self.session["phase"] == "detailed_symptoms"
                and self.has_detailed_symptoms()
            ):
                self.session["phase"] = "routing"
                self.session["messages"].append(
                    {"role": "system", "content": self._get_system_prompt()}
                )
            elif self.session["phase"] == "routing" and self.has_routing_decision():
                # Check if we should escalate
                if self.should_escalate():
                    return self._prepare_escalation()
                else:
                    return self._finalize_routing()

            # Continue conversation
            return self.next_prompt(None)

        # No function call - regular response
        return message.content, False, None

    def _prepare_escalation(self) -> tuple[str, bool, Dict]:
        """Prepare escalation data for human review."""
        routing_data = self.session["data"].get("routing", {})
        escalation_info = {
            "session_id": self.session.get("session_id"),
            "agent_prediction": routing_data.get("route", "unknown"),
            "reasoning": routing_data.get("reasoning", "No reasoning provided"),
            "patient_data": self.session["data"],
            "conversation": self.session["messages"],
        }

        self.session["escalation_data"] = escalation_info

        escalation_message = (
            f"I've analyzed your symptoms and believe this may require {routing_data.get('route', 'unknown')} care. "
            f"However, I'd like to have a human expert review this case to ensure you get the best care. "
            f"Let me connect you with one of our specialists."
        )

        return escalation_message, True, escalation_info

    def _finalize_routing(self) -> tuple[str, bool, None]:
        """Finalize routing decision when confident."""
        routing_data = self.session["data"].get("routing", {})
        route = routing_data.get("route", "unknown")
        reasoning = routing_data.get("reasoning", "")

        final_message = f"Based on your symptoms, I recommend {route} care. {reasoning} I'll connect you with the appropriate department now."

        return final_message, True, None

    def get_history(self) -> List[Dict[str, str]]:
        return self.session.get("messages", [])

    def get_data(self) -> Dict[str, Any]:
        return self.session.get("data", {})

    def get_escalation_data(self) -> Dict[str, Any]:
        return self.session.get("escalation_data", {})


@app.post("/chat")
async def chat(user_message: UserMessage):
    # Get or create session
    session = sessions.setdefault(user_message.session_id, {})
    session["session_id"] = user_message.session_id  # Ensure session_id is stored

    # Add timestamp for tracking
    import datetime

    if "created_at" not in session:
        session["created_at"] = datetime.datetime.now().isoformat()
    session["last_activity"] = datetime.datetime.now().isoformat()

    processor = IntakeProcessor(session)

    # Get response with potential escalation info
    reply, end_call, escalation_info = processor.next_prompt(user_message.message)

    # Note: All data persistence is now handled by DataManager
    # No need for separate intake_logs directory

    # Mark session as completed
    if end_call:
        session["completed"] = True
        session["completed_at"] = datetime.datetime.now().isoformat()

        # Save completed conversation to persistent storage
        conversation_data = {
            "messages": processor.get_history(),
            "data": processor.get_data(),
            "escalation_data": processor.get_escalation_data(),
        }
        data_manager.save_conversation(user_message.session_id, conversation_data)

    response = {
        "reply": reply,
        "history": processor.get_history(),
        "data": processor.get_data(),
        "end_call": end_call,
    }

    # Add escalation info if present
    if escalation_info:
        response["escalation"] = escalation_info

    return response


@app.post("/escalation/feedback")
async def escalation_feedback(feedback: EscalationFeedback):
    """Handle human expert feedback on escalated cases."""
    session = sessions.get(feedback.session_id)
    if not session:
        return {"error": "Session not found"}

    processor = IntakeProcessor(session)
    conversation = processor.get_history()

    # Create training example using LLM Judge
    training_example = llm_judge.create_training_example(
        conversation, feedback.agent_prediction, feedback.human_label
    )

    # Evaluate the prediction
    evaluation = llm_judge.evaluate_prediction_accuracy(
        feedback.agent_prediction, feedback.human_label, conversation
    )

    # Add to vector store if this should be used for training
    if llm_judge.should_add_to_training(evaluation):
        symptoms_summary = training_example["symptoms_summary"]
        vector_store.add_labeled_case(
            conversation, feedback.human_label, symptoms_summary
        )

    # Store evaluation for performance tracking
    if "evaluations" not in session:
        session["evaluations"] = []
    session["evaluations"].append(evaluation)

    # Save evaluation to persistent storage
    data_manager.save_evaluation(feedback.session_id, evaluation)

    return {
        "message": "Feedback received and processed",
        "evaluation": evaluation,
        "training_added": llm_judge.should_add_to_training(evaluation),
    }


@app.get("/vector_store/stats")
async def vector_store_stats():
    """Get statistics about the vector store."""
    return vector_store.get_stats()


@app.get("/system/performance")
async def system_performance():
    """Get overall system performance metrics."""
    all_evaluations = []
    for session in sessions.values():
        all_evaluations.extend(session.get("evaluations", []))

    performance = llm_judge.analyze_system_performance(all_evaluations)
    suggestions = llm_judge.generate_improvement_suggestions(performance)

    return {
        "performance": performance,
        "improvement_suggestions": suggestions,
        "vector_store_stats": vector_store.get_stats(),
    }


@app.get("/dashboard/metrics")
async def dashboard_metrics():
    """Get comprehensive metrics for the dashboard."""
    # Use DataManager for persistent metrics
    escalation_metrics = data_manager.get_escalation_metrics()
    data_stats = data_manager.get_data_statistics()
    learning_curve = data_manager.compute_learning_curve()

    # Get current session data
    all_evaluations = []
    for session in sessions.values():
        all_evaluations.extend(session.get("evaluations", []))

    # Get vector store conversations with metadata
    vector_conversations = []
    for conv in vector_store.conversations:
        vector_conversations.append(
            {
                "id": conv.get("id"),
                "symptoms_summary": conv.get("symptoms_summary", ""),
                "correct_route": conv.get("correct_route", "unknown"),
                "timestamp": conv.get("timestamp", ""),
            }
        )

    # Combine persistent data with current session data
    total_persistent_evaluations = len(data_manager.get_all_evaluations())
    total_current_evaluations = len(all_evaluations)

    return {
        "total_conversations": data_stats["total_conversations"]
        + len([s for s in sessions.values() if s.get("completed", False)]),
        "total_escalations": escalation_metrics["total_escalations"]
        + total_current_evaluations,
        "escalation_rate": escalation_metrics["escalation_rate"],
        "necessary_escalations": escalation_metrics["necessary_escalations"],
        "unnecessary_escalations": escalation_metrics["unnecessary_escalations"],
        "escalation_precision": escalation_metrics["escalation_precision"],
        "vector_conversations": vector_conversations,
        "recent_activity": data_stats["recent_activity"],
        "learning_curve": learning_curve,
        "data_size_mb": data_stats["data_size_mb"],
        "persistent_data": {
            "evaluations": total_persistent_evaluations,
            "conversations": data_stats["total_conversations"],
        },
    }


@app.post("/dashboard/demo")
async def run_demo_scenarios():
    """Run predefined demo scenarios to show learning progression."""
    demo_scenarios = [
        {
            "name": "Emergency - Chest Pain",
            "conversation": [
                {
                    "role": "user",
                    "content": "I'm having severe chest pain that started 30 minutes ago",
                },
                {
                    "role": "user",
                    "content": "The pain is 9/10, crushing, radiating to my left arm with shortness of breath",
                },
            ],
            "agent_prediction": "emergency",
            "correct_route": "emergency",
        },
        {
            "name": "Routine - Annual Checkup",
            "conversation": [
                {"role": "user", "content": "I'm here for my yearly physical exam"},
                {
                    "role": "user",
                    "content": "No specific symptoms, just routine preventive care",
                },
            ],
            "agent_prediction": "routine",
            "correct_route": "routine",
        },
        {
            "name": "Urgent - High Fever",
            "conversation": [
                {
                    "role": "user",
                    "content": "I've had a fever of 103°F for 2 days with severe headache",
                },
                {
                    "role": "user",
                    "content": "The fever is 8/10 severity, started suddenly, with chills and body aches",
                },
            ],
            "agent_prediction": "urgent",
            "correct_route": "urgent",
        },
        {
            "name": "Emergency - Stroke Symptoms",
            "conversation": [
                {
                    "role": "user",
                    "content": "I suddenly can't speak clearly and my face feels droopy",
                },
                {
                    "role": "user",
                    "content": "Started 10 minutes ago, sudden onset, left side weakness, 10/10 concern",
                },
            ],
            "agent_prediction": "urgent",  # Agent initially gets this wrong
            "correct_route": "emergency",  # Human corrects it
        },
        {
            "name": "Self Care - Mild Cold",
            "conversation": [
                {
                    "role": "user",
                    "content": "I have a runny nose and mild cough for 2 days",
                },
                {
                    "role": "user",
                    "content": "Symptoms are 2/10 severity, typical cold symptoms, no fever",
                },
            ],
            "agent_prediction": "self_care",
            "correct_route": "self_care",
        },
    ]

    for scenario in demo_scenarios:
        # Create demo session
        session_id = f"demo_{scenario['name'].replace(' ', '_').lower()}"
        session = {"session_id": session_id, "timestamp": "", "evaluations": []}

        # Simulate escalation and feedback
        evaluation = {
            "agent_prediction": scenario["agent_prediction"],
            "human_label": scenario["correct_route"],
            "prediction_correct": scenario["agent_prediction"]
            == scenario["correct_route"],
            "timestamp": "",
        }
        session["evaluations"].append(evaluation)
        sessions[session_id] = session

        # Add to vector store if judgment says to
        if llm_judge.should_add_to_training(evaluation):
            symptoms_summary = " | ".join(
                [msg["content"] for msg in scenario["conversation"]]
            )
            vector_store.add_labeled_case(
                scenario["conversation"], scenario["correct_route"], symptoms_summary
            )

    return {"message": f"Demo completed: {len(demo_scenarios)} scenarios processed"}


@app.get("/dashboard/export")
async def export_system_data():
    """Export all system data for analysis."""
    from fastapi.responses import JSONResponse

    # Use DataManager for comprehensive export
    export_data = data_manager.export_all_data()

    # Add current session data
    export_data["current_sessions"] = dict(sessions)
    export_data["vector_store"] = {
        "conversations": vector_store.conversations,
        "stats": vector_store.get_stats(),
    }

    return JSONResponse(
        content=export_data,
        headers={"Content-Disposition": "attachment; filename=siva_export.json"},
    )


@app.post("/dashboard/reset")
async def reset_system():
    """Reset all system data (for demo purposes)."""
    global sessions
    sessions.clear()

    # Reset vector store
    vector_store.conversations.clear()
    vector_store.save_data()

    # Reset persistent data
    data_manager.reset_all_data()

    return {"message": "System reset successfully"}


@app.get("/")
def root():
    return {"message": "SIVA Intake API is running."}


@app.get("/dashboard")
async def dashboard():
    """Serve the dashboard HTML page."""
    from fastapi.responses import FileResponse

    return FileResponse("dashboard.html")


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
                "sample_rate": 44100,
            },
            stream=True,
        )
        print("TTS request sent, processing audio chunks...")

        chunk_count = 0
        async for out in output_generate:
            if out.audio is not None:
                chunk_count += 1
                # print(f"Sending chunk {chunk_count}: {len(out.audio)} bytes")
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

    try:
        print("[STT] Waiting for single audio chunk from client")
        # Receive a single audio message from the client
        audio_data = await websocket.receive_bytes()
        print(f"[STT] Received audio chunk: {len(audio_data)} bytes")

        print(f"[STT] Total audio received: {len(audio_data)} bytes")

        if len(audio_data) == 0:
            print("[STT] No audio data received")
            try:
                await websocket.send_text("")
                print("[STT] Sent empty response to client")
            except Exception:
                print("[STT] Could not send empty response (WebSocket closed)")
            return

        # Save audio to temporary file for OpenAI Whisper
        import tempfile
        import os

        # Create temporary file with .wav extension
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_filename = temp_file.name
        print(f"[STT] Audio written to temp file: {temp_filename}")

        try:
            # Use OpenAI Whisper for transcription
            print("[STT] Sending audio to OpenAI Whisper...")
            with open(temp_filename, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file, language="en"
                )

            result_text = transcript.text.strip()
            print(f"[STT] Whisper transcript: '{result_text}'")

            # Send transcript back to client
            try:
                await websocket.send_text(result_text)
                print(f"[STT] Transcript sent to client: '{result_text}'")

                # Close the WebSocket gracefully after sending response
                await websocket.close()
                print("[STT] WebSocket closed gracefully after sending transcript")

            except Exception as send_error:
                print(
                    f"[STT] Could not send transcript (WebSocket may be closed): {send_error}"
                )

        except Exception as e:
            print(f"[STT] OpenAI Whisper error: {e}")
            try:
                await websocket.send_text("")
                print("[STT] Sent empty response to client after Whisper error")
            except Exception:
                print("[STT] Could not send empty response (WebSocket may be closed)")

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_filename)
                print(f"[STT] Temporary audio file cleaned up: {temp_filename}")
            except Exception:
                print(f"[STT] Could not clean up temp file: {temp_filename}")

        print("[STT] STT processing complete")

    except Exception as e:
        print(f"STT WebSocket error: {e}")
        import traceback

        traceback.print_exc()
        try:
            await websocket.send_text("")
            await websocket.close()
        except Exception:
            pass
