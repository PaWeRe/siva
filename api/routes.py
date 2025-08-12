"""API routes for SIVA application."""

import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, FileResponse

from core.schemas import (
    UserMessage,
    EscalationFeedback,
    ModeRequest,
    PearlExtractionRequest,
    PearlValidationRequest,
    PearlOutcomeRequest,
)
from core.processor import UnifiedProcessor
from core.data_manager import DataManager
from core.vector_store import VectorStore
from core.llm_judge import LLMJudge
from config.settings import settings

# Global components (will be initialized in main.py)
vector_store: VectorStore = None
llm_judge: LLMJudge = None
data_manager: DataManager = None
openai_client = None
sessions: Dict[str, Dict[str, Any]] = {}
current_mode: str = "patient_intake"

# Create router
router = APIRouter()


@router.post("/chat")
async def chat(user_message: UserMessage):
    """Handle chat messages from users."""
    # Get or create session
    session = sessions.setdefault(user_message.session_id, {})
    session["session_id"] = user_message.session_id  # Ensure session_id is stored

    # Add timestamp for tracking
    if "created_at" not in session:
        session["created_at"] = datetime.datetime.now().isoformat()
    session["last_activity"] = datetime.datetime.now().isoformat()

    processor = UnifiedProcessor(
        session,
        vector_store,
        llm_judge,
        openai_client,
        settings.retrieval_threshold,
        current_mode,
    )

    # Get response with potential escalation info
    reply, end_call, escalation_info = processor.next_prompt(user_message.message)

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

        # Automatically add completed conversations to vector store for learning
        try:
            conversation = processor.get_history()
            data = processor.get_data()

            # Only add if we have routing information
            if "routing" in data and data["routing"]:
                routing = data["routing"]
                if isinstance(routing, dict) and "route" in routing:
                    correct_route = routing["route"]

                    # Create symptoms summary
                    symptoms_summary = llm_judge.extract_symptoms_summary(conversation)

                    # Add to vector store
                    vector_store.add_labeled_case(
                        conversation,
                        correct_route,
                        symptoms_summary,
                        user_message.session_id,
                    )
                    print(
                        f"[Chat] Automatically added conversation to vector store: {correct_route}"
                    )
                else:
                    print(f"[Chat] No valid routing found in data: {routing}")
            else:
                print(f"[Chat] No routing data available for vector store addition")
        except Exception as e:
            print(f"[Chat] Error adding conversation to vector store: {e}")

    # Handle different modes
    mode = session.get("mode", "patient_intake")

    if mode == "physician_consultation":
        # In physician consultation mode, don't speak - only provide silent analysis
        response = {
            "reply": "",  # No spoken reply
            "history": processor.get_history(),
            "data": processor.get_data(),
            "end_call": False,  # Don't end call automatically
            "silent_mode": True,  # Flag to indicate silent mode
        }
    else:
        # Normal patient intake mode with spoken responses
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


@router.post("/escalation/feedback")
async def escalation_feedback(feedback: EscalationFeedback):
    """Handle human expert feedback on escalated cases."""
    session = sessions.get(feedback.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    processor = UnifiedProcessor(
        session,
        vector_store,
        llm_judge,
        openai_client,
        settings.retrieval_threshold,
        current_mode,
    )
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
            conversation, feedback.human_label, symptoms_summary, feedback.session_id
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


@router.get("/vector_store/stats")
async def vector_store_stats():
    """Get statistics about the vector store."""
    return vector_store.get_stats()


@router.get("/system/performance")
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


@router.get("/dashboard/metrics")
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


@router.post("/dashboard/demo")
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
            demo_session_id = f"demo_{scenario['name'].replace(' ', '_').lower()}"
            vector_store.add_labeled_case(
                scenario["conversation"],
                scenario["correct_route"],
                symptoms_summary,
                demo_session_id,
            )

    return {"message": f"Demo completed: {len(demo_scenarios)} scenarios processed"}


@router.get("/dashboard/export")
async def export_system_data():
    """Export all system data for analysis."""
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


@router.post("/dashboard/reset")
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


@router.get("/")
def root():
    """Root endpoint."""
    return {"message": "SIVA Unified API is running."}


@router.get("/evidence/{session_id}")
async def get_real_time_evidence(session_id: str):
    """Get real-time evidence for display panel."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    processor = UnifiedProcessor(
        session,
        vector_store,
        llm_judge,
        openai_client,
        settings.retrieval_threshold,
        current_mode,
    )
    evidence = processor.get_real_time_evidence()

    return {
        "session_id": session_id,
        "mode": session.get("mode", "patient_intake"),
        "evidence": evidence,
    }


@router.post("/mode/switch")
async def switch_mode(mode_request: ModeRequest):
    """Switch between patient intake and physician consultation modes."""
    global current_mode
    if mode_request.mode in ["patient_intake", "physician_consultation"]:
        current_mode = mode_request.mode
        return {"mode": current_mode, "status": "switched"}
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid mode. Use 'patient_intake' or 'physician_consultation'",
        )


@router.post("/mode/toggle")
async def toggle_mode(mode_request: ModeRequest):
    """Toggle between patient intake and physician consultation modes."""
    global current_mode
    if current_mode == "patient_intake":
        current_mode = "physician_consultation"
    else:
        current_mode = "patient_intake"

    return {"mode": current_mode, "status": "toggled"}


@router.get("/mode/current")
async def get_current_mode():
    """Get current application mode."""
    return {"mode": current_mode}


@router.get("/dashboard")
async def dashboard():
    """Serve the dashboard HTML page."""
    from pathlib import Path

    dashboard_path = Path(__file__).parent / ".." / "frontend" / "dashboard.html"
    return FileResponse(str(dashboard_path))
